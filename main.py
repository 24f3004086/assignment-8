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
def extract(data: InvoiceRequest):

    if not data.text.strip():
        return {
            "vendor":"",
            "amount":0,
            "currency":"",
            "date":""
        }

    prompt = f"""
Extract invoice information.

Return ONLY JSON.

Fields:
vendor
amount
currency
date

Currency must be uppercase 3-letter code.

Date must be YYYY-MM-DD.

Invoice:

{data.text}
"""

    response = client.chat.completions.create(
        model="llama3.2",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    result = response.choices[0].message.content

    try:
        parsed = json.loads(result)
    except:
        parsed = {
            "vendor":"",
            "amount":0,
            "currency":"",
            "date":""
        }

    return parsed