import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv("backend/.env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
)

try:
    completion = client.chat.completions.create(
        model="deepseek/deepseek-v4-flash:free",
        messages=[
            {"role": "user", "content": "hello"}
        ],
        temperature=0.25,
        max_tokens=100,
    )
    print("Completion type:", type(completion))
    print("Raw Completion:", completion)
    print("Choices:", completion.choices)
except Exception as e:
    print("Error:", e)
