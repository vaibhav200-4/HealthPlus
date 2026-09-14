from pipecat.frames.frames import Frame

class UserTurnFrame(Frame):
    """
    Frame emitted when a full user speech turn is aggregated.
    """
    def __init__(self, text: str = "", user_id: str = ""):
        super().__init__()
        self.text = text
        self.user_id = user_id

    def __str__(self):
        return f"UserTurnFrame(text={self.text!r})"
