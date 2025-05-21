"""
app/agents/clarifier.py

Clarification Agent: formulates follow-up questions based on ambiguities
and parses user answers into structured clarifications using the OpenAI Responses API.
"""
import os
import json
import logging
import pprint
from typing import Dict, Any, List

from openai import OpenAI
from schemas import ClarificationAnswer
from .systemprompts import CLASSIFIER_PROMPT

# Initialize OpenAI Responses client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

async def clarify_requirements(ambiguities: List[str]) -> Dict[str, Any]:
    """
    Given a list of ambiguity questions, ask the OpenAI Responses API to
    provide answers in JSON format under the key 'clarifications'.
    """
    logging.info("[Clarifier] Entry: clarify_requirements")
    logging.debug(f"[Clarifier] Received ambiguities: {pprint.pformat(ambiguities)[:500]}")
    if not ambiguities:
        logging.info("[Clarifier] No ambiguities provided, returning empty clarifications.")
        return {"clarifications": {}}

    try:
        # Prepare the input payload as a JSON string
        payload = json.dumps({"questions": ambiguities}, ensure_ascii=False)
        logging.debug(f"[Clarifier] Payload for OpenAI: {payload}")

        # Call the official Responses API per Quickstart
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content":CLASSIFIER_PROMPT,
                },
                {
                    "role": "user",
                    "content": payload,
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        logging.info("[Clarifier] OpenAI API call complete.")

        # Get the content from the response
        content = response.output[0].content
        logging.debug(f"[Clarifier] Raw OpenAI response: {str(content)[:500]}")
        
        # If content is a list, take the first item
        if isinstance(content, list):
            content = content[0]
            
        # If content is a ResponseOutputText object, get its text
        if hasattr(content, 'text'):
            content = content.text
            
        # If content is a string, parse it as JSON
        if isinstance(content, str):
            parsed = json.loads(content)
        else:
            # If it's already a dict, use it directly
            parsed = content
        logging.debug(f"[Clarifier] Parsed response: {pprint.pformat(parsed)[:500]}")

        # Parse the JSON from the model's response
        answer = ClarificationAnswer(**parsed)
        logging.info("[Clarifier] Parsed clarifications successfully.")
        logging.debug(f"[Clarifier] Returning clarifications: {pprint.pformat(answer.dict())[:500]}")
        logging.info("[Clarifier] Exit: clarify_requirements")
        return answer.dict()

    except json.JSONDecodeError as e:
        logging.error(f"[Clarifier] JSON parsing error: {e}", exc_info=True)
        logging.info("[Clarifier] Returning empty clarifications due to JSON error.")
        # Return empty answers for each question on parse failure
        return {"clarifications": {q: "" for q in ambiguities}}

    except Exception as e:
        logging.error(f"[Clarifier] Error: {e}", exc_info=True)
        logging.info("[Clarifier] Returning empty clarifications due to error.")
        # Return empty answers for each question on any other failure
        return {"clarifications": {q: "" for q in ambiguities}}