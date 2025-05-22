from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import traceback
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

trialAPIJson = {
    "flow_json": {
        "nodes": [
            {
                "id": "embedder",
                "type": "OpenAIEmbeddings",
                "position": {
                    "x": 300,
                    "y": 100
                },
                "data": {
                    "model": "text-embedding-3-small"
                }
            },
            {
                "id": "vectorstore",
                "type": "HCD",
                "position": {
                    "x": 600,
                    "y": 100
                },
                "data": {
                    "collection_name": "my_collection",
                    "username": "hcd-superuser",
                    "password": "HCD_PASSWORD",
                    "api_endpoint": "HCD_API_ENDPOINT"
                }
            },
            {
                "id": "qa",
                "type": "RetrievalQA",
                "position": {
                    "x": 900,
                    "y": 100
                },
                "data": {
                    "chain_type": "Stuff",
                    "llm": "OpenAIModel",
                    "retriever": "vectorstore"
                }
            },
            {
                "id": "llm",
                "type": "OpenAIModel",
                "position": {
                    "x": 300,
                    "y": 250
                },
                "data": {
                    "model_name": "gpt-4",
                    "temperature": 0.5
                }
            }
        ],
        "edges": [
            {
                "id": "e1",
                "source": "embedder",
                "target": "vectorstore"
            },
            {
                "id": "e2",
                "source": "vectorstore",
                "target": "qa"
            },
            {
                "id": "e3",
                "source": "llm",
                "target": "qa"
            }
        ]
    }
}
# trialAPIJson = {
#         "nodes": [
#             {
#                 "id": "embedder",
#                 "type": "OpenAIEmbeddings",
#                 "position": {
#                     "x": 400,
#                     "y": 100
#                 },
#                 "data": {
#                     "model": "text-embedding-3-small"
#                 }
#             },
#             {
#                 "id": "vectorstore",
#                 "type": "HCD",
#                 "position": {
#                     "x": 700,
#                     "y": 100
#                 },
#                 "data": {
#                     "collection_name": "my_collection",
#                     "username": "hcd-superuser",
#                     "password": "HCD_PASSWORD",
#                     "api_endpoint": "HCD_API_ENDPOINT"
#                 }
#             },
#             {
#                 "id": "retrieval_qa",
#                 "type": "RetrievalQA",
#                 "position": {
#                     "x": 1000,
#                     "y": 100
#                 },
#                 "data": {
#                     "llm": "OpenAIModel",
#                     "retriever": "vectorstore"
#                 }
#             }
#         ],
#         "edges": [
#             {
#                 "id": "e1",
#                 "source": "embedder",
#                 "target": "vectorstore"
#             },
#             {
#                 "id": "e2",
#                 "source": "vectorstore",
#                 "target": "retrieval_qa"
#             }
#         ]
#     }

trial8Json = {
  "nodes": [
    {
      "id": "loader",
      "type": "GitLoaderComponent",
      "position": { "x": 100, "y": 100 },
      "data": {
        "repo_source": "Remote",
        "clone_url": "https://github.com/my-org/annual-report.git",
        "branch": "main",
        "file_filter": "*.md"
      }
    },
    {
      "id": "splitter",
      "type": "RecursiveCharacterTextSplitter",
      "position": { "x": 500, "y": 500 },
      "data": {
        "chunk_size": 1000,
        "chunk_overlap": 200
      }
    },
    {
      "id": "embedder",
      "type": "OpenAIEmbeddings",
      "position": { "x": 1000, "y": 1000 },
      "data": {
        "model": "text-embedding-3-small"
      }
    },
    {
      "id": "store",
      "type": "Chroma",
      "position": { "x": 1700, "y": 1500 },
      "data": {
        "collection_name": "annual_report_index",
        "persist_directory": "./chroma_store",
        "search_type": "similarity",
        "number_of_results": 10,
      }
    },
    {
      "id": "llm",
      "type": "OpenAIModel",
      "position": { "x": 300, "y": 300 },
      "data": {
        "model_name": "gpt-4o",
        "temperature": 0.0
      }
    },
    {
      "id": "memory",
      "type": "Memory",
      "position": { "x": 500, "y": 300 },
      "data": {}
    },
    {
      "id": "qa",
      "type": "RetrievalQA",
      "position": { "x": 700, "y": 300 },
      "data": {
        "input_value": "What are the key insights from the annual report?",
        "chain_type": "Stuff"
      }
    }
  ],
  "edges": [
    { "id": "e1", "source": "loader",   "target": "splitter" },
    { "id": "e2", "source": "splitter", "target": "embedder" },
    { "id": "e3", "source": "embedder", "target": "store"    },
    { "id": "e4", "source": "store",    "target": "qa"       },
    { "id": "e5", "source": "llm",      "target": "qa"       },
    { "id": "e6", "source": "memory",   "target": "qa"       }
  ]
}

trial6Json = {
  "nodes": [
    {
      "id": "node1",
      "type": "Create List",
      "position": { "x": 100, "y": 100 },
      "data": {
        "texts": [
          "LangChain is a framework for building LLM apps.",
          "Chroma DB is a vector store for embeddings."
        ]
      }
    },
    {
      "id": "node2",
      "type": "OpenAIEmbeddings",
      "position": { "x": 300, "y": 100 },
      "data": {
        "model": "text-embedding-3-small",
        "chunk_size": 500
      }
    },
    {
      "id": "node3",
      "type": "Chroma",
      "position": { "x": 500, "y": 100 },
      "data": {
        "collection_name": "langflow",
        "persist_directory": "./chroma_store",
        "search_type": "Similarity",
        "number_of_results": 5
      }
    },
    {
      "id": "node4",
      "type": "OpenAI",
      "position": { "x": 700, "y": 50 },
      "data": {
        "model_name": "gpt-3.5-turbo",
        "temperature": 0.1
      }
    },
    {
      "id": "node5",
      "type": "Memory",
      "position": { "x": 700, "y": 200 },
      "data": {}
    },
    {
      "id": "node6",
      "type": "RetrievalQA",
      "position": { "x": 900, "y": 100 },
      "data": {
        "input_value": "What is LangFlow?",
        "chain_type": "Stuff"
      }
    }
  ],
  "edges": [
    {
      "id": "edge1",
      "source": "node1",
      "target": "node2"
    },
    {
      "id": "edge2",
      "source": "node1",
      "target": "node3"
    },
    {
      "id": "edge3",
      "source": "node2",
      "target": "node3"
    },
    {
      "id": "edge4",
      "source": "node3",
      "target": "node6"
    },
    {
      "id": "edge5",
      "source": "node4",
      "target": "node6"
    },
    {
      "id": "edge6",
      "source": "node5",
      "target": "node6"
    }
  ]
}


complexFLow = {
  "nodes": [
    {
      "id": "node1",
      "type": "OpenAIEmbeddings",
      "position": { "x": 100, "y": 100 },
      "data": {
        "description": "Embeds input text into high-dimensional vectors via OpenAI’s embeddings API.",
        "inputs": ["text_documents"],
        "outputs": ["embedding_vectors"]
      }
    },
    {
      "id": "node2",
      "type": "Chroma",
      "position": { "x": 400, "y": 100 },
      "data": {
        "description": "Ingests embeddings (plus document metadata) into a Chroma vector store and performs similarity search.",
        "inputs": ["embedding_vectors", "document_metadata"],
        "outputs": ["retriever"]
      }
    },
    {
      "id": "node3",
      "type": "RetrievalQA",
      "position": { "x": 700, "y": 100 },
      "data": {
        "description": "Retrieval-augmented QA component: takes a Retriever (from Chroma) and an LLM internally configured, plus a user query, and returns an answer with source documents.",
        "inputs": ["retriever", "user_query", "llm"],
        "outputs": ["answer_text", "source_documents"]
      }
    }
  ],
  "edges": [
    { "id": "edge1", "source": "node1", "target": "node2" },
    { "id": "edge2", "source": "node2", "target": "node3" }
  ]
}



trial5Json = {
"nodes": [
{
"id": "node1",
"type": "OpenAIEmbeddings",
"position": { "x": 100, "y": 100 },
"data": {}
},
{
"id": "node2",
"type": "Chroma",
"position": { "x": 400, "y": 100 },
"data": {}
}
],
"edges": [
{
"id": "edge1",
"source": "node1",
"target": "node2"
}
]
}

trial4Json = {
    "nodes": [
        {"id": "TextInput", "type": "OpenAIEmbeddings", "position": {"x": 0, "y": 0}, "data": {}},
        {"id": "TextOutput", "type": "TextOutput", "position": {"x": 100, "y": 0}, "data": {}}
    ],
    "edges": [
        {
            "id": "edge-1",
            "source": "TextInput",
            "target": "TextOutput",
            "type": "default",
            # Use encodeURIComponent instead of œ replacement
            "sourceHandle": "%7B%22dataType%22%3A%22OpenAIEmbeddings%22%2C%22id%22%3A%22TextInput%22%2C%22name%22%3A%22text%22%2C%22output_types%22%3A%5B%22str%22%5D%7D",
            "targetHandle": "%7B%22fieldName%22%3A%22input_value%22%2C%22id%22%3A%22TextOutput%22%2C%22inputTypes%22%3A%5B%22str%22%5D%2C%22type%22%3A%22str%22%7D",
            "data": {
                "sourceHandle": {
                    "dataType": "OpenAIEmbeddings",
                    "id": "TextInput",
                    "name": "text",
                    "output_types": ["str"]
                },
                "targetHandle": {
                    "fieldName": "input_value",
                    "id": "TextOutput",
                    "inputTypes": ["str"],
                    "type": "str"
                }
            }
        }
    ]
}

# Example flow data with nodes and edges
trial3Json = {
    "nodes": [
        {"id": "TextInput", "type": "OpenAIEmbeddings", "position": {"x": 0, "y": 0}, "data": {}},
        {"id": "TextOutput", "type": "TextOutput", "position": {"x": 100, "y": 0}, "data": {}}
    ],
    "edges": [
        {
            "id": "edge-1",
            "source": "TextInput",
            "target": "TextOutput",
            "type": "default",
            "data": {}
        }
    ]
}

import json
from urllib.parse import quote

import json
from urllib.parse import quote

def generate_edge_handles(
    source_node_id, 
    source_node_type, 
    target_node_id, 
    output_name="text",
    output_types=["Message"],
    target_field_name="input_value",
    target_field_type="str",
    input_types=None
):
    """
    Generate properly encoded edge handles for React Flow edge connections.
    
    Args:
        source_node_id: ID of the source node
        source_node_type: Type of the source node
        target_node_id: ID of the target node
        output_name: Name of the output port (default: "text")
        output_types: Types that this output can produce (default: ["Message"])
        target_field_name: Name of the input field on target node (default: "input_value")
        target_field_type: Type of the target field (default: "str")
        input_types: Types that the target accepts (default: same as output_types)
        
    Returns:
        Dict containing sourceHandle, targetHandle and data values
    """
    if input_types is None:
        input_types = output_types
    
    # Create source handle object with explicit structure matching frontend expectations
    source_handle = {
        "dataType": source_node_type,
        "id": source_node_id,
        "name": output_name,
        "output_types": output_types
    }
    
    # Create target handle object with explicit structure matching frontend expectations
    target_handle = {
        "fieldName": target_field_name,
        "id": target_node_id,
        "inputTypes": input_types,
        "type": target_field_type
    }
    
    # Properly sort keys to match frontend's exact JSON format
    def custom_json_dumps(obj):
        if isinstance(obj, dict):
            # Sort keys to ensure consistent output
            return "{" + ",".join(f'"{k}":{custom_json_dumps(v)}' for k, v in sorted(obj.items())) + "}"
        elif isinstance(obj, list):
            return "[" + ",".join(custom_json_dumps(item) for item in obj) + "]"
        elif obj is None:
            return "null"
        else:
            return json.dumps(obj)
    
    # URL encode the JSON strings
    source_handle_str = quote(custom_json_dumps(source_handle))
    target_handle_str = quote(custom_json_dumps(target_handle))
    
    # Create edge ID from source and target info
    edge_id = f"reactflow__edge-{source_node_id}{source_handle_str}-{target_node_id}{target_handle_str}"
    
    return {
        "id": edge_id,
        "source": source_node_id,
        "target": target_node_id,
        "sourceHandle": source_handle_str,
        "targetHandle": target_handle_str,
        "type": "default",
        "data": {
            "sourceHandle": source_handle,
            "targetHandle": target_handle
        }
    }

def generate_flow_with_error_handling(input_json, use_case=None):
    logger.info(f"Starting flow generation with JSON: {json.dumps(input_json, indent=2)}")
    
    try:
        # Validate nodes
        if not input_json.get("nodes"):
            try:
                input_json = input_json["flow_json"]
                if not input_json.get("nodes"):
                    raise ValueError("No nodes provided")
            except:
                pass
            raise ValueError("No nodes provided")
        
        for node in input_json["nodes"]:
            if not isinstance(node, dict) or "id" not in node:
                raise TypeError(f"Invalid node structure: {node}")
        
        logger.info("Nodes validated successfully")
        
        # Validate edges
        if "edges" in input_json and input_json["edges"]:
            logger.info("Validating edges")
            
            for i, edge in enumerate(input_json["edges"]):
                logger.info(f"Validating edge {i+1}/{len(input_json['edges'])}: {edge}")
                
                if "source" not in edge or "target" not in edge:
                    raise ValueError(f"Edge {i+1} is missing 'source' or 'target' field")
                
                # Check if source and target exist in nodes
                source = edge["source"]
                target = edge["target"]
                
                node_ids = [node["id"] for node in input_json["nodes"]]
                if source not in node_ids or target not in node_ids:
                    raise ValueError(f"Source or target node not found in nodes")
                
            logger.info("Edges validated successfully")
        
        # If we made it here, apply the use case if present
        if use_case:
            return generate_flow_from_use_case(input_json, use_case)
        
        return input_json
    
    except Exception as error:
        logger.error(f"Flow generation failed with error: {str(error)}")
        logger.error(traceback.format_exc())
        
        return {
            "error": True,
            "message": str(error),
            "stack": traceback.format_exc()
        }

def generate_flow_from_use_case(flow_json, use_case):
    logger.info(f"Generating flow for use case: {use_case}")
    
    modified_flow = json.loads(json.dumps(flow_json))
    
    if "translation" in use_case.lower():
        logger.info("Detected translation use case")
        if "OpenAI" not in [node["id"] for node in modified_flow["nodes"]]:
            modified_flow["nodes"].append({"id": "OpenAI", "type": "OpenAI", "position": {"x": 200, "y": 0}, "data": {}})
        
        modified_flow["edges"].append({
            "id": "edge-2",
            "source": "TextInput",
            "target": "OpenAI",
            "type": "default",
            "data": {}
        })
    
    elif "summarization" in use_case.lower():
        logger.info("Detected summarization use case")
        if "OpenAI" not in [node["id"] for node in modified_flow["nodes"]]:
            modified_flow["nodes"].append({"id": "OpenAI", "type": "OpenAI", "position": {"x": 200, "y": 0}, "data": {}})
        
        modified_flow["edges"].append({
            "id": "edge-2",
            "source": "TextInput",
            "target": "OpenAI",
            "type": "default",
            "data": {}
        })
    else:
        logger.info(f"Using default modification for use case: {use_case}")
        modified_flow["useCase"] = use_case
    
    return modified_flow


nodes = [
    {"id": "TextInput", "type": "TextInput", "position": {"x": 0, "y": 0}, "data": {}},
    {"id": "TextOutput", "type": "TextOutput", "position": {"x": 100, "y": 0}, "data": {}}
]

# Create edge with proper handles
# The function now returns a complete edge object
edge = generate_edge_handles(
    source_node_id="TextInput", 
    source_node_type="TextInput", 
    target_node_id="TextOutput",
    output_name="text",          # Output port name (defaults to "text")
    output_types=["Message"],    # Output types this node produces
    target_field_name="input_value",  # Input field name on target
    target_field_type="str",     # Field type
    input_types=["Message"]      # Types the target accepts
)

# Add custom id if needed (optional, function already generates an id)
edge["id"] = "edge-1"  # Override the auto-generated ID if desired

# Final response with the single edge
trial4Json = {
    "nodes": nodes,
    "edges": [edge]
}

@app.route('/api/flows', methods=['GET'])
def return_json():
    try:
        use_case = request.args.get('use_case')
        # flow = generate_flow_with_error_handling(trial8Json, use_case)
        flow = trialAPIJson
        return jsonify(flow)
        
    except Exception as e:
        logger.error(f"Error in /api/flows endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            "error": True,
            "message": str(e),
            "stack": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=8000)