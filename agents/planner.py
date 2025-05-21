"""
app/agents/planner.py

Planner agent: generates an abstract workflow plan using retrieval-augmented generation (RAG)
with Chroma DB retrieval and the OpenAI Responses API.
"""
import os
import json
import logging
import uuid
import pprint
from typing import Dict, Any, List
from .systemprompts import PLANNER_PROMPT

from openai import OpenAI
from schemas import WorkflowPlan
from memory.vector_store import vector_store

# Initialize OpenAI Responses client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

async def plan_workflow(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate an abstract workflow plan.
    1. Retrieve similar past plans from Chroma DB.
    2. Incorporate retrieved examples into the prompt for RAG.
    3. Call the OpenAI Responses API to produce a JSON plan.
    4. Store the new plan back into Chroma DB for future retrieval.
    """
    logging.info("[Planner] Entry: plan_workflow")
    logging.debug(f"[Planner] Received context: {pprint.pformat(context)[:500]}")
    try:
        # 1. Retrieve similar past workflows from Chroma DB (async)
        # use_case = context.get("use_case", "")
        # past_entries = await vector_store.query_patterns(use_case, n_results=3)
        # examples: List[str] = [entry["document"] for entry in past_entries]
        # logging.debug(f"Retrieved {len(examples)} past examples for use case '{use_case}'")

        # # 2. Build the prompt payload combining context and RAG examples
        # payload = {
        #     "use_case": use_case,
        #     "key_tasks": context.get("key_tasks", []),
        #     "tech_stack": context.get("tech_stack", []),
        #     "constraints": context.get("constraints", []),
        #     "examples": examples
        # }
        
        payload = {
            "use_case":    context.get("use_case", ""),
            "key_tasks":   context.get("key_tasks", []),
            "tech_stack":  context.get("tech_stack", []),
            "constraints": context.get("constraints", [])
        }
        logging.debug(f"[Planner] Payload for OpenAI: {pprint.pformat(payload)[:500]}")

        # 3. Call the Responses API to generate structured JSON (updated for new API)
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content":PLANNER_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        logging.info("[Planner] OpenAI API call complete.")
        content = response.output[0].content
        logging.debug(f"[Planner] Raw OpenAI response: {str(content)[:500]}")
        if isinstance(content, list):
            content = content[0]
        if hasattr(content, 'text'):
            content = content.text
        if isinstance(content, str):
            parsed = json.loads(content)
        else:
            parsed = content
        logging.debug(f"[Planner] Parsed response: {pprint.pformat(parsed)[:500]}")
        plan = WorkflowPlan(**parsed)
        logging.info("[Planner] Parsed WorkflowPlan successfully.")
        logging.debug(f"[Planner] Returning plan: {pprint.pformat(plan.model_dump())[:500]}")
        logging.info("[Planner] Exit: plan_workflow")
        return plan.model_dump()

    except Exception as e:
        logging.error(f"[Planner] Error: {e}", exc_info=True)
        # Fallback: return an empty plan if anything goes wrong
        empty = WorkflowPlan(steps=[])
        logging.info("[Planner] Returning empty plan due to error.")
        return empty.model_dump()