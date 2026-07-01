from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import json

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

class InvoiceRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str


@app.post("/extract", response_model=InvoiceResponse)
def extract(request: InvoiceRequest):

    if not request.text.strip():
        return InvoiceResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )

    prompt = f"""
Extract invoice information.

Return ONLY valid JSON.

{{
  "vendor":"",
  "amount":0,
  "currency":"",
  "date":"YYYY-MM-DD"
}}

Invoice:

{request.text}
"""

    response = client.chat.completions.create(
        model="llama3.2",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
    except:
        data = {
            "vendor":"",
            "amount":0,
            "currency":"",
            "date":""
        }

    return InvoiceResponse(**data)