import os
from typing import Optional
from app.config import settings


def get_llm(provider: Optional[str] = None):
    """
    Returns a LangChain chat model.

    Default fallback priority:
        Groq -> NVIDIA -> Gemini

    If `provider` is explicitly supplied, that provider is used
    (provided its API key is available).
    """

    groq_key = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    nvidia_key = getattr(settings, "NVIDIA_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
    google_key = getattr(settings, "GOOGLE_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")

    # ---------------------------------------------------------
    # Explicit provider selection
    # ---------------------------------------------------------
    if provider:
        target_provider = provider.lower()

        if target_provider == "groq":
            if not groq_key:
                raise ValueError("GROQ_API_KEY is missing.")
            return _get_groq(groq_key)

        elif target_provider == "nvidia":
            if not nvidia_key:
                raise ValueError("NVIDIA_API_KEY is missing.")
            return _get_nvidia(nvidia_key)

        elif target_provider == "gemini":
            if not google_key:
                raise ValueError("GOOGLE_API_KEY is missing.")
            return _get_gemini(google_key)

        else:
            raise ValueError(
                f"Unsupported LLM provider: '{provider}'. "
                "Must be 'groq', 'nvidia', or 'gemini'."
            )

    # ---------------------------------------------------------
    # Automatic fallback:
    # Groq -> NVIDIA -> Gemini
    # ---------------------------------------------------------
    if groq_key:
        return _get_groq(groq_key)

    if nvidia_key:
        return _get_nvidia(nvidia_key)

    if google_key:
        return _get_gemini(google_key)

    raise ValueError(
        "No LLM API key found. "
        "Set GROQ_API_KEY, NVIDIA_API_KEY, or GOOGLE_API_KEY."
    )


# =============================================================
# Groq
# =============================================================

def _get_groq(api_key: str):
    from langchain_groq import ChatGroq

    model_name = os.getenv(
        "GROQ_MODEL",
        "openai/gpt-oss-20b"
    )

    return ChatGroq(
        model=model_name,
        groq_api_key=api_key,
    )


# =============================================================
# NVIDIA
# =============================================================

def _get_nvidia(api_key: str):
    from langchain_nvidia_ai_endpoints import ChatNVIDIA

    model_name = os.getenv(
        "NVIDIA_NIM_MODEL",
        "openai/gpt-oss-20b"
    )

    return ChatNVIDIA(
        model=model_name,
        nvidia_api_key=api_key,
    )


# =============================================================
# Gemini
# =============================================================

def _get_gemini(api_key: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    model_name = os.getenv(
        "GEMINI_MODEL",
        "gemini-3.6-flash"
    )

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
    )