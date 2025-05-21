"""
app/agents/requirement_analyzer.py

Requirement Analyzer agent: parses free-text user prompts into structured RequirementContext
using the OpenAI Responses API.
"""
import os
import json
import logging
from typing import Dict, Any
import pprint

from openai import OpenAI
from schemas import RequirementContext
from .systemprompts import REQUIREMENT_ANALYZER_PROMPT

# Initialize OpenAI Responses client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

def ensure_list_fields(parsed):
    for key in ["key_tasks", "tech_stack", "constraints", "ambiguities"]:
        value = parsed.get(key)
        if isinstance(value, str):
            # If the model returned a string, convert to empty list if "not specified" or similar
            if value.strip().lower() in ["not specified", "none specified", "abstract steps only", ""]:
                parsed[key] = [value]
        elif value is None:
            parsed[key] = []
    return parsed

async def analyze_requirements(user_prompt: str) -> Dict[str, Any]:
    """
    Parse the user prompt into a structured RequirementContext.
    :param user_prompt: Free-text description of the desired AI workflow.
    :return: Dictionary matching the RequirementContext schema.
    """
    logging.info("[RequirementAnalyzer] Entry: analyze_requirements")
    logging.debug(f"[RequirementAnalyzer] Received user_prompt: {user_prompt!r}")
    try:
        logging.info("[RequirementAnalyzer] Sending request to OpenAI API for requirement extraction.")
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": REQUIREMENT_ANALYZER_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        logging.info("[RequirementAnalyzer] OpenAI API call complete.")
        content = response.output[0].content
        logging.debug(f"[RequirementAnalyzer] Raw OpenAI response: {str(content)[:500]}")
        if isinstance(content, list):
            content = content[0]
        if hasattr(content, 'text'):
            content = content.text
        if isinstance(content, str):
            parsed = json.loads(content)
        else:
            parsed = content
        logging.debug(f"[RequirementAnalyzer] Parsed response before coercion: {pprint.pformat(parsed)[:500]}")
        parsed = ensure_list_fields(parsed)
        logging.debug(f"[RequirementAnalyzer] Parsed and coerced response: {pprint.pformat(parsed)[:500]}")
        context = RequirementContext(**parsed)
        logging.info("[RequirementAnalyzer] Parsed context successfully.")
        logging.debug(f"[RequirementAnalyzer] Returning context: {pprint.pformat(context.model_dump())[:500]}")
        logging.info("[RequirementAnalyzer] Exit: analyze_requirements")
        return context.model_dump()
    except Exception as e:
        logging.error(f"[RequirementAnalyzer] Error: {e}", exc_info=True)
        empty = RequirementContext(
            use_case="",
            key_tasks=[],
            tech_stack=[],
            constraints=[],
            ambiguities=[]
        )
        logging.info("[RequirementAnalyzer] Returning empty context due to error.")
        return empty.model_dump()
