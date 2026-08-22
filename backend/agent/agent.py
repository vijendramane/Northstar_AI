import json
import os
import re
import time
from pathlib import Path
from typing import Any


from dotenv import load_dotenv
from google import genai
from google.genai import types

from agent.profile import CustomerProfileUpdate
from agent.tools import (
    create_site_visit,
    get_site_visit_slots,
    request_human_callback,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY is missing")


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(api_key=API_KEY)


# =========================================================
# MODELS
# =========================================================

PRIMARY_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)

FALLBACK_MODEL = os.getenv(
    "GEMINI_FALLBACK_MODEL",
    "gemini-3.6-flash",
)


# =========================================================
# GEMINI TOOL DECLARATIONS
# =========================================================

SITE_VISIT_TOOL = types.FunctionDeclaration(
    name="create_site_visit",
    description=(
        "Book a site visit for Northstar One. "
        "Only use this when the customer explicitly "
        "wants to schedule a site visit and provides "
        "a specific available slot."
    ),
    parameters={
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "The customer's conversation session ID.",
            },
            "slot": {
                "type": "string",
                "description": (
                    "The exact requested site visit slot, "
                    "for example 'Saturday 11:00 AM'."
                ),
            },
        },
        "required": [
            "session_id",
            "slot",
        ],
    },
)


AVAILABLE_SLOTS_TOOL = types.FunctionDeclaration(
    name="get_site_visit_slots",
    description=(
        "Get the currently available Northstar site visit slots. "
        "Use this when the customer wants to schedule a visit "
        "but needs to know the available options."
    ),
    parameters={
        "type": "object",
        "properties": {},
    },
)


HUMAN_CALLBACK_TOOL = types.FunctionDeclaration(
    name="request_human_callback",
    description=(
        "Record that the customer wants to speak with "
        "a human sales representative."
    ),
    parameters={
        "type": "object",
        "properties": {},
    },
)


AGENT_TOOLS = types.Tool(
    function_declarations=[
        SITE_VISIT_TOOL,
        AVAILABLE_SLOTS_TOOL,
        HUMAN_CALLBACK_TOOL,
    ]
)


# =========================================================
# SYSTEM PROMPT
# =========================================================

PROMPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "prompts"
    / "northstar_agent.txt"
)

if not PROMPT_PATH.exists():
    raise FileNotFoundError(
        f"Northstar prompt not found: {PROMPT_PATH}"
    )

SYSTEM_PROMPT = PROMPT_PATH.read_text(
    encoding="utf-8"
)


# =========================================================
# RESPONSE CLEANING
# =========================================================

def clean_response(text: str) -> str:
    """
    Cleans unnecessary Markdown formatting while
    preserving readable paragraphs and bullet points.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove Markdown bold markers
    text = text.replace("**", "")

    # Remove Markdown heading markers
    text = text.replace("### ", "")
    text = text.replace("## ", "")
    text = text.replace("# ", "")

    cleaned_lines = []

    for line in text.split("\n"):

        line = line.strip()

        # Convert Markdown bullets into clean text
        if line.startswith("* "):
            line = line[2:]

        elif line.startswith("- "):
            line = line[2:]

        cleaned_lines.append(line)

    # Remove excessive blank lines
    result = []

    previous_blank = False

    for line in cleaned_lines:

        if not line:

            if not previous_blank:
                result.append("")

            previous_blank = True

        else:

            result.append(line)
            previous_blank = False

    return "\n".join(result).strip()


# =========================================================
# BUILD CONVERSATION
# =========================================================

def build_conversation(
    message: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Converts stored conversation history into a format
    that Gemini can understand.
    """

    conversation_history = conversation_history or []

    conversation_text = ""

    for item in conversation_history:

        role = item.get("role", "customer")
        content = item.get("content", "")

        if not content:
            continue

        if role == "customer":

            conversation_text += (
                f"Customer: {content}\n"
            )

        elif role == "assistant":

            conversation_text += (
                f"Assistant: {content}\n"
            )

    return f"""
Previous conversation:

{conversation_text}

Current customer message:

{message}
"""


# =========================================================
# CALL GEMINI
# =========================================================

def call_gemini(
    model: str,
    contents: str,
) -> str:
    """
    Makes a single Gemini request.

    This function is intentionally kept simple.
    Retry/fallback logic is handled separately.
    """

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=250,
        ),
    )

    if not response.text:
        raise RuntimeError(
            "Gemini returned an empty response."
        )

    return clean_response(response.text)


# =========================================================
# GENERATE CUSTOMER RESPONSE
# =========================================================

def generate_response(
    message: str,
    conversation_history: list[dict] | None = None,
) -> str:
    """
    Generates the normal customer-facing response.

    Primary model:
        GEMINI_MODEL

    Fallback model:
        GEMINI_FALLBACK_MODEL

    Temporary 503/429 errors are retried automatically.
    """

    contents = build_conversation(
        message=message,
        conversation_history=conversation_history,
    )

    # -----------------------------------------------------
    # PRIMARY MODEL
    # -----------------------------------------------------

    for attempt in range(2):

        try:

            print(
                f"Gemini request: "
                f"{PRIMARY_MODEL} "
                f"(attempt {attempt + 1}/3)"
            )

            return call_gemini(
                model=PRIMARY_MODEL,
                contents=contents,
            )

        except Exception as error:

            error_text = str(error)

            print(
                f"Gemini primary model error: "
                f"{error_text}"
            )

            # -----------------------------------------------------
# Quota exhausted - do NOT retry
# -----------------------------------------------------

            if "RESOURCE_EXHAUSTED" in error_text:

                print(
                    "Gemini quota exhausted. "
                    "Skipping retries."
                )

                break


# -----------------------------------------------------
# Non-retryable errors
# -----------------------------------------------------

            if "503" not in error_text and "429" not in error_text:
                raise


# -----------------------------------------------------
# Temporary 429 / 503 errors
# -----------------------------------------------------

            if attempt < 2:

                wait_time = 1

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    # -----------------------------------------------------
    # FALLBACK MODEL
    # -----------------------------------------------------

    print(
        f"Primary model unavailable. "
        f"Trying fallback: {FALLBACK_MODEL}"
    )

    try:

        return call_gemini(
            model=FALLBACK_MODEL,
            contents=contents,
        )

    except Exception as error:

        print(
            f"Fallback Gemini model error: "
            f"{error}"
        )

        raise RuntimeError(
            "Gemini is temporarily unavailable. "
            "Please try again in a moment."
        )



# =========================================================
# TOOL EXECUTION
# =========================================================

def execute_tool(
    function_name: str,
    arguments: dict,
    session_id: str,
) -> dict:
    """
    Executes a tool requested by Gemini.
    """

    print(
        f"Tool requested: {function_name}"
    )

    if function_name == "create_site_visit":

        slot = arguments.get("slot")

        if not slot:
            return {
                "success": False,
                "reason": "missing_slot",
                "message": (
                    "A specific site visit slot "
                    "was not provided."
                ),
            }

        return create_site_visit(
            session_id=session_id,
            slot=slot,
        )

    if function_name == "get_site_visit_slots":

        return get_site_visit_slots()

    if function_name == "request_human_callback":

        return request_human_callback()

    return {
        "success": False,
        "reason": "unknown_tool",
        "message": (
            f"Unknown tool requested: {function_name}"
        ),
    }


# =========================================================
# AGENTIC RESPONSE WITH TOOLS
# =========================================================

def generate_agent_response(
    message: str,
    conversation_history: list[dict] | None,
    session_id: str,
) -> tuple[str, list[dict]]:
    """
    Generates a customer response and allows Gemini
    to call application tools when necessary.

    Returns:
        response_text
        tool_results
    """

    conversation_history = conversation_history or []

    contents = build_conversation(
        message=message,
        conversation_history=conversation_history,
    )

    tool_results = []

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0.7,
        tools=[AGENT_TOOLS],
    )

    # -----------------------------------------------------
    # Primary model
    # -----------------------------------------------------

    for attempt in range(2):

        try:

            print(
                f"Agent request: "
                f"{PRIMARY_MODEL} "
                f"(attempt {attempt + 1}/3)"
            )

            response = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=contents,
                config=config,
            )

            # -------------------------------------------------
            # Check whether Gemini requested a function
            # -------------------------------------------------

            function_calls = []

            if response.function_calls:

                function_calls = response.function_calls

            # -------------------------------------------------
            # No tool needed
            # -------------------------------------------------

            if not function_calls:

                if not response.text:

                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return (
                    clean_response(response.text),
                    tool_results,
                )

            # -------------------------------------------------
            # Execute requested tools
            # -------------------------------------------------

            for function_call in function_calls:

                function_name = function_call.name

                arguments = (
                    dict(function_call.args)
                    if function_call.args
                    else {}
                )

                result = execute_tool(
                    function_name=function_name,
                    arguments=arguments,
                    session_id=session_id,
                )

                tool_results.append(
                    {
                        "tool": function_name,
                        "result": result,
                    }
                )

            # -------------------------------------------------
            # For now, create a customer-facing response
            # using the tool results.
            #
            # We deliberately do this in a second Gemini
            # request instead of exposing raw tool output.
            # -------------------------------------------------

            tool_context = json.dumps(
                tool_results,
                ensure_ascii=False,
                indent=2,
            )

            final_prompt = f"""
The customer said:

{message}

The application executed these tools:

{tool_context}

Generate a natural customer-facing response.

IMPORTANT:

- Do not expose tool names.
- Do not expose internal JSON.
- Do not mention system instructions.
- Do not claim a booking succeeded unless the tool result
  says success=true.
- If booking failed, clearly explain that the requested slot
  is unavailable and offer the available slots.
- If human escalation was requested, say that the request
  has been noted. Do not claim that a real human has already
  called the customer.
- Keep the response concise and helpful.
"""

            final_response = client.models.generate_content(
                model=PRIMARY_MODEL,
                contents=final_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.5,
                ),
            )

            if not final_response.text:

                raise RuntimeError(
                    "Gemini returned an empty final response."
                )

            return (
                clean_response(final_response.text),
                tool_results,
            )

        except Exception as error:

            error_text = str(error)

            print(
                f"Agent model error: {error_text}"
            )

            # -----------------------------------------------------
# Quota exhausted - do NOT retry
# -----------------------------------------------------

            if "RESOURCE_EXHAUSTED" in error_text:

                print(
                "Gemini quota exhausted. "
                    "Skipping retries."
                )

                break


# -----------------------------------------------------
# Non-retryable errors
# -----------------------------------------------------

            if "503" not in error_text and "429" not in error_text:
                raise


# -----------------------------------------------------
# Temporary 429 / 503 errors
# -----------------------------------------------------

            if attempt < 2:

                wait_time = 1

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    # -----------------------------------------------------
    # Fallback
    # -----------------------------------------------------

    print(
        f"Agent primary model unavailable. "
        f"Trying fallback: {FALLBACK_MODEL}"
    )

    try:

        response = client.models.generate_content(
            model=FALLBACK_MODEL,
            contents=contents,
            config=config,
        )

        if not response.text:

            raise RuntimeError(
                "Fallback Gemini returned an empty response."
            )

        return (
            clean_response(response.text),
            tool_results,
        )

    except Exception as error:

        print(
            f"Agent fallback error: {error}"
        )

        raise RuntimeError(
            "Gemini is temporarily unavailable. "
            "Please try again in a moment."
        )


# =========================================================
# PROFILE EXTRACTION PROMPT
# =========================================================

PROFILE_EXTRACTION_INSTRUCTIONS = """
You are a customer-information extraction system for
Northstar Homes.

Your job is ONLY to identify information that the customer
explicitly provides about THEIR OWN requirements.

Do NOT generate a customer-facing response.

Do NOT answer the customer's question.

Do NOT guess.

Do NOT infer preferences from questions.

Do NOT invent values.

The customer may communicate in:

- English
- Hindi
- Hinglish
- a mixture of languages

Understand the meaning regardless of language.

==================================================
CUSTOMER PREFERENCE VS CUSTOMER QUESTION
==================================================

Only save information as a customer preference when the
customer clearly expresses what THEY want.

Example:

Customer:
"I want a 3 BHK."

Extract:
configuration = "3 BHK"


Customer:
"I'm looking for a 3 BHK."

Extract:
configuration = "3 BHK"


Customer:
"Mujhe 3 BHK chahiye."

Extract:
configuration = "3 BHK"


Customer:
"Do you have 3 BHK apartments?"

Extract:
configuration = null


Customer:
"Is 3 BHK available?"

Extract:
configuration = null


Customer:
"What configurations are available?"

Extract:
configuration = null


Customer:
"Do you have villas or plots?"

Extract:
configuration = null


Customer:
"Are villas available?"

Extract:
configuration = null


The fact that a customer asks about something does NOT mean
they want that thing.


# -----------------------------------------------------
# BUDGET
# -----------------------------------------------------

budget_patterns = [
    # budget of 2 crore
    r"(?:budget|budjet)\s+(?:of|od|is|around|approx|approximately)?\s*"
    r"(?:₹|rs\.?|inr)?\s*"
    r"(\d+(?:\.\d+)?)\s*(crore|crores|cr|lakh|lakhs|lac|lacs)",

    # around 2 crore / upto 2 crore / up to 2 crore
    r"(?:around|approx|approximately|upto|up\s+to|under|within)\s*"
    r"(?:₹|rs\.?|inr)?\s*"
    r"(\d+(?:\.\d+)?)\s*(crore|crores|cr|lakh|lakhs|lac|lacs)",

    # ₹2 crore / Rs 2 crore
    r"(?:₹|rs\.?|inr)\s*"
    r"(\d+(?:\.\d+)?)\s*(crore|crores|cr|lakh|lakhs|lac|lacs)",

    # plain "2 crore budget"
    r"(\d+(?:\.\d+)?)\s*(crore|crores|cr|lakh|lakhs|lac|lacs)"
    r"\s*(?:budget)?",
]

for pattern in budget_patterns:

    match = re.search(
        pattern,
        lower,
        re.IGNORECASE,
    )

    if match:

        amount = match.group(1)
        unit = match.group(2).lower()

        unit_normalized = {
            "cr": "crore",
            "crore": "crore",
            "crores": "crore",
            "lakh": "lakh",
            "lakhs": "lakh",
            "lac": "lakh",
            "lacs": "lakh",
        }.get(unit, unit)

        updates["budget"] = (
            f"₹{amount} {unit_normalized}"
        )

        break 
==================================================
PURPOSE
==================================================

Extract purpose only when the customer expresses it.

Example:

"Khud rehne ke liye chahiye."

purpose = "self-use"


"I want it as an investment."

purpose = "investment"


"Is this good for investment?"

purpose = null


==================================================
TIMELINE
==================================================

Extract timeline only when the customer gives their own
purchase timeline.

Example:

"Agale 3 mahine mein lena hai."

timeline = "within the next 3 months"


"I want to buy next year."

timeline = "next year"


"When should I buy?"

timeline = null


==================================================
LOCATION PREFERENCE
==================================================

Extract location preference only when the customer states
where THEY want to live or buy.

Example:

"Mujhe Gurugram mein hi chahiye."

location_preference = "Gurugram"


"Do you have projects in Mumbai?"

location_preference = null


==================================================
LANGUAGE
==================================================

Identify the language/style used by the customer when
reasonably clear.

Possible values:

English
Hindi
Hinglish

Do not guess if unclear.

==================================================
INTEREST LEVEL
==================================================

Only infer interest level from clear customer intent.

Possible values:

low
medium
high

Examples:

"Just checking prices."

interest_level = "low"


"I'm comparing a few projects."

interest_level = "medium"


"I really like this. Can I visit this weekend?"

interest_level = "high"


Do not assign an interest level when there is insufficient
evidence.

==================================================
OBJECTIONS
==================================================

Only extract an objection when the customer clearly expresses
a concern or objection.

Examples:

"₹1.75 crore is too expensive."

objection = "price"


"I'm worried about the location."

objection = "location"


"Is there any discount?"

objection = null

A question about a topic is not automatically an objection.




==================================================
INTENT CLASSIFICATION
==================================================

Classify the customer's latest message into ONE intent.

Allowed values only:

general
qualification
pricing_question
site_visit
human_escalation
callback
do_not_contact

Definitions:

general
→ greetings, casual questions, unsupported questions

qualification
→ customer shares requirements like budget,
configuration, purpose or timeline

pricing_question
→ asking about price or cost

site_visit
→ wants to visit the property or schedule a visit

human_escalation
→ wants to speak with sales or a human representative

callback
→ asks to be contacted later or says they are busy

do_not_contact
→ clearly asks not to be contacted again

Return only one intent.


==================================================
EXISTING PROFILE
==================================================

The existing profile is provided only as context.

Extract ONLY NEW information explicitly present in the
current customer message.

If the current message does not mention a field, return null.

Do NOT copy existing profile values into the output.

==================================================
OUTPUT
==================================================

Return only structured data matching the provided schema.
"""


# =========================================================
# PROFILE EXTRACTION
# =========================================================

def _extract_profile_with_model(
    model: str,
    extraction_prompt: str,
) -> dict:
    """
    Makes one structured profile-extraction request.
    """

    response = client.models.generate_content(
        model=model,
        contents=extraction_prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CustomerProfileUpdate,
            temperature=0,
        ),
    )

    if not response.text:
        return {}

    try:

        data = json.loads(response.text)

    except json.JSONDecodeError:

        print(
            "Profile extraction returned invalid JSON."
        )

        return {}

    if not isinstance(data, dict):
        return {}

    # Remove empty values
    cleaned_data = {}

    for key, value in data.items():

        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        cleaned_data[key] = value

    return cleaned_data


# =========================================================
# EXTRACT CUSTOMER PROFILE UPDATE
# =========================================================


def quick_profile_extract(message: str) -> dict:
    """
    Fast local extraction for obvious customer information.

    This avoids an extra Gemini request for common
    qualification messages.
    """

    text = message.strip()
    lower = text.lower()

    updates = {}

    # -----------------------------------------------------
    # NAME
    # -----------------------------------------------------

    name_match = re.search(
        r"\b(?:i am|i'm|my name is|this is)\s+([A-Za-z]{2,30})",
        text,
        re.IGNORECASE,
    )

    if name_match:
        name = name_match.group(1).strip()

        if name.lower() not in {
            "looking",
            "interested",
            "searching",
            "planning",
            "wanting",
        }:
            updates["name"] = name

    # -----------------------------------------------------
    # CONFIGURATION
    # -----------------------------------------------------

    config_match = re.search(
        r"\b([2345])\s*[-]?\s*BHK\b",
        text,
        re.IGNORECASE,
    )

    if config_match:
        updates["configuration"] = (
            f"{config_match.group(1)} BHK"
        )

    # -----------------------------------------------------
    # BUDGET
    # -----------------------------------------------------

    budget_patterns = [
        r"(?:budget|around|upto|up to|under|within)\s*(?:of\s*)?"
        r"(?:₹|rs\.?|inr)?\s*"
        r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|lacs)",
        r"(?:₹|rs\.?|inr)\s*"
        r"(\d+(?:\.\d+)?)\s*(crore|cr|lakh|lac|lacs)",
    ]

    for pattern in budget_patterns:
        match = re.search(
            pattern,
            lower,
            re.IGNORECASE,
        )

        if match:
            amount = match.group(1)
            unit = match.group(2)

            unit_normalized = {
                "cr": "crore",
                "crore": "crore",
                "lakh": "lakh",
                "lac": "lakh",
                "lacs": "lakh",
            }.get(unit.lower(), unit.lower())

            updates["budget"] = (
                f"₹{amount} {unit_normalized}"
            )

            break

    # -----------------------------------------------------
    # PURPOSE
    # -----------------------------------------------------

    self_use_patterns = [
        "for myself",
        "for me",
        "self use",
        "self-use",
        "khud rehne",
        "khud ke liye",
        "rehne ke liye",
    ]

    investment_patterns = [
        "investment",
        "invest kar",
        "investing",
        "rental income",
        "rent ke liye",
    ]

    if any(
        phrase in lower
        for phrase in self_use_patterns
    ):
        updates["purpose"] = "self-use"

    elif any(
        phrase in lower
        for phrase in investment_patterns
    ):
        updates["purpose"] = "investment"

    # -----------------------------------------------------
    # TIMELINE
    # -----------------------------------------------------

    if (
        "within 3 months" in lower
        or "next 3 months" in lower
        or "3 months" in lower
    ):
        updates["timeline"] = (
            "within the next 3 months"
        )

    elif (
        "within 6 months" in lower
        or "next 6 months" in lower
        or "6 months" in lower
    ):
        updates["timeline"] = (
            "within the next 6 months"
        )

    elif (
        "immediately" in lower
        or "as soon as possible" in lower
        or "jaldi" in lower
    ):
        updates["timeline"] = "immediately"

    # -----------------------------------------------------
    # LANGUAGE
    # -----------------------------------------------------

    hindi_words = [
        "mujhe",
        "chahiye",
        "hai",
        "ke liye",
        "karna",
        "rehne",
        "ghar",
    ]

    hindi_score = sum(
        word in lower
        for word in hindi_words
    )

    if hindi_score >= 2:
        updates["preferred_language"] = "hinglish"

    return updates


def extract_profile_update(
    message: str,
    existing_profile: dict[str, Any],
) -> dict:
    
    quick_updates = quick_profile_extract(message)

    if quick_updates:
        return quick_updates

    extraction_prompt = f"""
{PROFILE_EXTRACTION_INSTRUCTIONS}

==================================================
EXISTING CUSTOMER PROFILE
==================================================

{json.dumps(
    existing_profile,
    ensure_ascii=False,
    indent=2,
)}

==================================================
CURRENT CUSTOMER MESSAGE
==================================================

{message}

==================================================
TASK
==================================================

Extract ONLY NEW information explicitly provided in the
current customer message.

If a field is not mentioned in the current message,
return null for that field.

Do not copy information from the existing profile.

Do not treat questions as customer preferences.

Do not invent values.
"""

    # -----------------------------------------------------
    # PRIMARY MODEL WITH RETRIES
    # -----------------------------------------------------

    for attempt in range(2):

        try:

            print(
                f"Profile extraction: "
                f"{PRIMARY_MODEL} "
                f"(attempt {attempt + 1}/3)"
            )

            return _extract_profile_with_model(
                model=PRIMARY_MODEL,
                extraction_prompt=extraction_prompt,
            )

        except Exception as error:

            error_text = str(error)

            print(
                f"Profile extraction error: "
                f"{error_text}"
            )

            # Retry only temporary errors
            # -----------------------------------------------------
# Quota exhausted - do NOT retry
# -----------------------------------------------------

            if "RESOURCE_EXHAUSTED" in error_text:

                print(
                    "Gemini quota exhausted. "
                    "Skipping retries."
                )

                break


# -----------------------------------------------------
# Non-retryable errors
# -----------------------------------------------------

            if "503" not in error_text and "429" not in error_text:
                raise


# -----------------------------------------------------
# Temporary 429 / 503 errors
# -----------------------------------------------------

            if attempt < 2:

                wait_time = 1

                print(
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    # -----------------------------------------------------
    # FALLBACK MODEL
    # -----------------------------------------------------

    print(
        f"Profile extraction primary model unavailable. "
        f"Trying fallback: {FALLBACK_MODEL}"
    )

    try:

        return _extract_profile_with_model(
            model=FALLBACK_MODEL,
            extraction_prompt=extraction_prompt,
        )

    except Exception as error:

        print(
            f"Profile extraction fallback error: "
            f"{error}"
        )

        # Profile extraction should NOT break the
        # customer's conversation.
        #
        # If extraction fails, return an empty update
        # and allow the normal AI response to continue.

        return {}
    
    