# ai_voice_agent/processor/manager.py
import re

# ---------------------------------------------------------------------------
# Minimum word-token overlap ratio that marks a transcript as an echo of the
# bot's last utterance. 0.55 means 55 % of the user words appeared in the
# bot reply — almost certainly not a genuine user message.
# ---------------------------------------------------------------------------
_ECHO_OVERLAP_THRESHOLD = 0.55


def _token_overlap_ratio(text_a: str, text_b: str) -> float:
    """Return the fraction of words in `text_a` that also appear in `text_b`."""
    if not text_a or not text_b:
        return 0.0
    tokens_a = set(re.sub(r"[^a-z0-9 ]", "", text_a.lower()).split())
    tokens_b = set(re.sub(r"[^a-z0-9 ]", "", text_b.lower()).split())
    if not tokens_a:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a)


class TurnManager:
    """
    Simplified TurnManager storing last bot reply for browser echo cancellation.
    """

    def __init__(self, conversation_id=None, user_id=None, timeout: float = 0.18):
        self.timeout = timeout
        self._last_bot_text: str = ""

    def register_bot_reply(self, text: str) -> None:
        """Call this with the full text the bot is about to speak."""
        self._last_bot_text = text