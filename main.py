from fastapi import FastAPI, Request
from pydantic import BaseModel
from openai import OpenAI
import json, re

app = FastAPI()

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

def extract_json(text: str):
    try:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return None
        return json.loads(m.group())
    except:
        return None

def fallback_extract(text: str):
    vendor = ""
    m = re.search(r'(Acme-[A-Za-z0-9]+(?:\s+[A-Za-z0-9&.,-]+){0,5})', text)
    if m:
        vendor = m.group(1).strip()

    if not vendor:
        m = re.search(r'([A-Z][A-Za-z0-9&.,-]+(?:\s+[A-Z][A-Za-z0-9&.,-]+){1,6})', text)
        vendor = m.group(1).strip() if m else "Unknown Vendor"

    amt = re.search(r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)\b', text)
    amount = float(amt.group(1).replace(",", "")) if amt else 0.0

    cur = re.search(r'\b(USD|EUR|GBP)\b', text.upper())
    currency = cur.group(1) if cur else "USD"

    dt = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', text)
    date = dt.group(1) if dt else "1970-01-01"

    return {"vendor": vendor, "amount": amount, "currency": currency, "date": date}

@app.post("/extract", response_model=InvoiceResponse)
async def extract(request: Request):
    try:
        body = await request.json()
    except:
        return fallback_extract("")

    text = body.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return fallback_extract("")

    try:
        prompt = f"""
Return only valid JSON with keys vendor, amount, currency, date.
Invoice text:
{text}
"""
        response = client.chat.completions.create(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        raw = response.choices[0].message.content
        data = extract_json(raw) or fallback_extract(text)
    except:
        data = fallback_extract(text)

    return InvoiceResponse(
        vendor=str(data.get("vendor", "Unknown Vendor")),
        amount=float(data.get("amount", 0)),
        currency=str(data.get("currency", "USD")).upper(),
        date=str(data.get("date", "1970-01-01"))
    )