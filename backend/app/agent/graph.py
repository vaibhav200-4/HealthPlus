import logging
from datetime import datetime
from typing import Dict, Any
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.agent.llm import get_llm
from app.agent.tools import (
    search_doctors,
    check_availability,
    generate_mock_payment,
    book_appointment,
    save_intake_note
)
from app.services.patient_service import PatientService

logger = logging.getLogger("hospital_app.agent.graph")

async def router_node(state: AgentState) -> Dict[str, Any]:
    """Router node: resolves patient_id once and determines conversational stage."""
    user_id = state.get("user_id", "")
    patient_id = state.get("patient_id")

    if not patient_id and user_id:
        p_rec = PatientService.resolve_patient(user_id)
        patient_id = p_rec.get("id")

    current_stage = state.get("stage") or "qa"
    last_msg = ""
    messages = state.get("messages", [])
    if messages:
        last_msg = str(messages[-1].content).lower()

    # Dynamic stage intent detection — only fires from the "qa" stage value.
    # post_booking_intake_node must set stage back to "qa" (not the node name
    # "hospital_qa") on completion, or this check silently stops firing after
    # the first booking.
    if current_stage == "qa" and any(k in last_msg for k in ["book", "appointment", "schedule", "slot", "doctor"]):
        current_stage = "booking"

    return {
        "patient_id": patient_id,
        "stage": current_stage,
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
    namespace) to run at all; calling it without one is what raised
    "Missing required config key" previously."""
    tool_node = ToolNode(tools)
    messages = [SystemMessage(content=system_prompt)] + state.get("messages", [])

    response = await llm_with_tools.ainvoke(messages, config)

    tool_messages = []
    current_response = response
    iteration = 0
    # Booking's full chain (search -> check_availability -> generate_mock_payment ->
    # book_appointment) can legitimately need 4 sequential tool round-trips before a
    # plain-text reply — 3 was too low and could cut the chain off mid-booking.
    max_iterations = 6

    while current_response.tool_calls and iteration < max_iterations:
        iteration += 1
        tool_messages.append(current_response)

        # ToolNode resolves Annotated[AgentState, InjectedState] params from whatever
        # state dict it's given here — pass the full current state, with `messages`
        # narrowed to just the AI message carrying the pending tool_calls.
        tool_node_input = {**state, "messages": [current_response]}
        tool_node_result = await tool_node.ainvoke(tool_node_input, config)
        tool_messages.extend(tool_node_result["messages"])

        step_messages = messages + tool_messages
        current_response = await llm_with_tools.ainvoke(step_messages, config)

    new_msgs = tool_messages + [current_response] if tool_messages else [current_response]
    return {"messages": new_msgs}

async def hospital_qa_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Q&A Node: Answers general questions about hospital, departments, and doctors."""
    llm = get_llm()
    tools = [search_doctors]
    llm_with_tools = llm.bind_tools(tools)

    system_prompt = (
        "You are the HealthPulse AI Assistant. Answer patient questions about hospital facilities, "
        "departments, doctors, and specialties. Use the `search_doctors` tool when looking up specific "
        "doctors or departments — never ask the user for a doctor ID or database ID directly. "
        "Be professional, polite, and concise."
    )
    return await _execute_react_step(llm_with_tools, tools, state, system_prompt, config)

async def booking_node(state: AgentState, config: RunnableConfig) -> Dict[str, Any]:
    """Booking Node: Manages doctor slot lookup, payment QR generation, and appointment booking."""
    llm = get_llm()
    tools = [search_doctors, check_availability, generate_mock_payment, book_appointment]
    llm_with_tools = llm.bind_tools(tools)

    now_str = datetime.now().isoformat()
    system_prompt = (
        f"Current system date and time: {now_str}.\n"
        "You are the HealthPulse Booking Assistant. Help the user search for doctors, check slot availability, "
        "generate payment QR codes, and book appointments.\n"
        "Always resolve doctor identity via `search_doctors` first — including when the user names a "
        "specific doctor (pass it as doctor_name) — never ask the user for a doctor ID or user ID "
        "directly, the patient's identity is already known from their session. "
        "Once an appointment is successfully created, inform the patient."
    )
    res = await _execute_react_step(llm_with_tools, tools, state, system_prompt, config)

    new_stage = state.get("stage", "booking")
    for msg in res.get("messages", []):
        if hasattr(msg, "tool_calls"):
            for tc in getattr(msg, "tool_calls", []):
                if tc.get("name") == "book_appointment":
                    new_stage = "post_booking_intake"

    res["stage"] = new_stage
    if new_stage == "post_booking_intake":
        res["intake_turns"] = 0
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