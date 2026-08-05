import os
from dotenv import load_dotenv
load_dotenv("backend/.env")
from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
for m in client.models.list().data:
    if "llama" in m.id.lower():
        print(m.id)
