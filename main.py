from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import json
import re

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
def extract_json(text: str):
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            return None
        return json.loads(text[start:end+1])
    except:
        return None

    prompt = f"""
        You are an invoice extraction engine.

        You MUST return ONLY valid JSON. No text. No markdown. No explanation.

        Return format:
        {{
        "vendor": string,
        "amount": number,
        "currency": string,
        "date": string
        }}

        Rules:
        - vendor must be exact substring from invoice
        - amount must be numeric only
        - currency must be 3-letter uppercase (USD, EUR, GBP)
        - date must be YYYY-MM-DD

        Invoice:
        {req.text}
        """
    try:
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        text = response.choices[0].message.content

        # Remove markdown if model returns ```json
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

        data = json.loads(text)
        print("RAW MODEL OUTPUT:")
        print(text)
        return InvoiceResponse(
            vendor=data.get("vendor", ""),
            amount=float(data.get("amount", 0)),
            currency=data.get("currency", "").upper(),
            date=data.get("date", "")
        )

    except Exception:
        # Never return HTTP 500
        return InvoiceResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )