from pydantic import Field
from typing import List, Any, Dict
from core.config import ALIAS_MAPPING
from core.schemes.base import AliasGenIgnoreFields, IgnoreFieldModel
from core.schemes.leads import CustomFieldValue, Lead
from core.schemes.pipelines import EmbeddedPipelines, Pipeline

from pydantic import BaseModel, Field


class LeadToTable(AliasGenIgnoreFields):
    id: int
    name: str
    created_at: int
    stage: str | None = None
    pipeline: str | None = None
    price: int | None = None
    loss_reason: str | None = None
    closed_at: int | None = None
    responsible_user_id: int = None
    view: str | None = None
    institute: str | None = None
    admission: str | None = None
    program_type: str | None = None
    direction_1: str | None = None
    main_profile: str | None = None
    additional_profile_mitu: str | None = None
    dpo_direction: str | None = None
    dpo_program: str | None = None
    dpo_hours: str | None = None
    months_count: str | None = None
    ym_uid: str | None = None
    ym_counter: str | None = None
    google_client_id: str | None = None
    advertising_source: str | None = None
    traffic_type: str | None = None
    campaign_name: str | None = None
    advertisement: str | None = None
    keyword: str | None = None


# class LeadToTable(IgnoreFieldModel):
#     id: int = Field(aliases=["ID", "id"])
#     name: str = Field(aliases=["Название сделки", "name"])
#     created_at: int = Field(aliases=["Дата создания", "created_at"])
#     stage: str | None = Field(aliases=["Этап сделки", "stage"], default=None)
#     pipeline: str | None = Field(aliases=["Воронка", "pipeline"], default=None)
#     price: int | None = Field(aliases=["Бюджет", "price"], default=None)
#     loss_reason: str | None = Field(aliases=["Причина отказа", "loss_reason"], default=None)
#     closed_at: int | None = Field(aliases=["Дата закрытия", "closed_at"], default=None)
#     responsible_user_id: int = Field(aliases=["Ответственный", "responsible_user_id"], default=None)
#     view: str | None = Field(aliases=["Вид", "view"], default=None)
#     institute: str | None = Field(aliases=["Институт", "institute"], default=None)
#     admission: str | None = Field(aliases=["Поступление", "admission"], default=None)
#     program_type: str | None = Field(aliases=["Тип программы", "program_type"], default=None)
#     direction_1: str | None = Field(aliases=["Направление(1)", "direction_1"], default=None)
#     main_profile: str | None = Field(aliases=["Осн. Профиль", "main_profile"], default=None)
#     additional_profile_mitu: str | None = Field(aliases=["Доп. профиль МИТУ", "additional_profile_mitu"], default=None)
#     dpo_direction: str | None = Field(aliases=["Направление ДПО", "dpo_direction"], default=None)
#     dpo_program: str | None = Field(aliases=["Программа ДПО", "dpo_program"], default=None)
#     dpo_hours: str | None = Field(aliases=["Часы ДПО", "dpo_hours"], default=None)
#     months_count: str | None = Field(aliases=["Кол.мес", "months_count"], default=None)
#     ym_uid: str | None = Field(aliases=["ym_uid"], default=None)
#     ym_counter: str | None = Field(aliases=["ym_counter"], default=None)
#     google_client_id: str | None = Field(aliases=["Google Client ID", "google_client_id"], default=None)
#     advertising_source: str | None = Field(aliases=["Источник рекламы", "advertising_source"], default=None)
#     traffic_type: str | None = Field(aliases=["Тип трафика", "traffic_type"], default=None)
#     campaign_name: str | None = Field(aliases=["Название РК", "campaign_name"], default=None)
#     advertisement: str | None = Field(aliases=["Объявление", "advertisement"], default=None)
#     keyword: str | None = Field(aliases=["Ключевое слово", "keyword"], default=None)


class ToCSV(IgnoreFieldModel):
    items: List[LeadToTable] | None = []

    def add_lead_table_to_items(self, list_pipelines: List[Pipeline], leads: List[Lead]) -> List[LeadToTable]:
        """Добавляет в список обьекты модели"""
        pipelines = EmbeddedPipelines(pipelines=list_pipelines).get_pipelines()
        for lead in leads:
            custom_fields_values = self._extract_custom_fields(lead.custom_fields_values or [])

            to_tbl = LeadToTable(
                id=lead.id,
                name=lead.name,
                created_at=lead.created_at,
                responsible_user_id=lead.responsible_user_id,
                stage=pipelines[lead.pipeline_id].get_status_by_id(lead.status_id).name,
                pipeline=pipelines[lead.pipeline_id].name,
                loss_reason=lead.embedded.get_last_loss_reason(),
                **custom_fields_values,
            )
            self.items.append(to_tbl)

    def _extract_custom_fields(self, custom_fields: List[CustomFieldValue]) -> Dict[str, Any]:

        extracted_values = {}

        for field in custom_fields:
            if field.field_name in ALIAS_MAPPING:
                extracted_values[ALIAS_MAPPING[field.field_name]] = field.values[0]["value"] if field.values else None

        return extracted_values
