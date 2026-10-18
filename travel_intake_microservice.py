import json
from google.colab import userdata
from google import genai
from google.genai import types

# 1. AUTHENTICATE SECURELY FROM COLAB SECRETS
api_key = userdata.get('GEMINI_API_KEY')
client = genai.Client(api_key=api_key)

# 2. RAW CLIENT INTAKE (Simulating an Incoming WhatsApp Message)
raw_whatsapp_message = (
    "Hola, soy el socio 334129. Quiero cotizar hotel todo incluido en Cancún "
    "del 12 al 16 de noviembre para 2 adultos y 1 niño de 8 años. Presupuesto $45,000 MXN."
)

print(f"📩 Incoming Unstructured WhatsApp Message:\n'{raw_whatsapp_message}'\n")

# 3. DEFINE SYSTEM INSTRUCTION & EXTRACTION SCHEMA
system_instruction = (
    "You are the Lead Intake AI Architect for Traveler Club (traveler.com.mx). "
    "Your job is to parse incoming messy travel requests into a strict JSON object. "
    "Never invent missing dates; if incomplete, mark is_complete as false. "
    "Always return valid JSON matching the requested keys."
)

extraction_prompt = f"""
Extract the travel booking details from this message:
"{raw_whatsapp_message}"

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

print("📡 Sending extraction request to Gemini API (Enforcing Structured JSON Mode)...")

# 4. EXECUTE API CALL WITH NATIVE JSON MIME-TYPE (Zero Backticks Guarantee)
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=extraction_prompt,
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.1,  # Low temperature = high extraction fidelity
        response_mime_type="application/json"  # <-- The secret weapon for clean JSON
    )
)

# 5. PYTHON POST-PROCESSING: PARSE RAW TEXT INTO A NATIVE PYTHON DICTIONARY
# json.loads() converts the JSON string into a live Python dictionary
try:
    parsed_quote = json.loads(response.text)
    print("✅ JSON successfully parsed into a native Python dictionary.\n")
except json.JSONDecodeError as e:
    print("❌ Failed to parse JSON string:")
    print(response.text)
    raise e

# 6. EXECUTIVE CONFIRMATION & KEY ACCESS
print("=================== EXECUTIVE INTAKE CONFIRMATION ===================")
print(f"Member ID:            {parsed_quote['member_id']}")
print(f"Destination:          {parsed_quote['destination']}")
print(f"Travel Dates:         {parsed_quote['arrival_date']} to {parsed_quote['departure_date']}")
print(f"Travelers:            {parsed_quote['adults_count']} Adults | {parsed_quote['kids_count']} Kids (Age: {parsed_quote['kids_ages']})")
print(f"Target Budget:        ${parsed_quote['budget_mxn']:,.2f} MXN")
print(f"Request Complete?:    {'🟢 YES (Ready for Quoting)' if parsed_quote['is_complete'] else '🔴 NO (Missing Info)'}")
print("=====================================================================")

# 7. PROOF OF PROGRAMMATIC DATA ACCESS
# Show that we can now do math directly on the parsed dictionary:
standard_margin_target = 0.18  # 18% Traveler Club margin
potential_gross_margin = parsed_quote["budget_mxn"] * standard_margin_target
print(f"💰 Projected Gross Margin Opportunity: ${potential_gross_margin:,.2f} MXN")
