from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.config import ALIAS_REVERT


class IgnoreFieldModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    @model_validator(mode="before")
    def remove_quotes(cls, values):
        for key, value in values.items():
            if isinstance(value, str):
                values[key] = value.strip('"')
        return values


def mapping_alias(field_name: str):
    return ALIAS_REVERT.get(field_name, field_name)


class AliasGenIgnoreFields(IgnoreFieldModel):
    model_config = ConfigDict(extra="ignore", alias_generator=mapping_alias, populate_by_name=True)


class Link(IgnoreFieldModel):
    href: str


class Links(IgnoreFieldModel):
    self: Link
    next: Link | None = None
    first: Link | None = None
    prev: Link | None = None


class PaginatedResponse(IgnoreFieldModel):

    links: Links = Field(alias="_links")

    def get_items(self):
        """Возвращает элементы в зависимости от типа ответа."""
        raise NotImplementedError("This method should be implemented in subclasses.")
