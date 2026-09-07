import os
from typing import Optional
from app.config import settings

def get_llm(provider: Optional[str] = None):
    """Returns a LangChain chat model bound the same way regardless of provider.
    provider defaults to settings.LLM_PROVIDER. Callable with .bind_tools(tools).
    Nothing outside this file ever imports a provider-specific class.
    """
    target_provider = (provider or settings.LLM_PROVIDER or "gemini").lower()
    
    # Smart fallback if selected provider key is missing but alternative exists
    groq_key   = getattr(settings, "GROQ_API_KEY", "") or os.getenv("GROQ_API_KEY", "")
    nvidia_key = getattr(settings, "NVIDIA_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
    google_key = getattr(settings, "GOOGLE_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    
    if not provider and target_provider == "nvidia" and not nvidia_key and google_key:
        target_provider = "gemini"

    if target_provider == "nvidia":
        from langchain_nvidia_ai_endpoints import ChatNVIDIA
        model_name = os.getenv("NVIDIA_MODEL", "openai/gpt-oss-20b")
        kwargs = {"model": model_name}
        if nvidia_key:
            kwargs["nvidia_api_key"] = nvidia_key
        else:
            kwargs["nvidia_api_key"] = "nvapi-placeholder-key"
        return ChatNVIDIA(**kwargs)
    elif target_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        kwargs = {"model": model_name}
        if google_key:
            kwargs["google_api_key"] = google_key
        else:
            kwargs["google_api_key"] = "AIzaSy-placeholder-key"
        return ChatGoogleGenerativeAI(**kwargs)
    else:
        raise ValueError(f"Unsupported LLM provider: '{target_provider}'. Must be 'nvidia' or 'gemini'.")
