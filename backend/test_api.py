import sys
import os
from dotenv import load_dotenv

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from app.core.config import get_settings
from app.services.rewrite import generate_with_gemini

settings = get_settings()
print("AI Provider:", settings.ai_provider)
print("Gemini Model:", settings.gemini_model)
print("Max Output Tokens:", settings.max_output_tokens)
print("API Key present:", bool(settings.gemini_api_key))

prompt = "Hello, write a short poem about coding."
try:
    res = generate_with_gemini(prompt)
    print("Response status: Success")
    print("Response length:", len(res) if res else 0)
    print("Response start:", res[:100] if res else "None")
except Exception as e:
    print("ERROR running Gemini:", e)
