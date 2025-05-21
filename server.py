from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

trial3Json = {
  "nodes": [
        {
            "id": "OpenAIModel-whU7n",
            "type": "genericNode",
            "position": {
                "x": 0,
                "y": 0
            },
            "data": {
                "node": {
                    "template": {
                        "_type": "Component",
                        "api_key": {
                            "load_from_db": True,
                            "required": True,
                            "placeholder": "",
                            "show": True,
                            "name": "api_key",
                            "value": "OPENAI_API_KEY",
                            "display_name": "OpenAI API Key",
                            "advanced": False,
                            "input_types": [],
                            "dynamic": False,
                            "info": "The OpenAI API Key to use for the OpenAI model.",
                            "title_case": False,
                            "password": True,
                            "type": "str",
                            "_input_type": "SecretStrInput"
                        },
                        "code": {
                            "type": "code",
                            "required": True,
                            "placeholder": "",
                            "list": False,
                            "show": True,
                            "multiline": True,
                            "value": "from typing import Any\n\nfrom langchain_openai import ChatOpenAI\nfrom pydantic.v1 import SecretStr\n\nfrom langflow.base.models.model import LCModelComponent\nfrom langflow.base.models.openai_constants import (\n    OPENAI_MODEL_NAMES,\n    OPENAI_REASONING_MODEL_NAMES,\n)\nfrom langflow.field_typing import LanguageModel\nfrom langflow.field_typing.range_spec import RangeSpec\nfrom langflow.inputs import BoolInput, DictInput, DropdownInput, IntInput, SecretStrInput, SliderInput, StrInput\nfrom langflow.logging import logger\n\n\nclass OpenAIModelComponent(LCModelComponent):\n    display_name = \"OpenAI\"\n    description = \"Generates text using OpenAI LLMs.\"\n    icon = \"OpenAI\"\n    name = \"OpenAIModel\"\n\n    inputs = [\n        *LCModelComponent._base_inputs,\n        IntInput(\n            name=\"max_tokens\",\n            display_name=\"Max Tokens\",\n            advanced=True,\n            info=\"The maximum number of tokens to generate. Set to 0 for unlimited tokens.\",\n            range_spec=RangeSpec(min=0, max=128000),\n        ),\n        DictInput(\n            name=\"model_kwargs\",\n            display_name=\"Model Kwargs\",\n            advanced=True,\n            info=\"Additional keyword arguments to pass to the model.\",\n        ),\n        BoolInput(\n            name=\"json_mode\",\n            display_name=\"JSON Mode\",\n            advanced=True,\n            info=\"If True, it will output JSON regardless of passing a schema.\",\n        ),\n        DropdownInput(\n            name=\"model_name\",\n            display_name=\"Model Name\",\n            advanced=False,\n            options=OPENAI_MODEL_NAMES + OPENAI_REASONING_MODEL_NAMES,\n            value=OPENAI_MODEL_NAMES[1],\n            combobox=True,\n            real_time_refresh=True,\n        ),\n        StrInput(\n            name=\"openai_api_base\",\n            display_name=\"OpenAI API Base\",\n            advanced=True,\n            info=\"The base URL of the OpenAI API. \"\n            \"Defaults to https://api.openai.com/v1. \"\n            \"You can change this to use other APIs like JinaChat, LocalAI and Prem.\",\n        ),\n        SecretStrInput(\n            name=\"api_key\",\n            display_name=\"OpenAI API Key\",\n            info=\"The OpenAI API Key to use for the OpenAI model.\",\n            advanced=False,\n            value=\"OPENAI_API_KEY\",\n            required=True,\n        ),\n        SliderInput(\n            name=\"temperature\",\n            display_name=\"Temperature\",\n            value=0.1,\n            range_spec=RangeSpec(min=0, max=1, step=0.01),\n            show=True,\n        ),\n        IntInput(\n            name=\"seed\",\n            display_name=\"Seed\",\n            info=\"The seed controls the reproducibility of the job.\",\n            advanced=True,\n            value=1,\n        ),\n        IntInput(\n            name=\"max_retries\",\n            display_name=\"Max Retries\",\n            info=\"The maximum number of retries to make when generating.\",\n            advanced=True,\n            value=5,\n        ),\n        IntInput(\n            name=\"timeout\",\n            display_name=\"Timeout\",\n            info=\"The timeout for requests to OpenAI completion API.\",\n            advanced=True,\n            value=700,\n        ),\n    ]\n\n    def build_model(self) -> LanguageModel:  # type: ignore[type-var]\n        parameters = {\n            \"api_key\": SecretStr(self.api_key).get_secret_value() if self.api_key else None,\n            \"model_name\": self.model_name,\n            \"max_tokens\": self.max_tokens or None,\n            \"model_kwargs\": self.model_kwargs or {},\n            \"base_url\": self.openai_api_base or \"https://api.openai.com/v1\",\n            \"seed\": self.seed,\n            \"max_retries\": self.max_retries,\n            \"timeout\": self.timeout,\n            \"temperature\": self.temperature if self.temperature is not None else 0.1,\n        }\n\n        logger.info(f\"Model name: {self.model_name}\")\n        if self.model_name in OPENAI_REASONING_MODEL_NAMES:\n            logger.info(\"Getting reasoning model parameters\")\n            parameters.pop(\"temperature\")\n            parameters.pop(\"seed\")\n        output = ChatOpenAI(**parameters)\n        if self.json_mode:\n            output = output.bind(response_format={\"type\": \"json_object\"})\n\n        return output\n\n    def _get_exception_message(self, e: Exception):\n        \"\"\"Get a message from an OpenAI exception.\n\n        Args:\n            e (Exception): The exception to get the message from.\n\n        Returns:\n            str: The message from the exception.\n        \"\"\"\n        try:\n            from openai import BadRequestError\n        except ImportError:\n            return None\n        if isinstance(e, BadRequestError):\n            message = e.body.get(\"message\")\n            if message:\n                return message\n        return None\n\n    def update_build_config(self, build_config: dict, field_value: Any, field_name: str | None = None) -> dict:\n        if field_name in {\"base_url\", \"model_name\", \"api_key\"} and field_value in OPENAI_REASONING_MODEL_NAMES:\n            build_config[\"temperature\"][\"show\"] = False\n            build_config[\"seed\"][\"show\"] = False\n        if field_name in {\"base_url\", \"model_name\", \"api_key\"} and field_value in OPENAI_MODEL_NAMES:\n            build_config[\"temperature\"][\"show\"] = True\n            build_config[\"seed\"][\"show\"] = True\n        return build_config\n",
                            "fileTypes": [],
                            "file_path": "",
                            "password": False,
                            "name": "code",
                            "advanced": True,
                            "dynamic": True,
                            "info": "",
                            "load_from_db": False,
                            "title_case": False
                        },
                        "input_value": {
                            "trace_as_input": True,
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "load_from_db": False,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "input_value",
                            "value": "",
                            "display_name": "Input",
                            "advanced": False,
                            "input_types": [
                                "Message"
                            ],
                            "dynamic": False,
                            "info": "",
                            "title_case": False,
                            "type": "str",
                            "_input_type": "MessageInput"
                        },
                        "json_mode": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "json_mode",
                            "value": False,
                            "display_name": "JSON Mode",
                            "advanced": True,
                            "dynamic": False,
                            "info": "If True, it will output JSON regardless of passing a schema.",
                            "title_case": False,
                            "type": "bool",
                            "_input_type": "BoolInput"
                        },
                        "max_retries": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "max_retries",
                            "value": 5,
                            "display_name": "Max Retries",
                            "advanced": True,
                            "dynamic": False,
                            "info": "The maximum number of retries to make when generating.",
                            "title_case": False,
                            "type": "int",
                            "_input_type": "IntInput"
                        },
                        "max_tokens": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "range_spec": {
                                "step_type": "float",
                                "min": 0,
                                "max": 128000,
                                "step": 0.1
                            },
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "max_tokens",
                            "value": "",
                            "display_name": "Max Tokens",
                            "advanced": True,
                            "dynamic": False,
                            "info": "The maximum number of tokens to generate. Set to 0 for unlimited tokens.",
                            "title_case": False,
                            "type": "int",
                            "_input_type": "IntInput"
                        },
                        "model_kwargs": {
                            "tool_mode": False,
                            "trace_as_input": True,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "model_kwargs",
                            "value": {},
                            "display_name": "Model Kwargs",
                            "advanced": True,
                            "dynamic": False,
                            "info": "Additional keyword arguments to pass to the model.",
                            "title_case": False,
                            "type": "dict",
                            "_input_type": "DictInput"
                        },
                        "model_name": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "options": [
                                "gpt-4o-mini",
                                "gpt-4o",
                                "gpt-4.1",
                                "gpt-4.1-mini",
                                "gpt-4.1-nano",
                                "gpt-4.5-preview",
                                "gpt-4-turbo",
                                "gpt-4-turbo-preview",
                                "gpt-4",
                                "gpt-3.5-turbo",
                                "o1"
                            ],
                            "options_metadata": [],
                            "combobox": True,
                            "dialog_inputs": {},
                            "toggle": False,
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "model_name",
                            "value": "gpt-4o",
                            "display_name": "Model Name",
                            "advanced": False,
                            "dynamic": False,
                            "info": "",
                            "real_time_refresh": True,
                            "title_case": False,
                            "type": "str",
                            "_input_type": "DropdownInput"
                        },
                        "openai_api_base": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "load_from_db": False,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "openai_api_base",
                            "value": "",
                            "display_name": "OpenAI API Base",
                            "advanced": True,
                            "dynamic": False,
                            "info": "The base URL of the OpenAI API. Defaults to https://api.openai.com/v1. You can change this to use other APIs like JinaChat, LocalAI and Prem.",
                            "title_case": False,
                            "type": "str",
                            "_input_type": "StrInput"
                        },
                        "seed": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "seed",
                            "value": 1,
                            "display_name": "Seed",
                            "advanced": True,
                            "dynamic": False,
                            "info": "The seed controls the reproducibility of the job.",
                            "title_case": False,
                            "type": "int",
                            "_input_type": "IntInput"
                        },
                        "stream": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "stream",
                            "value": False,
                            "display_name": "Stream",
                            "advanced": True,
                            "dynamic": False,
                            "info": "Stream the response from the model. Streaming works only in Chat.",
                            "title_case": False,
                            "type": "bool",
                            "_input_type": "BoolInput"
                        },
                        "system_message": {
                            "tool_mode": False,
                            "trace_as_input": True,
                            "multiline": True,
                            "trace_as_metadata": True,
                            "load_from_db": False,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "system_message",
                            "value": "",
                            "display_name": "System Message",
                            "advanced": False,
                            "input_types": [
                                "Message"
                            ],
                            "dynamic": False,
                            "info": "System message to pass to the model.",
                            "title_case": False,
                            "copy_field": False,
                            "type": "str",
                            "_input_type": "MultilineInput"
                        },
                        "temperature": {
                            "tool_mode": False,
                            "min_label": "",
                            "max_label": "",
                            "min_label_icon": "",
                            "max_label_icon": "",
                            "slider_buttons": False,
                            "slider_buttons_options": [],
                            "slider_input": False,
                            "range_spec": {
                                "step_type": "float",
                                "min": 0,
                                "max": 1,
                                "step": 0.01
                            },
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "temperature",
                            "value": 0.1,
                            "display_name": "Temperature",
                            "advanced": False,
                            "dynamic": False,
                            "info": "",
                            "title_case": False,
                            "type": "slider",
                            "_input_type": "SliderInput"
                        },
                        "timeout": {
                            "tool_mode": False,
                            "trace_as_metadata": True,
                            "list": False,
                            "list_add_label": "Add More",
                            "required": False,
                            "placeholder": "",
                            "show": True,
                            "name": "timeout",
                            "value": 700,
                            "display_name": "Timeout",
                            "advanced": True,
                            "dynamic": False,
                            "info": "The timeout for requests to OpenAI completion API.",
                            "title_case": False,
                            "type": "int",
                            "_input_type": "IntInput"
                        }
                    },
                    "description": "Generates text using OpenAI LLMs.",
                    "icon": "OpenAI",
                    "base_classes": [
                        "LanguageModel",
                        "Message"
                    ],
                    "display_name": "OpenAI",
                    "documentation": "",
                    "minimized": False,
                    "custom_fields": {},
                    "output_types": [],
                    "pinned": False,
                    "conditional_paths": [],
                    "frozen": False,
                    "outputs": [
                        {
                            "types": [
                                "Message"
                            ],
                            "selected": "Message",
                            "name": "text_output",
                            "display_name": "Message",
                            "method": "text_response",
                            "value": "__UNDEFINED__",
                            "cache": True,
                            "required_inputs": [],
                            "allows_loop": False,
                            "tool_mode": True
                        },
                        {
                            "types": [
                                "LanguageModel"
                            ],
                            "selected": "LanguageModel",
                            "name": "model_output",
                            "display_name": "Language Model",
                            "method": "build_model",
                            "value": "__UNDEFINED__",
                            "cache": True,
                            "required_inputs": [
                                "api_key"
                            ],
                            "allows_loop": False,
                            "tool_mode": True
                        }
                    ],
                    "field_order": [
                        "input_value",
                        "system_message",
                        "stream",
                        "max_tokens",
                        "model_kwargs",
                        "json_mode",
                        "model_name",
                        "openai_api_base",
                        "api_key",
                        "temperature",
                        "seed",
                        "max_retries",
                        "timeout"
                    ],
                    "beta": False,
                    "legacy": False,
                    "edited": False,
                    "metadata": {},
                    "tool_mode": False,
                    "category": "models",
                    "key": "OpenAIModel",
                    "score": 0.001
                },
                "showNode": True,
                "type": "OpenAIModel",
                "id": "OpenAIModel-whU7n"
            }
        },
    {
      "id": "OpenAIModel-abc123",
      "type": "OpenAIModel",
      "position": { "x": 500, "y": 300 },
      "data": {
        "type": "OpenAIModelComponent",
        "id": "OpenAIModel-abc123",
        "node": {
          "display_name": "OpenAI",
          "description": "Generates text using OpenAI LLMs.",
          "base_classes": ["LanguageModel"],
          "template": {
            "api_key": {
              "type": "str",
              "required": True,
              "display_name": "OpenAI API Key",
              "value": ""
            },
            "model_name": {
              "type": "str",
              "required": True,
              "display_name": "Model Name",
              "value": "gpt-4o"
            },
            "temperature": {
              "type": "float",
              "required": False,
              "display_name": "Temperature",
              "value": 0.1
            },
            "input_value": {
              "type": "str",
              "display_name": "Input",
              "value": ""
            },
            "system_message": {
              "type": "str",
              "display_name": "System Message",
              "value": ""
            }
          }
        }
      }
    }
  ],
  "edges": [
    {
      "id": "edge-ChatInput-xyz789-to-OpenAIModel-abc123",
      "source": "ChatInput-xyz789",
      "target": "OpenAIModel-abc123",
      "sourceHandle": "{œdataTypeœ:œChatInputComponentœ,œidœ:œChatInput-xyz789œ,œnameœ:œmessageœ,œoutput_typesœ:[œMessageœ]}",
      "targetHandle": "{œfieldNameœ:œinput_valueœ,œidœ:œOpenAIModel-abc123œ,œinputTypesœ:[œMessageœ],œtypeœ:œstrœ}",
      "data": {
        "sourceHandle": {
          "dataType": "ChatInputComponent",
          "id": "ChatInput-xyz789",
          "name": "message", 
          "output_types": ["Message"]
        },
        "targetHandle": {
          "fieldName": "input_value",
          "id": "OpenAIModel-abc123",
          "inputTypes": ["Message"],
          "type": "str"
        }
      }
    }
  ]
}

trial2Json = {
  "nodes": [
      {
      "id": "node-1",
      "type": "ChatInput", # This can be either "ChatInput" or "genericNode" with type: "ChatInput" in data
      "position": { "x": 100, "y": 100 },
      "data": {
        "label": "Chat Input Node",
        "type": "ChatInput",
        "id": "node-1",
        "node": {
          "template": {
            "input_text": {
              "type": "string",
              "value": "Hello, how can I help you?"
            },
            "input_value": {  # This is the critical field that creates the text input
              "type": "string",
              "value": "",
              "display_name": "Text",
              "multiline": True
            },
            "should_store_message": {
              "type": "boolean",
              "value": True
            },
            "sender": {
              "type": "string",
              "value": "User"
            }
          },
          "description": "Get chat inputs from the Playground.",
          "icon": "MessagesSquare",
          "base_classes": ["Message"],
          "display_name": "Chat Input",
          "outputs": [
            {
              "types": ["Message"],
              "selected": "Message",
              "name": "message",
              "display_name": "Message",
              "method": "message_response",
              "value": "__UNDEFINED__",
              "cache": True,
              "allows_loop": False,
              "tool_mode": True
            }
          ],
          "field_order": ["input_value", "should_store_message", "sender"]
        }
      }
    },
    {
      "id": "node-2",
      "type": "genericNode",
      "position": { "x": 400, "y": 100 },
      "data": {
        "label": "Chat Output Node",
        "type": "ChatOutput",
        "id": "node-2",
        "node": {
          "template": {
            "input_value": {
              "type": "Message",
              "value": "",
              "required": True,
              "display_name": "Input"
            },
            "output_text": {
              "type": "string",
              "value": "Sure, let me assist you with that."
            }
          },
          "description": "Display a chat message in the Playground.",
          "icon": "MessagesSquare",
          "base_classes": ["Message"],
          "display_name": "Chat Output",
          "field_order": ["input_value", "should_store_message"]
        }
      }
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "node-1",
      "target": "node-2",
      "type": "smoothstep"
    }
  ]
}

trial1Json = {
    "nodes": [
    {
      "id": "node-1",
      "type": "ChatInput",
      "data": {
        "label": "Chat Input Node",
        "node": {
          "template": {
            "input_text": {
              "type": "string",
              "value": "Hello, how can I help you?"
            }
          }
        }
      },
      "position": { "x": 100, "y": 100 }
    }
    ]
}

@app.route('/api/flows', methods=['GET'])
def return_json():
    return jsonify(trial3Json)

if __name__ == '__main__':
    app.run(debug=True, port=8000)