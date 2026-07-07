from fastapi import FastAPI
from pydantic import BaseModel
import ollama
import json

app = FastAPI()

class InvoiceRequest(BaseModel):
    text: str

class InvoiceResponse(BaseModel):
    vendor: str
    amount: float
    currency: str
    date: str

PROMPT = """
Extract the invoice fields.

Return ONLY a JSON object.

Do not use markdown.
Do not use ```json.
Do not explain.
Do not write anything before or after the JSON.

Example:

{
  "vendor":"Acme Industries Ltd.",
  "amount":2500.75,
  "currency":"USD",
  "date":"2026-09-18"
}
"""

@app.post("/extract", response_model=InvoiceResponse)
def extract(data: InvoiceRequest):

    if not data.text.strip():
        return InvoiceResponse(
            vendor="",
            amount=0,
            currency="",
            date=""
        )

    response = ollama.chat(
        model="llama3.2",
        messages=[
            {
                "role":"user",
                "content":PROMPT + "\n\nInvoice:\n" + data.text
            }
        ]
    )

    text = response["message"]["content"]

    print("========== RAW OUTPUT ==========")
    print(text)
    print("================================")
    try:
        parsed = json.loads(text)
    except Exception as e:
        print("JSON ERROR:", e)
        print(text)
        parsed = {}

    # Handle alternate field names
    if "due_date" in parsed:
        parsed["date"] = parsed.pop("due_date")

    if "total" in parsed and "amount" not in parsed:
        parsed["amount"] = parsed.pop("total")

    if "vendor_name" in parsed and "vendor" not in parsed:
        parsed["vendor"] = parsed.pop("vendor_name")

    return InvoiceResponse(**parsed)