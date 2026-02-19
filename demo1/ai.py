from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "You are Edith, a voice assistant. "
    "Reply briefly in 2 or 3 short sentences only."
)

def chat_with_ai(user_text):
    res = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        max_tokens=120,
        temperature=0.6
    )
    return res.choices[0].message.content.strip()
