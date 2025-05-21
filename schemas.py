"""
app/schemas.py

Pydantic models defining the structured data exchanged between agents:
- RequirementContext: parsed user intent
- WorkflowPlan: abstract steps of the design
- ComponentSpec & ComponentSelection: mapping steps to Langflow components
- OptimizedPlan: post-optimization details (including clarification flag)
- ClarificationAnswer: user responses to clarification questions
- AssemblyResult: final Langflow JSON output
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class RequirementContext(BaseModel):
    use_case: str = Field(..., description="High-level goal extracted from the user prompt")
    key_tasks: List[str] = Field(..., description="List of discrete tasks the system must perform")
    tech_stack: List[str] = Field(..., description="User-specified tools, models, and platforms")
    constraints: List[str] = Field(..., description="Constraints like cost, privacy, performance, etc.")
    ambiguities: List[str] = Field(..., description="List of unclear or missing details requiring clarification")


class WorkflowPlan(BaseModel):
    steps: List[str] = Field(..., description="Sequential abstract steps defining the AI workflow")


class ComponentSpec(BaseModel):
    step: str = Field(..., description="Abstract workflow step being implemented")
    component_name: str = Field(..., description="Name of the Langflow component selected for this step")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration parameters for the component (e.g., model, API keys placeholder)"
    )


class ComponentSelection(BaseModel):
    components: List[ComponentSpec] = Field(
        ..., description="Concrete component specs for each workflow step"
    )


class OptimizedPlan(BaseModel):
    components: List[ComponentSpec] = Field(
        ..., description="Components after applying cost/performance optimization"
    )
    needs_clarification: bool = Field(
        False,
        description="Flag indicating whether user clarification is needed"
    )
    ambiguities: List[str] = Field(
        default_factory=list,
        description="Ambiguities carried forward if clarification is required"
    )


class ClarificationAnswer(BaseModel):
    clarifications: Dict[str, str] = Field(
        ..., description="Mapping from ambiguity questions to user answers"
    )


class AssemblyResult(BaseModel):
    flow_json: Dict[str, Any] = Field(
        ..., description="Final Langflow JSON representation of the designed workflow"
    )
