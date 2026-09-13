"""
Diagnostic test script for ResolveAI LLM, Hugging Face configuration, and tool-calling integration.
Verifies:
1. Environment configuration
2. Hugging Face authentication
3. Model invocation
4. Tool binding
5. Tool calling
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import (
    HUGGINGFACEHUB_API_TOKEN,
    HUGGINGFACE_MODEL,
    HUGGINGFACE_PROVIDER,
    is_valid_hf_token,
    get_masked_hf_token,
)
from app.models.llm import create_llm_endpoint, create_chat_model
from app.agent.agent import ALL_TOOLS, model_with_tools


def run_diagnostics():
    print("=" * 60)
    print("ResolveAI LLM & Tool-Calling Diagnostic Suite")
    print("=" * 60)

    # -------------------------------------------------------------
    # 1. Environment Configuration Check
    # -------------------------------------------------------------
    try:
        env_file_exists = Path(".env").exists()
        print(f"[OK] Environment configuration")
        print(f"     - .env present: {env_file_exists}")
        print(f"     - Target Model: {HUGGINGFACE_MODEL}")
        print(f"     - Provider: {HUGGINGFACE_PROVIDER or 'Hugging Face Auto-Router (Default)'}")
    except Exception as e:
        print(f"[FAIL] Environment configuration: {str(e)}")
        return False

    # -------------------------------------------------------------
    # 2. Hugging Face Authentication Check
    # -------------------------------------------------------------
    token_valid = is_valid_hf_token()
    masked_tok = get_masked_hf_token()
    if token_valid:
        print(f"[OK] Hugging Face authentication")
        print(f"     - Token status: Configured ({masked_tok})")
    else:
        print(f"[FAIL] Hugging Face authentication")
        print(f"     - Token status: {masked_tok}")
        print("     - Note: Set a valid HUGGINGFACEHUB_API_TOKEN (starting with 'hf_') in .env for live API calls.")

    # -------------------------------------------------------------
    # 3. Model Invocation Check
    # -------------------------------------------------------------
    if token_valid:
        try:
            test_model = create_chat_model()
            resp = test_model.invoke("Respond with exactly: Hello ResolveAI")
            print(f"[OK] Model invocation")
            print(f"     - Response: {resp.content[:60]}...")
        except Exception as e:
            raw_err = str(e)
            if "auto-router" in raw_err.lower():
                print(f"[FAIL] Model invocation: Auto-router rejected token format. Ensure token starts with 'hf_'.")
            elif "401" in raw_err or "unauthorized" in raw_err.lower():
                print(f"[FAIL] Model invocation: Invalid or expired Hugging Face token.")
            elif "402" in raw_err or "credits" in raw_err.lower() or "429" in raw_err:
                print(f"[WARN] Model invocation: Rate limited or quota exceeded (402/429).")
            else:
                print(f"[FAIL] Model invocation: {raw_err}")
    else:
        print(f"[SKIP] Model invocation (requires valid Hugging Face token in .env)")

    # -------------------------------------------------------------
    # 4. Tool Binding Check
    # -------------------------------------------------------------
    try:
        bound_model = create_chat_model().bind_tools(ALL_TOOLS)
        tool_names = [t.name for t in ALL_TOOLS]
        print(f"[OK] Tool binding")
        print(f"     - Registered Tools ({len(ALL_TOOLS)}): {', '.join(tool_names)}")
    except Exception as e:
        print(f"[FAIL] Tool binding: {str(e)}")
        return False

    # -------------------------------------------------------------
    # 5. Tool Calling Schema Verification
    # -------------------------------------------------------------
    try:
        from langchain_core.utils.function_calling import convert_to_openai_tool
        formatted_tools = [convert_to_openai_tool(t) for t in ALL_TOOLS]
        assert len(formatted_tools) == len(ALL_TOOLS)
        for ft in formatted_tools:
            assert "type" in ft and ft["type"] == "function"
            assert "name" in ft["function"]
            assert "description" in ft["function"]
        print(f"[OK] Tool calling")
        print(f"     - All {len(formatted_tools)} tool schemas successfully validated for LangGraph execution.")
    except Exception as e:
        print(f"[FAIL] Tool calling: {str(e)}")
        return False

    print("=" * 60)
    print("Diagnostic Complete.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    run_diagnostics()
