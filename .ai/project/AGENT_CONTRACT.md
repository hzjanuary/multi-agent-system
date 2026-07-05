# AGENT CONTRACT

## Common Rules

Every Agent must:

- Accept structured input.
- Return structured output.
- Avoid direct database access unless wrapped by a tool/service.
- Log start, success and failure.
- Respect timeout and retry policies.
- Never expose hidden chain-of-thought.

## Planner Agent

Input: WorkflowRequest  
Output: WorkflowPlan  
Responsibility: Determine intent, domain and required tasks.

## Retrieval Agent

Input: RetrievalRequest  
Output: RetrievalResult  
Responsibility: Retrieve contracts, policies, product specs and historical data with citations.

## Calculator Agent

Input: CalculationRequest  
Output: Quotation  
Responsibility: Generate deterministic quote using pricing rules and Python tools.

## Compliance Agent

Input: ComplianceRequest  
Output: ComplianceReport  
Responsibility: Check quotation against contract and policy constraints.

## Validation Agent

Input: ValidationRequest  
Output: ValidationResult  
Responsibility: Validate schemas, calculations and required business fields.

## Email Agent

Input: EmailGenerationRequest  
Output: EmailPreview  
Responsibility: Generate customer-facing email preview after approval only.
