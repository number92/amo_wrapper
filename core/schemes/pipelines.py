from pydantic import Field
from typing import List, Optional, Dict
from core.schemes.base import IgnoreFieldModel, Link, Links, PaginatedResponse


class Status(IgnoreFieldModel):
    id: int
    name: str
    sort: int | None = None
    is_editable: bool
    pipeline_id: int | None = None
    color: str | None = None
    type: int | None = None
    account_id: int | None = None
    links: Optional[Dict[str, Link]] = Field(alias="_links")


class Pipeline(IgnoreFieldModel):
    id: int
    name: str
    sort: int
    is_main: bool
    is_unsorted_on: bool
    is_archive: bool
    account_id: int | None = None
    links: Optional[Dict[str, Link]] = Field(alias="_links")
    embedded: Optional[Dict[str, List[Status]]] = Field(alias="_embedded")

    def get_statuses(self) -> Optional[Dict[int, str]]:
        if not self.embedded:
            return None
        statuses = {}

        for key, status_list in self.embedded.items():
            if status_list:
                for status in status_list:
                    statuses[status.id] = status.name
        return statuses

    def get_status_by_id(self, id: int) -> Status | None:
        if not self.embedded:
            return None
        for status in self.embedded["statuses"]:
            if status.id == id:
                return status
        return None


class EmbeddedPipelines(IgnoreFieldModel):
    pipelines: List[Pipeline]

    def get_pipelines(self) -> Dict[int, Pipeline]:
        """Возвращает словарь id: Pipeline"""
        pipelines = {}
        for pipeline in self.pipelines:
            pipelines[pipeline.id] = pipeline
        return pipelines


class PipelinesResponse(PaginatedResponse):
    total_items: int = Field(alias="_total_items")

    embedded: EmbeddedPipelines = Field(alias="_embedded")

    def get_items(self) -> List[Pipeline]:
        return self.embedded.pipelines
