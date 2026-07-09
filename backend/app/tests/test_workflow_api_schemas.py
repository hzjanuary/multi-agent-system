"""Workflow API schema and error mapping tests."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.api.v1.workflow_errors import (
    map_workflow_exception,
    raise_workflow_http_exception,
    workflow_error_detail,
    workflow_http_exception,
)
from app.models.enums import WorkflowEventStatus, WorkflowStatus
from app.schemas.workflows_api import (
    WorkflowCreateRequest,
    WorkflowEventListResponse,
    WorkflowEventResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowStateUpdateRequest,
    WorkflowTransitionRequest,
)
from app.workflows.exceptions import (
    InvalidWorkflowTransitionError,
    WorkflowEventNotFoundError,
    WorkflowNotFoundError,
    WorkflowStateMismatchError,
)
from app.workflows.schemas import WorkflowEventRead, WorkflowState, WorkflowType


def test_workflow_create_request_reuses_workflow_state_create_shape() -> None:
    request = WorkflowCreateRequest.model_validate(
        {
            "workflow_type": WorkflowType.PROCUREMENT_QUOTATION,
            "domain": "general",
            "request": {"raw_text": "Need office supplies"},
        },
    )

    assert request.workflow_type is WorkflowType.PROCUREMENT_QUOTATION
    assert request.domain == "general"
    assert request.request == {"raw_text": "Need office supplies"}


def test_workflow_transition_request_validates_status_and_reason() -> None:
    request = WorkflowTransitionRequest.model_validate(
        {
            "to_status": WorkflowStatus.PLANNING,
            "reason": "Begin planning",
        },
    )

    assert request.to_status is WorkflowStatus.PLANNING
    assert request.reason == "Begin planning"


def test_workflow_transition_request_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        WorkflowTransitionRequest.model_validate({"to_status": "NOT_A_STATUS"})


def test_workflow_list_response_validates_minimal_pagination() -> None:
    workflow = _workflow_state()

    response = WorkflowListResponse.model_validate(
        {
            "workflows": [workflow],
            "count": 1,
            "limit": 25,
            "offset": 0,
            "status": WorkflowStatus.CREATED,
        },
    )

    assert response.workflows == [workflow]
    assert response.count == 1
    assert response.limit == 25
    assert response.offset == 0
    assert response.status is WorkflowStatus.CREATED


def test_workflow_list_response_rejects_invalid_limit() -> None:
    with pytest.raises(ValidationError):
        WorkflowListResponse.model_validate(
            {
                "workflows": [],
                "count": 0,
                "limit": 0,
                "offset": 0,
            },
        )


def test_workflow_response_and_state_update_request_validate_state() -> None:
    workflow = _workflow_state()

    response = WorkflowResponse.model_validate({"workflow": workflow})
    update_request = WorkflowStateUpdateRequest.model_validate(
        {
            "state": workflow,
            "reason": "metadata correction",
        },
    )

    assert response.workflow == workflow
    assert update_request.state == workflow
    assert update_request.reason == "metadata correction"


def test_workflow_event_response_schemas_validate_events() -> None:
    event = _workflow_event()

    response = WorkflowEventResponse.model_validate({"event": event})
    list_response = WorkflowEventListResponse.model_validate(
        {
            "events": [event],
            "count": 1,
            "limit": 100,
            "offset": 0,
        },
    )

    assert response.event == event
    assert list_response.events == [event]
    assert list_response.count == 1


def test_workflow_not_found_maps_to_404() -> None:
    mapping = map_workflow_exception(WorkflowNotFoundError("Workflow missing"))

    assert mapping is not None
    assert mapping.status_code == status.HTTP_404_NOT_FOUND
    assert mapping.detail.code == "workflow_not_found"
    assert mapping.detail.message == "Workflow missing"


def test_workflow_event_not_found_maps_to_404() -> None:
    mapping = map_workflow_exception(
        WorkflowEventNotFoundError("Workflow event missing"),
    )

    assert mapping is not None
    assert mapping.status_code == status.HTTP_404_NOT_FOUND
    assert mapping.detail.code == "workflow_event_not_found"


def test_invalid_transition_maps_to_409_with_safe_details() -> None:
    error = InvalidWorkflowTransitionError(
        from_status=WorkflowStatus.CREATED,
        to_status=WorkflowStatus.COMPLETED,
        allowed_statuses={WorkflowStatus.PLANNING, WorkflowStatus.CANCELLED},
    )

    mapping = map_workflow_exception(error)

    assert mapping is not None
    assert mapping.status_code == status.HTTP_409_CONFLICT
    assert mapping.detail.code == "invalid_workflow_transition"
    assert mapping.detail.details == {
        "from_status": "CREATED",
        "to_status": "COMPLETED",
        "allowed_statuses": ["CANCELLED", "PLANNING"],
    }


def test_workflow_state_mismatch_maps_to_400() -> None:
    mapping = map_workflow_exception(WorkflowStateMismatchError("State mismatch"))

    assert mapping is not None
    assert mapping.status_code == status.HTTP_400_BAD_REQUEST
    assert mapping.detail.code == "workflow_state_mismatch"


def test_workflow_http_exception_uses_json_compatible_detail() -> None:
    error = WorkflowNotFoundError("Workflow missing")

    http_exception = workflow_http_exception(error)
    detail = cast(dict[str, Any], http_exception.detail)

    assert http_exception.status_code == status.HTTP_404_NOT_FOUND
    assert detail == {
        "code": "workflow_not_found",
        "message": "Workflow missing",
        "details": {},
    }


def test_raise_workflow_http_exception_reraises_unknown_errors() -> None:
    error = RuntimeError("unexpected")

    with pytest.raises(RuntimeError, match="unexpected"):
        raise_workflow_http_exception(error)


def test_raise_workflow_http_exception_raises_known_http_exception() -> None:
    with pytest.raises(HTTPException) as exc_info:
        raise_workflow_http_exception(WorkflowStateMismatchError("State mismatch"))

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST


def test_workflow_error_detail_builds_bounded_shape() -> None:
    assert workflow_error_detail(
        code="workflow_state_mismatch",
        message="State mismatch",
        details={"field": "status"},
    ) == {
        "code": "workflow_state_mismatch",
        "message": "State mismatch",
        "details": {"field": "status"},
    }


def _workflow_state() -> WorkflowState:
    return WorkflowState.model_validate(
        {
            "workflow_id": str(uuid4()),
            "workflow_type": WorkflowType.PROCUREMENT_QUOTATION,
            "domain": "general",
            "status": WorkflowStatus.CREATED,
            "request": {"raw_text": "Need office supplies"},
            "created_at": datetime.now(UTC),
        },
    )


def _workflow_event() -> WorkflowEventRead:
    workflow_id = uuid4()
    return WorkflowEventRead.model_validate(
        {
            "event_id": uuid4(),
            "workflow_id": workflow_id,
            "event_type": "workflow.created",
            "actor_type": "user",
            "actor_id": uuid4(),
            "agent_name": None,
            "status": WorkflowEventStatus.COMPLETED,
            "message": "Workflow created",
            "payload": {"workflow_id": str(workflow_id)},
            "created_at": datetime.now(UTC),
        },
    )
