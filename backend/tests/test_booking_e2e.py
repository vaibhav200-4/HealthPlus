import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from app.agent.graph import get_agent_graph, _fallback_classify_stage, _normalize_message_content
from app.agent.tools import search_doctors, check_availability
from app.database.supabase_client import SupabaseService


async def test_router_fallback():
    print("\n--- TEST 1: Router Fallback ---", flush=True)
    booking_msg = "I want to book an appointment with Dr. Riya Kapoor"
    qa_msg = "What departments do you have?"

    stage_booking = _fallback_classify_stage(booking_msg)
    stage_qa = _fallback_classify_stage(qa_msg)

    assert stage_booking == "booking", f"Expected 'booking', got '{stage_booking}'"
    assert stage_qa == "qa", f"Expected 'qa', got '{stage_qa}'"
    print("TEST 1 PASS: Router fallback correctly classified booking vs qa", flush=True)
    return True


async def test_tool_message_safety():
    print("\n--- TEST 2: Tool Message Safety ---")
    null_msg = ToolMessage(content=None, tool_call_id="call_123")
    dict_msg = ToolMessage(content={"status": "empty"}, tool_call_id="call_456")

    _normalize_message_content(null_msg, index=0)
    _normalize_message_content(dict_msg, index=1)

    assert null_msg.content == "[]", f"Expected '[]', got {repr(null_msg.content)}"
    assert isinstance(dict_msg.content, str), f"Expected string, got {type(dict_msg.content)}"
    assert "empty" in dict_msg.content
    print("TEST 2 PASS: Tool message content correctly normalized")
    return True


async def test_real_doctor_search():
    print("\n--- TEST 3: Real Doctor Search ---")
    results = await search_doctors.ainvoke({"doctor_name": "Riya Kapoor"})
    if not results:
        results = await search_doctors.ainvoke({})

    assert len(results) > 0, "No doctors found in real database!"
    doctor = results[0]
    assert "id" in doctor and doctor["id"], "Doctor missing ID"
    assert "name" in doctor and doctor["name"], "Doctor missing name"
    print(f"TEST 3 PASS: Found real doctor: {doctor['name']} (ID: {doctor['id']})")
    return doctor


async def test_real_availability(doctor_id: str):
    print("\n--- TEST 4: Real Availability ---")
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    slots = await check_availability.ainvoke({"doctor_id": doctor_id, "date": tomorrow})

    available_slots = [s for s in slots if s.get("available")]
    assert len(available_slots) > 0, f"No available slots for doctor {doctor_id} on {tomorrow}"
    slot = available_slots[0]
    print(f"TEST 4 PASS: Found available slot on {tomorrow}: {slot['start_time']} - {slot['end_time']}")
    return tomorrow, slot


async def test_full_e2e_booking(doctor: dict, date_str: str, slot: dict):
    print("\n--- TEST 5: Full E2E Booking ---")
    user_id = os.getenv("ADMIN_USER_ID", "00000000-0000-0000-0000-000000000001")
    thread_id = f"test_e2e_{uuid.uuid4().hex[:8]}"

    agent_graph = await get_agent_graph()
    config = {"configurable": {"thread_id": thread_id}}

    user_prompt = f"I want to book an appointment with {doctor['name']} on {date_str} at {slot['start_time']}."
    agent_input = {
        "messages": [HumanMessage(content=user_prompt)],
        "user_id": user_id,
        "channel": "web",
        "thread_id": thread_id
    }

    res = await agent_graph.ainvoke(agent_input, config=config)
    messages = res.get("messages", [])

    executed_tools = []
    for msg in messages:
        if hasattr(msg, "tool_calls"):
            for tc in getattr(msg, "tool_calls", []):
                executed_tools.append((tc.get("name"), tc.get("args")))
        elif getattr(msg, "name", None):
            executed_tools.append((getattr(msg, "name"), getattr(msg, "content", "")))

    print("\n--- EXECUTED TOOL TRACE ---", flush=True)
    for item in executed_tools:
        print(item, flush=True)

    apps = SupabaseService.get_records("appointments", {"user_id": user_id, "doctor_id": doctor["id"], "date": date_str})

    created_app = None
    for app in apps:
        if app.get("start_time") == slot["start_time"]:
            created_app = app
            break

    assert created_app is not None, f"Mandatory DB Assertion Failed: No appointment row created for doctor {doctor['id']} on {date_str} at {slot['start_time']}"
    assert created_app["user_id"] == user_id
    assert created_app["doctor_id"] == doctor["id"]
    assert created_app["date"] == date_str
    assert created_app["start_time"] == slot["start_time"]

    print(f"TEST 5 PASS: Database insertion verified! Appointment ID: {created_app['id']}")
    return created_app


async def test_unavailable_slot(doctor: dict, date_str: str, slot: dict):
    print("\n--- TEST 6: Unavailable Slot ---")
    thread_id = f"test_e2e_conflict_{uuid.uuid4().hex[:8]}"
    user_id = os.getenv("ADMIN_USER_ID", "00000000-0000-0000-0000-000000000001")

    agent_graph = await get_agent_graph()
    config = {"configurable": {"thread_id": thread_id}}

    user_prompt = f"I want to book an appointment with {doctor['name']} on {date_str} at {slot['start_time']}."
    agent_input = {
        "messages": [HumanMessage(content=user_prompt)],
        "user_id": user_id,
        "channel": "web",
        "thread_id": thread_id
    }

    res = await agent_graph.ainvoke(agent_input, config=config)

    apps = SupabaseService.get_records("appointments", {"user_id": user_id, "doctor_id": doctor["id"], "date": date_str})
    matching_apps = [app for app in apps if app.get("start_time") == slot["start_time"]]

    assert len(matching_apps) == 1, f"Expected exactly 1 appointment for booked slot, got {len(matching_apps)}"
    print("TEST 6 PASS: Conflict slot correctly blocked. No duplicate appointment created.")
    return True


async def cleanup_test_appointment(app_id: str):
    print("\n--- CLEANUP ---")
    if app_id:
        try:
            SupabaseService.delete_record("appointments", app_id)
            print(f"CLEANUP PASS: Deleted test appointment {app_id}")
        except Exception as e:
            print(f"CLEANUP NOTICE: {e}")


async def main():
    print("==================================================")
    print("RUNNING END-TO-END LANGGRAPH BOOKING TEST SUITE")
    print("==================================================")

    created_app_id = None
    try:
        await test_router_fallback()
        await test_tool_message_safety()
        doctor = await test_real_doctor_search()
        date_str, slot = await test_real_availability(doctor["id"])
        created_app = await test_full_e2e_booking(doctor, date_str, slot)
        created_app_id = created_app.get("id")
        await test_unavailable_slot(doctor, date_str, slot)
        print("\n==================================================")
        print("ALL E2E BOOKING TESTS PASSED SUCCESSFULLY!")
        print("==================================================")
    finally:
        if created_app_id:
            await cleanup_test_appointment(created_app_id)


if __name__ == "__main__":
    asyncio.run(main())
