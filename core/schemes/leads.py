from pydantic import Field
from typing import Optional, List, Any, Dict
from core.schemes.base import IgnoreFieldModel, Link, PaginatedResponse


class CustomFieldValue(IgnoreFieldModel):
    field_id: int
    field_name: str
    field_code: str | None = None
    field_type: str
    values: List[Dict[str, Any]]


class Tag(IgnoreFieldModel):
    id: int
    name: str
    color: str | None = None


class Contact(IgnoreFieldModel):
    id: int
    is_main: bool
    links: Optional[Dict[str, Link]] = Field(alias="_links")


class LossReason(IgnoreFieldModel):
    id: int
    name: str
    sort: int
    created_at: int
    updated_at: int
    links: Optional[Dict[str, Link]] = Field(alias="_links")


class EmbeddedLead(IgnoreFieldModel):
    tags: List[Tag] | None = None
    companies: List[Any] | None = None
    contacts: List[Contact] | None = None
    loss_reason: List[LossReason] | None = None

    def get_last_loss_reason(self):
        if not self.loss_reason:
            return None
        return sorted(self.loss_reason, key=lambda lr: lr.created_at, reverse=True)[0]


class Lead(IgnoreFieldModel):
    id: int
    name: str
    price: int
    responsible_user_id: int
    group_id: int
    status_id: int
    pipeline_id: int
    loss_reason_id: int | None = None
    created_by: int
    updated_by: int
    created_at: int
    updated_at: int
    closed_at: int | None = None
    closest_task_at: int | None = None

    custom_fields_values: Optional[List[CustomFieldValue]] = None
    score: Any | None = None
    account_id: int

    links: Optional[Dict[str, Link]] = Field(alias="_links")
    embedded: EmbeddedLead = Field(alias="_embedded")


class EmbeddedLeadsResponse(IgnoreFieldModel):
    leads: List[Lead]


class LeadResponse(PaginatedResponse):
    page: int = Field(alias="_page")
    embedded: EmbeddedLeadsResponse = Field(alias="_embedded")

    def get_items(self) -> List[Lead]:
        return self.embedded.leads
