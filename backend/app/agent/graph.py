import json
import logging
from datetime import datetime
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.tools import (
    search_doctors,
    get_hospital_info,
    check_availability,
    book_appointment,
    save_intake_note
)
from app.services.patient_service import PatientService

logger = logging.getLogger("hospital_app.agent.graph")

MAX_HISTORY_MESSAGES = 20  # trim before every LLM call so long threads don't dilute the current turn
CLASSIFIER_FAILURE_COUNT = 0


def _normalize_message_content(m: Any, index: Optional[int] = None) -> Any:
    """Safely normalizes message content to ensure non-empty valid string for LLM endpoints."""
    content = getattr(m, "content", None)
    original_content = content

    if content is None or str(content).strip() in ("", "None", "null"):
        content = "[]"
    elif isinstance(content, (dict, list)):
        try:
            content = json.dumps(content)
        except Exception:
            content = str(content)
    elif not isinstance(content, str):
        content = str(content)

    if hasattr(m, "content"):
        if content != original_content and index is not None:
            logger.warning(f"[AGENT] NORMALIZING EMPTY/INVALID MESSAGE at index={index}")
        m.content = content
    return m


def _fallback_classify_stage(latest_msg_text: str) -> str:
    """Small deterministic fallback classifier when LLM structured output fails or returns None."""
    logger.info("[ROUTER FALLBACK] classifier unavailable")
    text_lower = (latest_msg_text or "").lower().strip()
    booking_keywords = ["book", "booking", "appointment", "schedule", "slot", "see dr", "see doctor"]
    
    if any(kw in text_lower for kw in booking_keywords):
        logger.info("[ROUTER FALLBACK] detected stage=booking")
        return "booking"
    
    logger.info("[ROUTER FALLBACK] detected stage=qa")
    return "qa"


class StageDecision(BaseModel):
    stage: Literal["qa", "booking"] = Field(
        description=(
            "Which mode best serves the patient's LATEST message, given the recent conversation. "
            "'booking' only if they clearly want to search doctors, check availability, or book/reschedule "
            "an appointment right now. Everything else — general questions, small talk, follow-ups, "
            "questions unrelated to booking even if a booking is already in progress — is 'qa'."
        )
    )


async def router_node(state: AgentState) -> Dict[str, Any]:
    """Router node: resolves patient_id once, then classifies stage EVERY turn (except
    mid-intake) so the agent can be interrupted by an off-topic question instead of
    getting stuck in booking/qa forever. This replaces the old one-way keyword gate,
    which only ever fired from the "qa" stage and had no way back once it left it."""
    global CLASSIFIER_FAILURE_COUNT
    user_id = state.get("user_id", "")
    patient_id = state.get("patient_id")

    if not patient_id and user_id:
        p_rec = PatientService.resolve_patient(user_id)
        patient_id = p_rec.get("id")

    prev_stage = state.get("stage") or "qa"
    messages = state.get("messages", [])

    if prev_stage == "post_booking_intake":
        # Never reclassify mid-intake — that flow has its own turn-count escape
        # hatch (post_booking_intake_node) and re-routing here would let a stray
        # "doctor"/"schedule" mention bounce the patient out before it's done.
        new_stage = "post_booking_intake"
    elif not messages:
        new_stage = "qa"
    else:
        last_msg_content = getattr(messages[-1], "content", "") if messages else ""
        if isinstance(last_msg_content, str) and last_msg_content.startswith("[Uploaded document:"):
            new_stage = prev_stage
        else:
            try:
                llm = get_llm()
                classifier = llm.with_structured_output(StageDecision, method="function_calling")
                recent = messages[-6:]
                decision = await classifier.ainvoke(
                    [SystemMessage(content=(
                        "Classify what the patient's latest message needs. Default to 'qa' unless "
                        "booking intent is unambiguous."
                    ))] + recent
                )
                if decision is None:
                    CLASSIFIER_FAILURE_COUNT += 1
                    logger.error(f"Stage classifier returned None (unparsable output) [total failures: {CLASSIFIER_FAILURE_COUNT}]")
                    new_stage = _fallback_classify_stage(str(last_msg_content))
                else:
                    new_stage = decision.stage
            except Exception:
                CLASSIFIER_FAILURE_COUNT += 1
                logger.error(f"Stage classifier failed [total failures: {CLASSIFIER_FAILURE_COUNT}]; running fallback classifier", exc_info=True)
                new_stage = _fallback_classify_stage(str(last_msg_content))

    return {
        "patient_id": patient_id,
        "stage": new_stage,
        "booking_draft": state.get("booking_draft") or {},
        "intake_draft": state.get("intake_draft") or {},
        "intake_turns": state.get("intake_turns", 0)
    }


def route_stage(state: AgentState) -> str:
    stage = state.get("stage", "qa")
    if stage == "booking":
        return "booking"
    elif stage == "post_booking_intake":
        return "post_booking_intake"
    return "hospital_qa"


async def _execute_react_step(llm_with_tools, tools, state: AgentState, system_prompt: str, config: RunnableConfig) -> Dict[str, Any]:
    """Executes a single ReAct LLM step with tool execution loop, via ToolNode so
    that InjectedState (user_id/thread_id/patient_id) actually resolves from graph
    state instead of failing or being asked of the user. `config` is threaded through
    from the parent node invocation — ToolNode needs it (thread_id/checkpoint
    namespace) to run at all."""
    tool_node = ToolNode(tools)
    raw_history = state.get("messages", [])[-MAX_HISTORY_MESSAGES:]
    history = []
    for idx, m in enumerate(raw_history):
        _normalize_message_content(m, index=idx)
        history.append(m)

    messages = [SystemMessage(content=system_prompt)] + history

    for idx, m in enumerate(messages):
        _normalize_message_content(m, index=idx)

    logger.info(f"[AGENT] Sending {len(messages)} messages to LLM")
    response = await llm_with_tools.ainvoke(messages, config)

    tool_messages = []
    current_response = response
    iteration = 0
    # Booking's chain (search -> check_availability -> book_appointment) can
    # legitimately need a few sequential tool round-trips before a plain-text
    # reply — keep headroom above the minimum needed so multi-step queries
    # (e.g. QA + booking mixed in one turn) don't get cut off mid-chain.
    max_iterations = 6

    while current_response.tool_calls and iteration < max_iterations:
        iteration += 1
        tool_messages.append(current_response)

        for tc in current_response.tool_calls:
            logger.info(f"[AGENT] LLM requested tool={tc.get('name')}")

        tool_node_input = {**state, "messages": [current_response]}
        tool_node_result = await tool_node.ainvoke(tool_node_input, config)

        for m in tool_node_result["messages"]:
            _normalize_message_content(m)
            tool_name = getattr(m, "name", getattr(m, "tool_call_id", "unknown"))
            c_type = type(getattr(m, "content", None)).__name__
            c_repr = str(getattr(m, "content", ""))[:200]
            logger.info(f"[AGENT] Tool result name={tool_name} content_type={c_type}")
            logger.info(f"[AGENT] Tool result content={c_repr}")

        tool_messages.extend(tool_node_result["messages"])

        step_messages = messages + tool_messages
        for idx, m in enumerate(step_messages):
            _normalize_message_content(m, index=idx)

        logger.info(f"[AGENT] Sending {len(step_messages)} messages to LLM")
        current_response = await llm_with_tools.ainvoke(step_messages, config)

    if current_response.tool_calls:
        # Loop was exhausted with tool_calls still pending — returning this as-is
        # gives the user a message with no visible text (looked like the agent
        # silently failing on complex, multi-step queries). Force one clean,
        # tool-free final answer instead.
        tool_messages.append(current_response)
        fallback_llm = llm_with_tools.bind_tools([])
        final_msgs = messages + tool_messages + [SystemMessage(content=(
            "You have gathered enough information from the tool calls above. "
            "Give the patient a clear, direct answer now — do not call any more tools."
        ))]
        for idx, m in enumerate(final_msgs):
            _normalize_message_content(m, index=idx)

        logger.info(f"[AGENT] Sending {len(final_msgs)} messages to LLM")
        current_response = await fallback_llm.ainvoke(final_msgs, config)

    new_msgs = tool_messages + [current_response] if tool_messages else [current_response]
    return {"messages": new_msgs}


async def hospital_qa_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Q&A Node: Answers general questions about hospital, departments, and doctors."""
    llm = get_llm()
    tools = [search_doctors, get_hospital_info]
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = (
        "You are the HealthPulse AI Assistant. Answer patient questions about hospital facilities, "
        "departments, doctors, and specialties. Use `search_doctors` to look up specific doctors or "
        "departments, and `get_hospital_info` for facility-level questions (location, hours, contact, "
        "departments available) — never ask the user for a doctor ID or database ID directly.\n"
        "If a tool call returns no relevant data for the question, say so plainly and offer to connect "
        "the patient with the front desk — never invent hospital details, doctor credentials, fees, or "
        "availability that a tool did not actually return.\n"
        "Be professional, polite, and concise."
    )
    return await _execute_react_step(llm_with_tools, tools, state, system_prompt, config)


async def booking_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Booking Node: Manages doctor slot lookup and appointment booking. Payment is
    not currently collected — book_appointment fires directly once a valid slot is
    confirmed."""
    llm = get_llm()
    tools = [search_doctors, check_availability, book_appointment]
    llm_with_tools = llm.bind_tools(tools)

    now_str = datetime.now().isoformat()
    system_prompt = (
        f"Current system date and time: {now_str}.\n"
        "You are the HealthPulse Booking Assistant. Help the user search for doctors, check slot "
        "availability, and book appointments.\n"
        "Always resolve doctor identity via `search_doctors` first — including when the user names a "
        "specific doctor (pass it as doctor_name) — never ask the user for a doctor ID or user ID "
        "directly, the patient's identity is already known from their session.\n"
        "Once the user confirms a doctor, date, and time that check_availability shows as available, "
        "call book_appointment right away — do not ask for payment or any confirmation beyond the "
        "slot itself.\n"
        "If check_availability shows no slot matching the patient's requested time, tell them plainly "
        "and offer the closest available slots that day, or ask for a different date.\n"
        "Only report slots, fees, or confirmations that a tool actually returned — never guess or "
        "invent availability.\n"
        "Once an appointment is successfully created, inform the patient."
    )
    res = await _execute_react_step(llm_with_tools, tools, state, system_prompt, config)

    # Stage only advances when book_appointment actually reports success — merely
    # requesting the tool isn't enough (e.g. slot taken, doctor not found, DB
    # integrity error all return success=False and must NOT push the patient into
    # post-booking intake).
    new_stage = state.get("stage", "booking")
    booking_success = False

    for msg in res.get("messages", []):
        if getattr(msg, "name", None) == "book_appointment":
            content = getattr(msg, "content", "")
            if isinstance(content, str):
                try:
                    result = json.loads(content)
                    booking_success = result.get("success") is True
                except Exception:
                    pass

    if booking_success:
        new_stage = "post_booking_intake"
        res["intake_turns"] = 0

    res["stage"] = new_stage
    return res


async def post_booking_intake_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Post-Booking Intake Node: Collects symptom notes with guaranteed exit after 4 turns or enough info."""
    llm = get_llm()
    tools = [save_intake_note]
    llm_with_tools = llm.bind_tools(tools)

    turns = state.get("intake_turns", 0) + 1

    system_prompt = (
        "You are the HealthPulse Medical Intake Assistant. The patient has just booked an appointment.\n"
        "Ask about their current symptoms, medical history, and any past test reports to prepare notes for the doctor.\n"
        "Only record what the patient actually tells you — never fill in symptoms or history they did not mention.\n"
        "Call `save_intake_note` when notes are collected."
    )
    res = await _execute_react_step(llm_with_tools, tools, state, system_prompt, config)

    note_saved = False
    for msg in res.get("messages", []):
        if hasattr(msg, "tool_calls"):
            for tc in getattr(msg, "tool_calls", []):
                if tc.get("name") == "save_intake_note":
                    note_saved = True

    if note_saved or turns >= 4:
        # This must be the stage VALUE "qa" (what router_node checks), not the node
        # name "hospital_qa" — setting it to the node name silently disabled
        # booking-intent detection for any conversation after the first booking.
        res["stage"] = "qa"
    else:
        res["stage"] = "post_booking_intake"
        res["intake_turns"] = turns

    return res


def create_agent_graph():
    """Builds and compiles the StateGraph for the HealthPulse agent."""
    builder = StateGraph(AgentState)

    builder.add_node("router", router_node)
    builder.add_node("hospital_qa", hospital_qa_node)
    builder.add_node("booking", booking_node)
    builder.add_node("post_booking_intake", post_booking_intake_node)

    builder.add_edge(START, "router")
    builder.add_conditional_edges(
        "router",
        route_stage,
        {
            "hospital_qa": "hospital_qa",
            "booking": "booking",
            "post_booking_intake": "post_booking_intake"
        }
    )

    builder.add_edge("hospital_qa", END)
    builder.add_edge("booking", END)
    builder.add_edge("post_booking_intake", END)

    return builder


_compiled_agent = None


async def get_agent_graph():
    global _compiled_agent
    if _compiled_agent is not None:
        return _compiled_agent

    from app.agent.memory import get_checkpointer
    checkpointer = await get_checkpointer()
    builder = create_agent_graph()
    _compiled_agent = builder.compile(checkpointer=checkpointer)
    return _compiled_agent