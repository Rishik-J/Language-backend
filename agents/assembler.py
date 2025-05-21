import os
import json
import logging
from typing import Dict, Any
import pprint

from openai import OpenAI
from schemas import AssemblyResult
from memory.vector_store import vector_store
from .systemprompts import FLOW_ASSEMBLER_PROMPT

# Initialize OpenAI Responses client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

async def assemble_flow(
    optimized_plan: Dict[str, Any],
    full_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Assembles a Langflow JSON workflow by:
    1. Retrieving templates for each component
    2. Invoking the OpenAI Responses API with components and templates
    3. Generating a workflow that uses exact component names and structure
    """
    logging.info("[Assembler] Entry: assemble_flow")
    logging.debug(f"[Assembler] Received optimized_plan: {pprint.pformat(optimized_plan)[:500]}")
    logging.debug(f"[Assembler] Received full_context: {pprint.pformat(full_context)[:500]}")
    try:
        components = optimized_plan.get("components", [])
        
        # Retrieve templates for each component in the plan
        component_templates = {}
        for component_spec in components:
            component_name = component_spec.get("component_name")
            if not component_name:
                continue
                
            # Query for templates specific to this component
            logging.info(f"[Assembler] Retrieving template for {component_name}")
            templates = await vector_store.query_templates(component_name=component_name)
            
            # Process the template if found
            if templates:
                try:
                    template_data = json.loads(templates[0]["document"])
                    component_templates[component_name] = template_data
                    logging.info(f"[Assembler] Found template for {component_name}")
                except json.JSONDecodeError:
                    logging.warning(f"[Assembler] Could not parse template for {component_name}")
            else:
                logging.warning(f"[Assembler] No template found for component {component_name}")
        
        # Build the prompt payload
        prompt_payload = {
            "components": components,
            "templates": component_templates,
            "notes": {
                "Conform to Langflow JSON schema": True,
                "Use exact component names from templates": True,
                "Ensure connections are logically valid": True
            }
        }
        logging.debug(f"[Assembler] Payload for OpenAI: {pprint.pformat(prompt_payload)[:500]}")

        # Call the official Responses API
        response = client.responses.create(
            model="gpt-4o",
            input=[
                {
                    "role": "system",
                    "content": FLOW_ASSEMBLER_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload, ensure_ascii=False),
                },
            ],
            text={"format": {"type": "json_object"}},
        )
        logging.info("[Assembler] OpenAI API call complete.")

        # Get the content from the response
        content = response.output[0].content
        logging.debug(f"[Assembler] Raw OpenAI response: {str(content)[:500]}")
        
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

        # If the top-level keys are 'nodes' and 'edges', wrap them in 'flow_json'
        if isinstance(parsed, dict) and "nodes" in parsed and "edges" in parsed and "flow_json" not in parsed:
            parsed = {"flow_json": parsed}
        logging.debug(f"[Assembler] Parsed response: {pprint.pformat(parsed)[:500]}")

        # Parse and validate against our Pydantic schema
        result = AssemblyResult(**parsed)
        logging.info("[Assembler] Parsed AssemblyResult successfully.")
        logging.debug(f"[Assembler] Returning flow_json: {pprint.pformat(result.flow_json)[:500]}")
        logging.info("[Assembler] Exit: assemble_flow")
        return result.flow_json

    except Exception as e:
        logging.error(f"[Assembler] Error: {e}", exc_info=True)
        # Fallback to a simple linear flow with correct structure
        nodes = []
        for comp in optimized_plan.get("components", []):
            node = {
                "id": comp["step"].lower().replace(" ", "_"),
                "type": comp["component_name"],
                "position": {"x": len(nodes) * 200, "y": 100},
                "data": comp.get("parameters", {})
            }
            nodes.append(node)
            
        edges = []
        for i in range(len(nodes) - 1):
            edge = {
                "id": f"e{i+1}",
                "source": nodes[i]["id"],
                "target": nodes[i+1]["id"]
            }
            edges.append(edge)
            
        logging.info("[Assembler] Returning fallback flow with correct node/edge structure.")
        return {"nodes": nodes, "edges": edges}