"""LLM-assisted runtime stage adapter behind the runtime feature flag."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from typing import Any, Protocol

from pydantic import BaseModel

from app.llm.contracts import LLMChatRequest, LLMChatResponse, LLMUsage
from app.llm.output_parser import parse_structured_output
from app.llm.prompts import (
    build_approval_package_request,
    build_finance_risk_analysis_request,
    build_legal_compliance_analysis_request,
    build_requirement_extraction_request,
    build_supplier_pricing_analysis_request,
)
from app.llm.structured_outputs import (
    ApprovalPackageOutput,
    FinanceRiskAnalysisOutput,
    LegalComplianceAnalysisOutput,
    RequirementExtractionOutput,
    SupplierPricingAnalysisOutput,
)
from app.runtime.nodes import run_quotation_node
from app.runtime.schemas import RuntimeStage, RuntimeWorkflowState


class LLMCompletionService(Protocol):
    """Narrow LLM service protocol required by runtime integration."""

    def complete_json(
        self,
        request: LLMChatRequest,
    ) -> Awaitable[LLMChatResponse]:
        """Return a provider-independent JSON-mode LLM response."""
        ...


type PromptBuilder = Callable[..., LLMChatRequest]
type StructuredOutputModel = type[BaseModel]

_STAGE_PROMPTS: Mapping[
    RuntimeStage,
    tuple[PromptBuilder, StructuredOutputModel],
] = {
    RuntimeStage.PLANNER: (
        build_requirement_extraction_request,
        RequirementExtractionOutput,
    ),
    RuntimeStage.RETRIEVAL: (
        build_supplier_pricing_analysis_request,
        SupplierPricingAnalysisOutput,
    ),
    RuntimeStage.COMPLIANCE: (
        build_legal_compliance_analysis_request,
        LegalComplianceAnalysisOutput,
    ),
    RuntimeStage.VALIDATION: (
        build_finance_risk_analysis_request,
        FinanceRiskAnalysisOutput,
    ),
    RuntimeStage.APPROVAL: (
        build_approval_package_request,
        ApprovalPackageOutput,
    ),
}


class LLMRuntimeAdapter:
    """Run procurement runtime stages through LLM prompts when enabled."""

    def __init__(self, llm_service: LLMCompletionService) -> None:
        self._llm_service = llm_service

    async def run_stage(
        self,
        state: RuntimeWorkflowState,
        stage: RuntimeStage,
    ) -> RuntimeWorkflowState:
        """Run one stage through the LLM pipeline or a bounded deterministic skip."""
        if stage is RuntimeStage.QUOTATION:
            return self._run_quotation_without_llm_arithmetic(state)

        prompt_config = _STAGE_PROMPTS.get(stage)
        if prompt_config is None:
            raise ValueError(f"LLM runtime does not support stage {stage.value}")

        prompt_builder, output_schema = prompt_config
        request = prompt_builder(
            _workflow_prompt_input(state),
            context=_workflow_prompt_context(state, stage),
            request_id=f"{state.workflow_id}:{stage.value}",
        )
        response = await self._llm_service.complete_json(request)
        parsed_output = parse_structured_output(response, output_schema)
        return _complete_llm_stage(
            state,
            stage,
            parsed_output=parsed_output,
            response=response,
        )

    def _run_quotation_without_llm_arithmetic(
        self,
        state: RuntimeWorkflowState,
    ) -> RuntimeWorkflowState:
        updated_state = run_quotation_node(state)
        quotation_output = dict(updated_state.stage_outputs[RuntimeStage.QUOTATION])
        quotation_output.update(
            {
                "llm_runtime_enabled": True,
                "llm_skipped": True,
                "llm_skipped_reason": (
                    "Quotation arithmetic remains deterministic and outside LLM scope."
                ),
            },
        )
        return _replace_stage_output(
            updated_state,
            RuntimeStage.QUOTATION,
            quotation_output,
            extra_runtime_context={"llm_runtime_enabled": True},
        )


def _complete_llm_stage(
    state: RuntimeWorkflowState,
    stage: RuntimeStage,
    *,
    parsed_output: BaseModel,
    response: LLMChatResponse,
) -> RuntimeWorkflowState:
    output = parsed_output.model_dump(mode="json")
    stage_output = {
        "stage": stage.value,
        "status": "completed",
        "summary": str(output.get("summary", "")),
        "placeholder": False,
        "llm_runtime_enabled": True,
        "llm_output_schema": type(parsed_output).__name__,
        "llm_output": output,
        "llm_provider": response.provider.value,
        "llm_model": response.model,
        "llm_request_id": response.request_id,
        "llm_finish_reason": response.finish_reason.value,
    }
    usage = _usage_payload(response.usage)
    if usage:
        stage_output["llm_usage"] = usage

    return _replace_stage_output(
        state,
        stage,
        stage_output,
        extra_runtime_context={"llm_runtime_enabled": True},
    )


def _replace_stage_output(
    state: RuntimeWorkflowState,
    stage: RuntimeStage,
    stage_output: dict[str, Any],
    *,
    extra_runtime_context: dict[str, Any] | None = None,
) -> RuntimeWorkflowState:
    completed_stages = state.completed_stages
    if stage not in completed_stages:
        completed_stages = (*completed_stages, stage)

    stage_outputs = {
        existing_stage: dict(output)
        for existing_stage, output in state.stage_outputs.items()
    }
    stage_outputs[stage] = dict(stage_output)

    outputs = dict(state.outputs)
    raw_output_stage_outputs = outputs.get("stage_outputs")
    output_stage_outputs = (
        {
            str(stage_value): dict(output)
            for stage_value, output in raw_output_stage_outputs.items()
            if isinstance(output, dict)
        }
        if isinstance(raw_output_stage_outputs, dict)
        else {}
    )
    output_stage_outputs[stage.value] = dict(stage_output)
    outputs["stage_outputs"] = output_stage_outputs
    outputs["last_completed_stage"] = stage.value

    runtime_context = dict(state.runtime_context)
    runtime_context["last_completed_stage"] = stage.value
    if extra_runtime_context:
        runtime_context.update(extra_runtime_context)

    return state.model_copy(
        update={
            "current_stage": stage,
            "completed_stages": completed_stages,
            "runtime_context": runtime_context,
            "stage_outputs": stage_outputs,
            "outputs": outputs,
        },
    )


def _workflow_prompt_input(state: RuntimeWorkflowState) -> dict[str, Any]:
    return {
        "workflow_id": state.workflow_id,
        "workflow_type": state.workflow_type.value,
        "domain": state.domain,
        "request": dict(state.request),
        "customer": dict(state.customer),
        "items": [dict(item) for item in state.items],
    }


def _workflow_prompt_context(
    state: RuntimeWorkflowState,
    stage: RuntimeStage,
) -> dict[str, Any]:
    return {
        "stage": stage.value,
        "completed_stages": [completed.value for completed in state.completed_stages],
        "stage_outputs": {
            completed_stage.value: dict(output)
            for completed_stage, output in state.stage_outputs.items()
        },
    }


def _usage_payload(usage: LLMUsage | None) -> dict[str, Any]:
    if usage is None:
        return {}
    return usage.model_dump(mode="json", exclude_none=True)


__all__ = ["LLMCompletionService", "LLMRuntimeAdapter"]
