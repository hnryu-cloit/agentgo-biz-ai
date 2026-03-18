from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceRef(BaseModel):
    name: str
    uploaded_at: datetime


class Evidence(BaseModel):
    metric: str
    value: str
    period: str
    source: SourceRef


class VersionTag(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    agent: str
    model_version: str
    prompt_version: str
    postprocess_version: str


class WarningMessage(BaseModel):
    code: str
    message: str


class DataWindow(BaseModel):
    start: date
    end: date


class BaseAnalysisRequest(BaseModel):
    store_id: str
    data_window: DataWindow
    record_count: int = Field(ge=0)
    source_name: str
    uploaded_at: datetime


class SalesFactor(BaseModel):
    factor: str
    impact_score: float
    summary: str


class SalesDiagnosticRequest(BaseAnalysisRequest):
    revenue_delta_pct: float
    customer_delta_pct: float
    avg_ticket_delta_pct: float
    channel_delta_pct: float
    weather_impact_pct: float = 0


class ChurnInsightRequest(BaseAnalysisRequest):
    at_risk_customers: int = Field(ge=0)
    delayed_visit_days: float = Field(ge=0)
    avg_visit_cycle_days: float = Field(gt=0)
    coupon_redemption_rate: float = Field(ge=0, le=1)


class AnomalyExplanationRequest(BaseAnalysisRequest):
    anomaly_type: Literal["payment", "discount", "inventory", "point_leak"]
    anomaly_score: float = Field(ge=0, le=100)
    occurrence_count: int = Field(ge=1)
    revenue_impact: float


class RetentionOfferRequest(BaseModel):
    store_id: str
    segment_name: str
    customer_count: int = Field(ge=1)
    avg_margin_per_customer: float
    churn_risk_level: Literal["low", "medium", "high"]
    coupon_budget: int = Field(ge=0)
    source_name: str
    uploaded_at: datetime


class MenuPricingRequest(BaseModel):
    store_id: str
    menu_id: str
    price: int = Field(ge=0)
    cost: float = Field(ge=0)
    quantity: float = Field(ge=0)
    margin_rate: float = Field(ge=0)
    category: str
    source_name: str
    uploaded_at: datetime


class MenuPricingResponse(BaseModel):
    store_id: str
    menu_id: str
    strategy_type: str
    action: str
    pricing_signal: str
    recommended_price_min: int
    recommended_price_max: int
    summary: str
    actions: list[StrategyAction]
    evidence: list[Evidence]
    warnings: list[WarningMessage]
    version: VersionTag


class StaffingOptimizationRequest(BaseModel):
    store_id: str
    date: date
    hour: int = Field(ge=0, le=23)
    sales: float = Field(ge=0)
    staff_actual: int = Field(ge=0)
    staff_recommended: int = Field(ge=0)
    source_name: str
    uploaded_at: datetime


class StaffingOptimizationResponse(BaseModel):
    store_id: str
    status: str
    gap: int
    opportunity_cost: int
    recommendation: str
    evidence: list[Evidence]
    version: VersionTag


class InventoryOptimizationRequest(BaseModel):
    store_id: str
    month: str
    item_id: str
    system_qty: float = Field(ge=0)
    actual_qty: float = Field(ge=0)
    loss_rate: float = Field(ge=0)
    source_name: str
    uploaded_at: datetime


class InventoryOptimizationResponse(BaseModel):
    store_id: str
    item_id: str
    risk_level: str
    reorder_qty: int
    estimated_loss_amount: int
    recommendation: str
    evidence: list[Evidence]
    version: VersionTag


class TargetCustomer(BaseModel):
    customer_id: str
    consent: bool
    cooldown_days: int = Field(ge=0)
    duplicate: bool = False


class CampaignTargetValidationRequest(BaseModel):
    campaign_id: str
    targets: list[TargetCustomer]


class CampaignTargetExclusion(BaseModel):
    customer_id: str
    reason: str


class CampaignTargetValidationResponse(BaseModel):
    campaign_id: str
    valid_count: int
    excluded_count: int
    exclusions: list[CampaignTargetExclusion]


class CampaignExecutionRequest(BaseModel):
    campaign_id: str
    approved: bool
    valid_target_count: int = Field(ge=0)
    channel: Literal["coupon", "point", "sms"]
    dry_run: bool = True


class CampaignExecutionResponse(BaseModel):
    campaign_id: str
    status: Literal["pending_approval", "scheduled", "executed"]
    retries: int
    message: str


class AnalysisResponse(BaseModel):
    store_id: str
    analysis_type: str
    summary: str
    highlights: list[str]
    evidence: list[Evidence]
    warnings: list[WarningMessage]
    version: VersionTag
    cold_start_mode: bool = False


class StoreIntelligenceRequest(BaseModel):
    store_id: str
    sales_input: SalesDiagnosticRequest
    churn_input: ChurnInsightRequest
    staffing_inputs: list[StaffingOptimizationRequest] = Field(default_factory=list)
    roi_rate: float = 0.0
    avg_order_value: float = 0.0
    recent_visit_count: int = 0


class StoreIntelligenceResponse(BaseModel):
    store_id: str
    summary: str
    priority_actions: list[str]
    sales: AnalysisResponse
    churn: AnalysisResponse
    staffing: list[StaffingOptimizationResponse]
    version: VersionTag


class CampaignBepSimulationRequest(BaseModel):
    store_id: str
    segment_name: str
    channel: Literal["sms", "push", "kakao"]
    offer_type: Literal["discount", "coupon", "free_item"]
    offer_value: float = Field(ge=0)
    target_customers: int = Field(ge=1)
    promo_days: int = Field(ge=1, le=60)
    fixed_cost: float = Field(ge=0)
    menu_name: str
    menu_price: float = Field(ge=0)
    margin_rate: float = Field(ge=0, le=1)
    daily_avg_qty: float = Field(ge=0)
    avg_order_value: float = Field(ge=0)
    recent_visit_count: int = Field(ge=0)
    return_rate: float = Field(ge=0, le=1)
    roi_rate: float = 0.0
    source_name: str
    uploaded_at: datetime


class CampaignBepSimulationResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    store_id: str
    model_name: str
    summary: str
    expected_open_rate: float
    expected_conversion_rate: float
    expected_incremental_orders: int
    expected_incremental_revenue: float
    expected_incremental_profit: float
    break_even_orders: int
    break_even_revenue: float
    break_even_probability: float
    expected_roi: float
    confidence: float
    action_guide: list[str]
    evidence: list[Evidence]
    version: VersionTag


class CampaignUpliftRequest(BaseModel):
    store_id: str
    segment_name: str
    channel: Literal["sms", "push", "kakao"]
    target_customers: int = Field(ge=1)
    discount_rate: float = Field(ge=0, le=1)
    avg_order_value: float = Field(ge=0)
    recent_visit_count: int = Field(ge=0)
    return_rate: float = Field(ge=0, le=1)
    roi_rate: float = 0.0
    source_name: str
    uploaded_at: datetime


class CampaignUpliftResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    store_id: str
    model_name: str
    summary: str
    expected_incremental_orders: int
    expected_incremental_revenue: float
    expected_uplift_rate: float
    expected_redemption_rate: float
    confidence: float
    action_guide: list[str]
    evidence: list[Evidence]
    version: VersionTag


class StrategyAction(BaseModel):
    title: str
    expected_effect: str
    priority: Literal["P0", "P1", "P2"]


class StrategyResponse(BaseModel):
    store_id: str
    strategy_type: str
    summary: str
    actions: list[StrategyAction]
    evidence: list[Evidence]
    warnings: list[WarningMessage]
    version: VersionTag


class OCRChecklistItem(BaseModel):
    item: str
    deadline: str
    assignee: str


class OCRResponse(BaseModel):
    summary: str
    required_actions: list[OCRChecklistItem]
    ocr_confidence: float
    raw_text: str
    evidence: list[Evidence]
    version: VersionTag


class GovernanceRegistryResponse(BaseModel):
    versions: list[VersionTag]
    rollback_ready: bool
    changed_at: datetime


class WorkflowStep(BaseModel):
    name: str
    status: Literal["completed", "skipped", "pending_approval"]
    detail: str


class WorkflowRequest(BaseModel):
    store_id: str
    scenario: Literal["retention_recovery", "anomaly_followup", "operations_tuning"]
    dry_run: bool = True
    sales_input: Optional[SalesDiagnosticRequest] = None
    churn_input: Optional[ChurnInsightRequest] = None
    anomaly_input: Optional[AnomalyExplanationRequest] = None
    retention_input: Optional[RetentionOfferRequest] = None
    menu_input: Optional[MenuPricingRequest] = None
    staffing_input: Optional[StaffingOptimizationRequest] = None
    inventory_input: Optional[InventoryOptimizationRequest] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    status: Literal["running", "completed", "pending_approval"]
    steps: list[WorkflowStep]
    outputs: dict[str, str]
