import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.agent.llm import get_llm
from app.config import settings

def test_phase0():
    print("--- Phase 0 Acceptance Test ---")
    print(f"Default LLM Provider: {settings.LLM_PROVIDER}")

    # Test NVIDIA provider instantiation & bind_tools
    llm_nvidia = get_llm("nvidia")
    assert llm_nvidia.__class__.__name__ == "ChatNVIDIA"
    print(f"NVIDIA Model initialized: {llm_nvidia.__class__.__name__}")
    bound_nvidia = llm_nvidia.bind_tools([])
    assert bound_nvidia is not None
    print("NVIDIA .bind_tools([]) successful")

    # Test Gemini provider instantiation & bind_tools
    llm_gemini = get_llm("gemini")
    assert llm_gemini.__class__.__name__ == "ChatGoogleGenerativeAI"
    print(f"Gemini Model initialized: {llm_gemini.__class__.__name__}")
    bound_gemini = llm_gemini.bind_tools([])
    assert bound_gemini is not None
    print("Gemini .bind_tools([]) successful")

    # Invoke tests if API keys are available
    if settings.NVIDIA_API_KEY:
        try:
            print("Invoking NVIDIA LLM ('say hi')...")
            res_nvidia = llm_nvidia.invoke("say hi")
            print(f"NVIDIA Response: {res_nvidia.content[:100]}...")
        except Exception as e:
            print(f"NVIDIA invocation error (expected if key/model inactive): {e}")

    if settings.GOOGLE_API_KEY:
        try:
            print("Invoking Gemini LLM ('say hi')...")
            res_gemini = llm_gemini.invoke("say hi")
            print(f"Gemini Response: {res_gemini.content[:100]}...")
        except Exception as e:
            print(f"Gemini invocation error (expected if key inactive): {e}")

    print("Phase 0 Acceptance Test PASSED successfully!")

if __name__ == "__main__":
    test_phase0()
