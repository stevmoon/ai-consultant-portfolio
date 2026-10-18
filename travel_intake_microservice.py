"""
Traveler Intelligent Intake Microservice
Description: Ingests unstructured customer WhatsApp messages, validates booking
parameters into strict JSON via Google Gemini API, and computes projected gross booking margins.
"""

import json
import os
from google import genai
from google.genai import types

# 1. AUTHENTICATION & CLIENT INITIALIZATION
# Reads GEMINI_API_KEY from environment variables
api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

# 2. RAW CLIENT INTAKE PAYLOAD
raw_message = (
    "Hola, soy el socio 334129. Quiero cotizar hotel todo incluido en Cancún "
    "del 12 al 16 de noviembre para 2 adultos y 1 niño de 8 años. Presupuesto $45,000 MXN."
)

system_instruction = (
    "You are the Lead Intake AI Architect for Traveler Club (traveler.com.mx). "
    "Your job is to parse incoming travel requests into a strict JSON object. "
    "Never invent missing dates; if incomplete, mark is_complete as false. "
    "Always return valid JSON matching the requested keys."
)

extraction_prompt = f"""
Extract the travel booking details from this message:
"{raw_message}"

Required JSON Schema:
{{
  "member_id": "string",
  "destination": "string",
  "arrival_date": "string",
  "departure_date": "string",
  "adults_count": int,
  "kids_count": int,
  "kids_ages": [int],
  "budget_mxn": float,
  "is_complete": bool
}}
"""

# 3. EXECUTE STRUCTURED JSON EXTRACTION
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=extraction_prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,
        response_mime_type="application/json"
    )
)

parsed_quote = json.loads(response.text)

# 4. EXECUTIVE CONFIRMATION & MARGIN AUDIT
print("=================== EXECUTIVE INTAKE CONFIRMATION ===================")
print(f"Member ID:            {parsed_quote['member_id']}")
print(f"Destination:          {parsed_quote['destination']}")
print(f"Travel Dates:         {parsed_quote['arrival_date']} to {parsed_quote['departure_date']}")
print(f"Travelers:            {parsed_quote['adults_count']} Adults | {parsed_quote['kids_count']} Kids (Age: {parsed_quote['kids_ages']})")
print(f"Target Budget:        ${parsed_quote['budget_mxn']:,.2f} MXN")
print(f"Request Complete?:    {'🟢 YES (Ready for Quoting)' if parsed_quote['is_complete'] else '🔴 NO (Missing Info)'}")

# Projected Gross Margin Calculation
TARGET_MARGIN = 0.18  # 18% Traveler Club margin
projected_margin = parsed_quote["budget_mxn"] * TARGET_MARGIN
print(f"Projected Margin:     ${projected_margin:,.2f} MXN")
print("=====================================================================")
