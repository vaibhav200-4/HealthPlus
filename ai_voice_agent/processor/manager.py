import asyncio
import re
import time
from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    InterimTranscriptionFrame,
    BotStartedSpeakingFrame,
    BotStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection
from processor.frames import UserTurnFrame

_CONTINUATION_START = re.compile(r"^(today|tomorrow|with|for|and|at|on|in|to|pm|am|\d)", re.I)
_CONTINUATION_END = re.compile(r"(?:\b(on|with|for|and|at|to|in|today|tomorrow)\s*)$", re.I)

# ---------------------------------------------------------------------------
# Echo suppression: duration (seconds) to ignore STT after bot stops speaking.
# Covers the audio ring-buffer latency where TTS audio leaks into the mic feed.
# 1.2 s is generous but safe; real human responses take longer than this.
# ---------------------------------------------------------------------------
_POST_SPEECH_SUPPRESSION_SECS = 1.2

# Minimum word-token overlap ratio that marks a transcript as an echo of the
# bot's last utterance.  0.55 means 55 % of the user words appeared in the
# bot reply — almost certainly not a genuine user message.
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


class TurnManager(FrameProcessor):
    """
    Turn manager with dual-layer echo suppression.

    Layer 1 – Hard block while bot is speaking:
        Any STT transcription that arrives while `bot_speaking` is True is
        silently dropped.  This is the primary defence.

    Layer 2 – Post-speech suppression window:
        After the bot finishes speaking, audio ring-buffer latency means the
        STT can still deliver echoes for up to ~1 s.  We keep a timestamp of
        when the bot stopped and discard transcriptions that arrive within
        `_POST_SPEECH_SUPPRESSION_SECS` AND look like the bot's last reply
        (token-overlap filter).  Transcriptions that arrive in that window but
        do NOT look like the bot's words are kept — they are genuine
        user interruptions.
    """

    def __init__(self, conversation_id=None, user_id=None, timeout: float = 0.18):
        super().__init__()
        self.timeout = timeout
        self.current_text = ""
        self.timer = None
        self.bot_speaking = False
        self._bot_stopped_at: float = 0.0          # monotonic timestamp
        self._last_bot_text: str = ""               # last TTS sentence spoken

    # ── public API used by GroqProcessor to register the bot reply ───────────
    def register_bot_reply(self, text: str) -> None:
        """Call this with the full text the bot is about to speak."""
        self._last_bot_text = text

    # ── frame processing ─────────────────────────────────────────────────────
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, BotStartedSpeakingFrame):
            self.bot_speaking = True
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, BotStoppedSpeakingFrame):
            self.bot_speaking = False
            self._bot_stopped_at = time.monotonic()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, InterimTranscriptionFrame):
            # Suppress interim frames while bot is speaking to avoid confusion
            if self.bot_speaking:
                return
            await self.push_frame(frame, direction)
            return

        if not isinstance(frame, TranscriptionFrame):
            await self.push_frame(frame, direction)
            return

        text = (frame.text or "").strip()
        if not text:
            return

        # Drop pure-noise blips (punctuation only)
        if not any(c.isalnum() for c in text):
            return

        # ── Layer 1: Hard block while bot is speaking ─────────────────────
        if self.bot_speaking:
            print(f"[ECHO L1] Dropped (bot speaking): {text!r}")
            return

        # ── Layer 2: Post-speech suppression window ───────────────────────
        elapsed = time.monotonic() - self._bot_stopped_at
        if elapsed < _POST_SPEECH_SUPPRESSION_SECS and self._last_bot_text:
            overlap = _token_overlap_ratio(text, self._last_bot_text)
            if overlap >= _ECHO_OVERLAP_THRESHOLD:
                print(
                    f"[ECHO L2] Dropped echo (overlap={overlap:.2f}, "
                    f"+{elapsed:.2f}s after bot): {text!r}"
                )
                return
            # overlap is low → genuine user utterance (interruption/new question)
            print(f"[ECHO L2] Kept user speech (overlap={overlap:.2f}): {text!r}")

        self.current_text = self._merge(self.current_text, text)
        self._restart_timer()

    # ── timer helpers ─────────────────────────────────────────────────────────
    def _restart_timer(self):
        if self.timer and not self.timer.done():
            self.timer.cancel()
        self.timer = asyncio.create_task(self._flush())

    async def _flush(self):
        try:
            await asyncio.sleep(self.timeout)
        except asyncio.CancelledError:
            return
        text = self.current_text.strip()
        self.current_text = ""
        if text:
            await self._emit(text)

    async def _emit(self, text):
        print(f"\nUSER TURN: {text}")
        await self.push_frame(UserTurnFrame(text=text), FrameDirection.DOWNSTREAM)

    # ── text merging ──────────────────────────────────────────────────────────
    @staticmethod
    def _merge(old, new):
        if not old:
            return new
        if not new:
            return old
        a, b = old.lower(), new.lower()
        if b == a or b.startswith(a):
            return new if len(new) >= len(old) else old
        if a.startswith(b) or a.endswith(b):
            return old
        if _CONTINUATION_END.search(old) or _CONTINUATION_START.match(new):
            return f"{old} {new}"
        return new