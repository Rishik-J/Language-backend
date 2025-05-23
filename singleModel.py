import os
import json
import logging
from typing import Dict, Any, List
import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

from openai import OpenAI
from memory.vector_store import vector_store

# --- Request/Response models ---
class DesignRequest(BaseModel):
    prompt: str
    api_provider: str = "groq"  # Default to groq, can be "openai" or "groq"

class DesignResponse(BaseModel):
    flow_json: Dict[str, Any]

# --- Initialize API clients ---
# OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
# Log a warning if the API key looks like a placeholder
if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("your_"):
    logging.warning("OpenAI API key appears to be missing or uses a placeholder. Check your environment variables.")

# GROQ client
groq_client = OpenAI(
    base_url="https://api.groq.com/openai/v1/",
    api_key=os.getenv("GROQ_API_KEY", "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")
)

# --- Main RAG function ---
async def generate_flow(prompt: str, api_provider: str = "groq") -> Dict[str, Any]:
    """Generate a flow using RAG pattern with either GROQ or OpenAI
    
    Args:
        prompt: The user prompt
        api_provider: Which API to use - "groq" or "openai"
    """
    logging.info(f"[RAG] Generating flow for prompt using {api_provider} API")
    
    try:
        # 1. Retrieve relevant documentation and templates from ChromaDB
        logging.info(f"[RAG] Querying vector store for documentation related to: '{prompt[:100]}...'")
        doc_results = await vector_store.query_docs(
            query=prompt, 
            content_type="documentation",
            n_results=5
        )
        logging.info(f"[RAG] Retrieved {len(doc_results)} documentation chunks")
        
        # Log documentation details
        for i, doc in enumerate(doc_results):
            component = doc["metadata"].get("component", "unknown")
            doc_type = doc["metadata"].get("doc_type", "unknown")
            doc_id = doc["id"]
            doc_preview = doc["document"][:150] + "..." if len(doc["document"]) > 150 else doc["document"]
            logging.info(f"[RAG] Doc {i+1}/{len(doc_results)}: ID={doc_id}, Component={component}, Type={doc_type}")
            logging.debug(f"[RAG] Doc {i+1} Content Preview: {doc_preview}")
        
        # 2. Get templates for potential components
        logging.info("[RAG] Retrieving component templates")
        template_results = await vector_store.query_templates(n_results=20)
        logging.info(f"[RAG] Retrieved {len(template_results)} component templates")
        
        # Log template details
        template_names = []
        for i, entry in enumerate(template_results):
            component_name = entry["metadata"].get("component", "unknown")
            category = entry["metadata"].get("category", "unknown")
            template_names.append(component_name)
            logging.info(f"[RAG] Template {i+1}/{len(template_results)}: Component={component_name}, Category={category}")
        
        # Process templates
        component_templates = {}
        successful_templates = 0
        for entry in template_results:
            component_name = entry["metadata"].get("component")
            if component_name:
                try:
                    template_data = json.loads(entry["document"])
                    component_templates[component_name] = template_data
                    successful_templates += 1
                except json.JSONDecodeError:
                    logging.warning(f"[RAG] Could not parse template for {component_name}")
        
        logging.info(f"[RAG] Successfully parsed {successful_templates}/{len(template_results)} templates")
        logging.info(f"[RAG] Available component templates: {', '.join(component_templates.keys())}")
        
        # 3. Prepare documents for context
        doc_chunks = [entry["document"] for entry in doc_results]
        
        # 4. Build the system prompt
        system_prompt = """
You are an expert Langflow workflow designer specializing in creating precise, functional workflows for language models and AI applications.

# CRITICAL REQUIREMENTS
Your task is to design a workflow that EXACTLY follows these specifications:

1. COMPONENT NAMING: 
   - The "type" field for each node MUST EXACTLY match a component name from the provided templates
   - Do NOT improvise component names - use ONLY component names that exist in the templates
   - Component names are case-sensitive and must match precisely (e.g., "OpenAIEmbeddings" not "OpenAIEmbedding")

2. COMPONENT PARAMETERS:
   - Only use parameters that are defined in the template for each component
   - Parameter names must match exactly what's in the template structure
   - Set appropriate values for required parameters

3. CONNECTIONS:
   - Create logical connections between components based on their functionality
   - Ensure source and target components are compatible (e.g., embeddings connect to vector stores)
   - Each edge must have a unique ID (e.g., "e1", "e2")
   - Sources and targets must reference valid node IDs

4. JSON FORMAT:
   - Respond with a SINGLE valid JSON object with exactly one top-level key: "flow_json"
   - "flow_json" must contain exactly two keys: "nodes" and "edges"
   - Do NOT include any explanation text outside the JSON

# OUTPUT FORMAT SPECIFICATION

```
{
  "flow_json": {
    "nodes": [
      {
        "id": "unique_identifier_string",
        "type": "ExactComponentNameFromTemplate",
        "position": {"x": number, "y": number},
        "data": {
          "param1": value1,
          "param2": value2
        }
      },
      // additional nodes...
    ],
    "edges": [
      {
        "id": "unique_edge_id",
        "source": "source_node_id",
        "target": "target_node_id"
      },
      // additional edges...
    ]
  }
}
```

# COMPONENT COMPATIBILITY GUIDELINES

Follow these compatibility rules when connecting components:
- DocumentLoaders → TextSplitters → Embeddings → VectorStores
- VectorStores → RetrievalQA or similar retrieval chains
- LLM models can connect to chains, agents, and memory components
- Memory components connect to chains and agents
- Prompts connect to chains and agents

# EXACT EXAMPLES

## Example 1: Document Q&A System
```json
{
  "flow_json": {
    "nodes": [
      {
        "id": "loader",
        "type": "GitLoaderComponent",
        "position": {"x": 100, "y": 100},
        "data": {
          "repo_source": "Remote",
          "clone_url": "https://github.com/example/repo.git",
          "branch": "main"
        }
      },
      {
        "id": "splitter",
        "type": "RecursiveCharacterTextSplitter",
        "position": {"x": 400, "y": 100},
        "data": {
          "chunk_size": 1000,
          "chunk_overlap": 200
        }
      },
      {
        "id": "embedder",
        "type": "OpenAIEmbeddings",
        "position": {"x": 700, "y": 100},
        "data": {
          "model": "text-embedding-3-small"
        }
      },
      {
        "id": "vectorstore",
        "type": "Chroma",
        "position": {"x": 1000, "y": 100},
        "data": {
          "collection_name": "repo_documents",
          "persist_directory": "./chroma_db"
        }
      },
      {
        "id": "llm",
        "type": "OpenAIModel",
        "position": {"x": 700, "y": 300},
        "data": {
          "model_name": "gpt-4o",
          "temperature": 0.2
        }
      },
      {
        "id": "qa",
        "type": "RetrievalQA",
        "position": {"x": 1000, "y": 300},
        "data": {
          "chain_type": "stuff"
        }
      }
    ],
    "edges": [
      {"id": "e1", "source": "loader", "target": "splitter"},
      {"id": "e2", "source": "splitter", "target": "embedder"},
      {"id": "e3", "source": "embedder", "target": "vectorstore"},
      {"id": "e4", "source": "vectorstore", "target": "qa"},
      {"id": "e5", "source": "llm", "target": "qa"}
    ]
  }
}
```

## Example 2: Conversational Agent with Tools
```json
{
  "flow_json": {
    "nodes": [
      {
        "id": "search_tool",
        "type": "GoogleSearchAPIWrapper",
        "position": {"x": 100, "y": 100},
        "data": {
          "api_key": "{{GOOGLE_API_KEY}}",
          "search_engine_id": "{{SEARCH_ENGINE_ID}}"
        }
      },
      {
        "id": "calculator_tool",
        "type": "Calculator",
        "position": {"x": 100, "y": 300},
        "data": {}
      },
      {
        "id": "llm",
        "type": "OpenAIModel",
        "position": {"x": 400, "y": 200},
        "data": {
          "model_name": "gpt-4o",
          "temperature": 0
        }
      },
      {
        "id": "memory",
        "type": "Memory",
        "position": {"x": 400, "y": 400},
        "data": {
          "chat_memory": "BufferMemory",
          "return_messages": true,
          "memory_key": "chat_history"
        }
      },
      {
        "id": "agent",
        "type": "Agent",
        "position": {"x": 700, "y": 200},
        "data": {
          "system_prompt": "You are a helpful assistant that can use tools to find information and perform calculations."
        }
      }
    ],
    "edges": [
      {"id": "e1", "source": "search_tool", "target": "agent"},
      {"id": "e2", "source": "calculator_tool", "target": "agent"},
      {"id": "e3", "source": "llm", "target": "agent"},
      {"id": "e4", "source": "memory", "target": "agent"}
    ]
  }
}
```

# WORKFLOW DESIGN PROCESS
1. Analyze the user's request to understand the workflow needs
2. Select appropriate components from the provided templates
3. Configure each component with valid parameters from its template
4. Arrange components in a logical flow
5. Connect components with appropriate edges
6. Ensure the JSON format is valid and component names match exactly

Study the templates carefully to identify exact component names and valid parameters. If uncertain about a component's purpose or compatibility, refer to the documentation provided.

Now, create a workflow that precisely matches the user's request using only components from the provided templates.
"""
        
        # 5. Build payload for API
        payload = {
            "prompt": prompt,
            "documentation": doc_chunks,
            "templates": component_templates
        }
        
        # 6. Call the appropriate API based on the provider
        if api_provider.lower() == "openai":
            logging.info("[RAG] Using OpenAI Responses API")
            response = openai_client.responses.create(
                model="gpt-4o-mini",  # or a more cost-effective model like "gpt-4o-mini"
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload, ensure_ascii=False),
                    },
                ],
                text={"format": {"type": "json_object"}},
            )
            
            # Process the OpenAI response
            content = response.output[0].content
            if isinstance(content, list):
                content = content[0]
            if hasattr(content, 'text'):
                content = content.text
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content
        else:
            # Default to GROQ
            logging.info("[RAG] Using GROQ API")
            chat_completion = groq_client.chat.completions.create(
                model="gemma2-9b-it",        # Groq model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                response_format={"type": "json_object"}  # keeps JSON-only answers
            )

            # Extract the assistant's JSON text
            content = chat_completion.choices[0].message.content
            parsed = json.loads(content)
            
        # If the top-level keys are 'nodes' and 'edges', wrap them in 'flow_json'
        if "flow_json" not in parsed and {"nodes", "edges"} <= parsed.keys():
            parsed = {"flow_json": parsed}

        return parsed["flow_json"]
    
    except Exception as e:
        logging.error(f"Error generating flow: {e}", exc_info=True)
        # Simple fallback flow in case of errors
        return {}

# --- FastAPI setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    await vector_store.initialize()
    logging.info("Vector store initialized at startup.")
    yield

app = FastAPI(title="LangFlow Designer", version="1.0.0", lifespan=lifespan)
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
    logging.info(f"[API] /design endpoint called with api_provider: {request.api_provider}")
    try:
        flow = await generate_flow(request.prompt, request.api_provider)
        logging.info("[API] Successfully generated flow.")
        return DesignResponse(flow_json=flow)
    except Exception as e:
        logging.error(f"[API] Design process failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Design process error")

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
