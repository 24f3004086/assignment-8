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
        Extract the invoice information.

        Return ONLY valid JSON.

        Example:

        {{
        "vendor":"Acme Industries Ltd.",
        "amount":1450.25,
        "currency":"USD",
        "date":"2026-08-19"
        }}

        Rules:
        - amount must be ONLY a number (no currency symbol or text)
        - currency must be the 3-letter code
        - date must be YYYY-MM-DD
        - Do not include markdown or explanations.

        Invoice:
        {data.text}
        """

    response = client.chat.completions.create(
    model="llama3.2",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ],
    response_format={"type": "json_object"}
)

    result = response.choices[0].message.content

    try:
        result = result.strip()
        if result.startswith("```"):
            result = result.replace("```json", "")
            result = result.replace("```", "")
            result = result.strip()
        parsed = json.loads(result)
    except Exception as e:
        print("JSON ERROR:", e)
        print("LLM returned:", result)
        return {
            "vendor": "",
            "amount": 0.0,
            "currency": "",
            "date": ""
    }

    return parsed