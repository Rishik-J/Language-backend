"""
app/agents/optimizer.py

Optimizer/Critic agent: evaluates and refines the selected components for cost,
performance, and completeness using the OpenAI Responses API.
"""
import os
import json
import logging
from typing import Dict, Any, List
import pprint

from openai import OpenAI
from schemas import OptimizedPlan, ComponentSpec
from .systemprompts import OPTIMIZER_PROMPT

# Initialize OpenAI Responses client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

async def optimize_plan(
    components_dict: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    logging.info("[Optimizer] Entry: optimize_plan")
    logging.debug(f"[Optimizer] Received components_dict: {pprint.pformat(components_dict)[:500]}")
    logging.debug(f"[Optimizer] Received context: {pprint.pformat(context)[:500]}")
    try:
        components: List[Dict[str, Any]] = components_dict.get("components", [])
        constraints: List[str] = context.get("constraints", [])
        logging.debug(f"[Optimizer] Components: {components}")
        logging.debug(f"[Optimizer] Constraints: {constraints}")
        payload = {
            "components": components,
            "constraints": constraints
        }
        logging.debug(f"[Optimizer] Payload for OpenAI: {pprint.pformat(payload)[:500]}")
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": OPTIMIZER_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        logging.info("[Optimizer] OpenAI API call complete.")
        content = response.output[0].content
        logging.debug(f"[Optimizer] Raw OpenAI response: {str(content)[:500]}")
        if isinstance(content, list):
            content = content[0]
        if hasattr(content, 'text'):
            content = content.text
        if isinstance(content, str):
            parsed = json.loads(content)
        else:
            parsed = content
        logging.debug(f"[Optimizer] Parsed response: {pprint.pformat(parsed)[:500]}")
        if "components" not in parsed or parsed["components"] is None:
            parsed["components"] = []
        if "ambiguities" not in parsed or parsed["ambiguities"] is None:
            parsed["ambiguities"] = []
        # Only set needs_clarification to True if there are real ambiguities
        parsed["needs_clarification"] = bool(parsed.get("ambiguities")) and len(parsed["ambiguities"]) > 0
        optimized = OptimizedPlan(**parsed)
        comp_dicts = [c.model_dump() for c in optimized.components]
        logging.info(f"[Optimizer] Optimized {len(comp_dicts)} components.")
        logging.debug(f"[Optimizer] Returning: components={comp_dicts}, needs_clarification={optimized.needs_clarification}, ambiguities={optimized.ambiguities}")
        logging.info("[Optimizer] Exit: optimize_plan")
        return {
            "components": comp_dicts,
            "needs_clarification": optimized.needs_clarification,
            "ambiguities": optimized.ambiguities
        }
    except Exception as e:
        logging.error(f"[Optimizer] Error: {e}", exc_info=True)
        logging.info("[Optimizer] Returning original components due to error.")
        return {
            "components": components_dict.get("components", []),
            "needs_clarification": False,
            "ambiguities": []
        }