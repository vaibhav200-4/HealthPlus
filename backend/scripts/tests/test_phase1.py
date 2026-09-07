import sys
import uuid
import asyncio
from pathlib import Path
from langchain_core.messages import HumanMessage

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.supabase_client import SupabaseService
from app.config import settings
from app.agent.graph import get_agent_graph
from app.services.patient_service import PatientService

async def test_phase1():
    print("--- Phase 1 Acceptance Test ---")
    
    # Use existing profile_id if available to respect foreign key constraint
    profs = SupabaseService.get_records("profiles")
    if profs:
        test_user_id = profs[0]["id"]
    else:
        test_user_id = settings.ADMIN_USER_ID or str(uuid.uuid4())

    # 1. Verify PatientService resolution deduplication
    p1 = PatientService.resolve_patient(test_user_id)
    p2 = PatientService.resolve_patient(test_user_id)
    assert p1["id"] == p2["id"], "PatientService failed to deduplicate patient creation!"
    print(f"PatientService deduplication verified: patient_id={p1['id']}")

    # 2. Verify LangGraph Agent graph invocation & memory checkpointer reducer
    graph = await get_agent_graph()
    thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_input = {
        "messages": [HumanMessage(content="Where is the hospital?")],
        "user_id": test_user_id,
        "channel": "web",
        "thread_id": thread_id,
        "stage": "qa"
    }

    print("Invoking agent graph (turn 1)...")
    res1 = await graph.ainvoke(initial_input, config=config)
    messages1 = res1.get("messages", [])
    print(f"Turn 1 produced {len(messages1)} message(s). Last message: {messages1[-1].content[:100]}...")

    # Second invocation with same thread_id
    second_input = {
        "messages": [HumanMessage(content="What specialties do you have?")],
        "user_id": test_user_id,
        "channel": "web",
        "thread_id": thread_id,
        "stage": "qa"
    }

    print("Invoking agent graph (turn 2 with same thread_id)...")
    res2 = await graph.ainvoke(second_input, config=config)
    messages2 = res2.get("messages", [])
    print(f"Turn 2 total history contains {len(messages2)} message(s).")
    
    assert len(messages2) > len(messages1), "Reducer failed: message history was replaced instead of appended!"
    print("Phase 1 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    asyncio.run(test_phase1())
