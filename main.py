"""
main.py

FastAPI backend orchestrator for the AI Architect multi-agent system,
using LangGraph StateGraph to define and run the multi-agent pipeline.
"""
import os
import logging
from typing import TypedDict, Dict, Any, Annotated
import pprint

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from agents.requirement_analyzer import analyze_requirements
from agents.planner import plan_workflow
from agents.selector import select_components
from agents.optimizer import optimize_plan
from agents.clarifier import clarify_requirements
from agents.assembler import assemble_flow
from memory.vector_store import vector_store

# --------------------
# Pydantic schemas for request/response
# --------------------
class DesignRequest(BaseModel):
    prompt: str

class DesignResponse(BaseModel):
    flow_json: Dict[str, Any]

# --------------------
# Graph state definition
# --------------------
class ContextState(TypedDict):
    messages: Annotated[list, add_messages]   # chat history
    context: Dict[str, Any]                  # intermediate pipeline context

# --------------------
# Node implementations
# --------------------
async def node_analyze(state: ContextState) -> Dict[str, Any]:
    logging.info("[Pipeline] Node: analyze - entry.")
    logging.debug(f"[Pipeline] State before analyze: {pprint.pformat(state)[:500]}")
    ctx = await analyze_requirements(state["context"]["prompt"])
    logging.debug(f"[Pipeline] Output from analyze: {pprint.pformat(ctx)[:500]}")
    logging.info("[Pipeline] Node: analyze - exit.")
    return {"context": {**state["context"], **ctx}}

async def node_plan(state: ContextState) -> Dict[str, Any]:
    logging.info("[Pipeline] Node: plan - entry.")
    logging.debug(f"[Pipeline] State before plan: {pprint.pformat(state)[:500]}")
    plan = await plan_workflow(state["context"])
    logging.debug(f"[Pipeline] Output from plan: {pprint.pformat(plan)[:500]}")
    logging.info("[Pipeline] Node: plan - exit.")
    return {"context": {**state["context"], "plan": plan}}

async def node_select(state: ContextState) -> Dict[str, Any]:
    logging.info("[Pipeline] Node: select - entry.")
    logging.debug(f"[Pipeline] State before select: {pprint.pformat(state)[:500]}")
    comps = await select_components(state["context"]["plan"], state["context"])
    logging.debug(f"[Pipeline] Output from select: {pprint.pformat(comps)[:500]}")
    logging.info("[Pipeline] Node: select - exit.")
    return {"context": {**state["context"], "components": comps}}

async def node_optimize(state: ContextState) -> Dict[str, Any]:
    logging.info("[Pipeline] Node: optimize - entry.")
    logging.debug(f"[Pipeline] State before optimize: {pprint.pformat(state)[:500]}")
    optim = await optimize_plan(state["context"]["components"], state["context"])
    logging.debug(f"[Pipeline] Output from optimize: {pprint.pformat(optim)[:500]}")
    logging.info("[Pipeline] Node: optimize - exit.")
    return {"context": {**state["context"], **optim}}

def next_after_optimize(state: ContextState) -> str:
    next_node = "clarify" if state["context"].get("needs_clarification") else "assemble"
    logging.info(f"[Pipeline] Conditional transition after optimize: {next_node}")
    return next_node

async def node_clarify(state: ContextState) -> Dict[str, Any]:
    logging.info("[Pipeline] Node: clarify - entry.")
    logging.debug(f"[Pipeline] State before clarify: {pprint.pformat(state)[:500]}")
    answers = await clarify_requirements(state["context"].get("ambiguities", []))
    logging.debug(f"[Pipeline] Output from clarify: {pprint.pformat(answers)[:500]}")
    logging.info("[Pipeline] Node: clarify - exit.")
    # Remove ambiguities after clarification
    new_context = {**state["context"], "clarifications": answers, "ambiguities": []}
    return {"context": new_context}

async def node_assemble(state: ContextState) -> Dict[str, Any]:
    logging.info("[Pipeline] Node: assemble - entry.")
    logging.debug(f"[Pipeline] State before assemble: {pprint.pformat(state)[:500]}")
    flow = await assemble_flow(state["context"], state["context"])
    logging.debug(f"[Pipeline] Output from assemble: {pprint.pformat(flow)[:500]}")
    logging.info("[Pipeline] Node: assemble - exit.")
    return {"context": {**state["context"], "flow_json": flow}}

# --------------------
# Build and compile the LangGraph pipeline
# --------------------
graph = StateGraph(ContextState)

# Register nodes
graph.add_node("analyze", node_analyze)
graph.add_node("plan", node_plan)
graph.add_node("select", node_select)
graph.add_node("optimize", node_optimize)
graph.add_node("clarify", node_clarify)
graph.add_node("assemble", node_assemble)

# Register edges
graph.add_edge(START, "analyze")
graph.add_edge("analyze", "plan")
graph.add_edge("plan", "select")
graph.add_edge("select", "optimize")
graph.add_conditional_edges("optimize", next_after_optimize)
graph.add_edge("clarify", "analyze")    # loop after clarification
graph.add_edge("assemble", END)
# 'assemble' has no outgoing edges (terminal)

pipeline = graph.compile()

# --------------------
# FastAPI setup & endpoint
# --------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await vector_store.initialize()
    logging.info("Vector store initialized at startup.")
    # Try to print 2 documents from the collection to verify data
    try:
        # Get up to 2 document ids (if any)
        results = await vector_store._collection.get(limit=2)
        docs = results.get("documents", [[]])[0]
        ids = results.get("ids", [[]])[0]
        logging.info(f"Sample Chroma DB docs: {docs}")
        print(f"Sample Chroma DB docs: {docs}")
        logging.info(f"Sample Chroma DB ids: {ids}")
        print(f"Sample Chroma DB ids: {ids}")
    except Exception as e:
        logging.error(f"Could not fetch sample docs from Chroma DB: {e}")
        print(f"Could not fetch sample docs from Chroma DB: {e}")
    yield
    # (Optional) Add any shutdown/cleanup code here

app = FastAPI(title="AI Architect Service", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@app.post("/design", response_model=DesignResponse)
async def design_workflow(request: DesignRequest):
    logging.info("[API] /design endpoint called.")
    initial_state = {"messages": [], "context": {"prompt": request.prompt}}
    logging.debug(f"[API] Initial pipeline state: {pprint.pformat(initial_state)[:500]}")
    try:
        result_state = await pipeline.ainvoke(input=initial_state)
        logging.debug(f"[API] Final pipeline state: {pprint.pformat(result_state)[:500]}")
        flow = result_state["context"].get("flow_json", {})
        logging.info("[API] /design endpoint completed successfully.")
        return DesignResponse(flow_json=flow)
    except Exception as e:
        logging.error("[API] Design pipeline failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Design process error")


# Run the server (if running directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

