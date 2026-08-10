import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
from app.core.config import get_settings
from openai import OpenAI

load_dotenv()

def main():
    settings = get_settings()
    client = OpenAI(
        api_key=settings.openai_api_key or settings.openrouter_api_key,
        base_url=settings.openai_base_url
    )
    
    try:
        response = client.embeddings.create(
            input="Software engineer backend java python",
            model="text-embedding-3-small"
        )
        print("Embedding generated successfully!")
        print(len(response.data[0].embedding))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
