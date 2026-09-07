from typing import Annotated, Optional, Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List[Any], add_messages]
    channel: str                # "telegram" | "web"
    user_id: str
    patient_id: Optional[str]   # resolved once by the router node
    thread_id: str               # session_id
    stage: str                   # "qa" | "booking" | "post_booking_intake"
    booking_draft: Dict[str, Any]
    intake_draft: Dict[str, Any]
    intake_turns: int            # escape-hatch counter
