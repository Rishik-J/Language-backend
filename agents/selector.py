"""
app/agents/selector.py

Component Selector agent: maps abstract workflow steps to concrete Langflow components
using RAG over documentation chunks and component templates stored in Chroma DB and the OpenAI Responses API.
"""
import os
import json
import logging
import pprint
from typing import Dict, Any, List

from openai import OpenAI
from schemas import ComponentSpec, ComponentSelection
from memory.vector_store import vector_store
from .systemprompts import SELECTOR_PROMPT

# Initialize OpenAI Responses client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

async def select_components(plan: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Select concrete Langflow components for each abstract step using RAG:
    1. Retrieve documentation chunks relevant to each step from Chroma DB.
    2. Retrieve component templates for potential components.
    3. Build prompt including examples, templates, and available components.
    4. Invoke the OpenAI Responses API to choose one component per step.
    """
    logging.info("[Selector] Entry: select_components")
    logging.debug(f"[Selector] Received plan: {pprint.pformat(plan)[:500]}")
    logging.debug(f"[Selector] Received context: {pprint.pformat(context)[:500]}")
    try:
        steps: List[str] = plan.get("steps", [])
        tech_stack: List[str] = context.get("tech_stack", [])
        constraints: List[str] = context.get("constraints", [])
        logging.debug(f"[Selector] Steps: {steps}")
        logging.debug(f"[Selector] Tech stack: {tech_stack}")
        logging.debug(f"[Selector] Constraints: {constraints}")
        
        # 1. RAG: retrieve docs for each step (documentation only)
        doc_results = []
        for step in steps:
            logging.info(f"[Selector] Querying vector store for docs related to step: {step}")
            docs = await vector_store.query_docs(query=step, content_type="documentation")
            logging.debug(f"[Selector] Retrieved docs for step '{step}': {pprint.pformat(docs)[:500]}")
            doc_results.extend(docs)
        logging.debug(f"[Selector] Total retrieved doc chunks: {len(doc_results)}")
        
        # 2. Collect available components from documentation results
        doc_components = set()
        doc_chunks = []
        for entry in doc_results:
            chunk = entry["document"]
            doc_chunks.append(chunk)
            comp = entry["metadata"].get("component")
            if comp:
                doc_components.add(comp)
        
        # 3. Retrieve templates for all components
        logging.info("[Selector] Retrieving component templates")
        template_results = await vector_store.query_templates(n_results=50)
        
        # Process template results
        component_templates = {}
        for entry in template_results:
            component_name = entry["metadata"].get("component")
            if component_name:
                # Parse JSON template if possible
                try:
                    template_data = json.loads(entry["document"])
                    component_templates[component_name] = template_data
                except json.JSONDecodeError:
                    logging.warning(f"[Selector] Could not parse template for {component_name}")
        
        # Combine both types of components
        available_components = list(doc_components.union(set(component_templates.keys())))
        logging.debug(f"[Selector] Available components: {available_components}")
        
        # 4. Build payload for Responses API
        payload = {
            "steps": steps,
            "tech_stack": tech_stack,
            "constraints": constraints,
            "available_components": available_components,
            "documentation": doc_chunks,
            "templates": component_templates
        }
        logging.debug(f"[Selector] Payload for OpenAI: {pprint.pformat(payload)[:500]}")
        
        # 5. Call the OpenAI Responses API
        response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": SELECTOR_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(payload, ensure_ascii=False),
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        logging.info("[Selector] OpenAI API call complete.")
        content = response.output[0].content
        logging.debug(f"[Selector] Raw OpenAI response: {str(content)[:500]}")
        if isinstance(content, list):
            content = content[0]
        if hasattr(content, 'text'):
            content = content.text
        if isinstance(content, str):
            parsed = json.loads(content)
        else:
            parsed = content
        logging.debug(f"[Selector] Parsed response: {pprint.pformat(parsed)[:500]}")
        selection = ComponentSelection(**parsed)
        valid_comps: List[ComponentSpec] = []
        for comp in selection.components:
            if comp.component_name in available_components:
                valid_comps.append(comp)
            else:
                logging.warning(f"[Selector] Ignoring unsupported component '{comp.component_name}'")
        logging.info(f"[Selector] Selected {len(valid_comps)} valid components.")
        logging.debug(f"[Selector] Returning components: {pprint.pformat([c.dict() for c in valid_comps])[:500]}")
        logging.info("[Selector] Exit: select_components")
        return {"components": [c.dict() for c in valid_comps]}
    except Exception as e:
        logging.error(f"[Selector] Error: {e}", exc_info=True)
        empty = ComponentSelection(components=[])
        logging.info("[Selector] Returning empty component selection due to error.")
        return {"components": []}