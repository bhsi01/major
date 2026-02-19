from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "You are Edith, a voice assistant. "
    "Reply briefly in 1 or 2 short sentences only."
)

def chat_with_ai(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are Edith. Be very very concise."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.6
    )
    return response.choices[0].message.content.strip()
