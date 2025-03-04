import asyncio
import http
import json
import os
import re
import traceback
from aiohttp import ClientSession
from datetime import datetime, timezone

from core.schemes.base import PaginatedResponse
from core.schemes.leads import Lead, LeadResponse
from core.schemes.pipelines import Pipeline, PipelinesResponse

from .logger import get_logger
from typing import Dict, Generator, List, Any, Iterable, Optional, Tuple, TypeVar, Type

logger = get_logger(__name__)

client = os.getenv("CLIENT", "turboagency")

T = TypeVar("T", bound=PaginatedResponse)


class AMOClientData:
    base_url = ".amocrm.ru"
    suffics = {
        "leads": "/api/v4/leads",
        "contacts": "/api/v4/contacts",
        "pipelines": "/api/v4/leads/pipelines",
        "pipeline": "/api/v4/leads/pipelines/{id}",
    }
    leads_with = []  # ["loss_reason", "contacts"]


class AMOClientStatic:
    @staticmethod
    def get_leads_from_response(response_dict: dict) -> list[dict]:
        leads = response_dict.get("_embedded", {}).get("leads", [])
        return leads

    @staticmethod
    def get_contact_ids_from_dict_lead(lead: dict) -> list[dict]:
        contacts = lead.get("_embedded", {}).get("contacts", [])
        return contacts

    @staticmethod
    def get_main_contact_id(contacts: list[dict]):
        result = None
        for contact in contacts:
            if contact.get("is_main"):
                return contact["id"]
        return result

    @staticmethod
    def get_validated_contact(amo_contact: dict, lead: dict) -> dict:
        contact = {}
        contact["id"] = amo_contact["id"]
        contact["amo_lead_id"] = lead["id"]
        contact["first_name"] = amo_contact["first_name"]
        contact["last_name"] = amo_contact["last_name"]
        contact["name"] = amo_contact["name"]
        contact["phone"] = None

        params = {}
        for cust_f in amo_contact["custom_fields_values"]:
            if cust_f.get("field_code") == "PHONE":
                contact["phone"] = AMOClientStatic.clear_phone_number(cust_f.get("values")[0]["value"])
            else:
                params[cust_f.get("field_name")] = cust_f.get("values")[0]["value"]

        contact["params"] = params
        return contact

    @staticmethod
    def extract__base_custom_fields(data: Dict[str, Any], fields: Iterable[str]) -> Dict[str, List[Any]]:
        """Базовый метод кастомных полей"""
        result = {}
        custom_fields = data.get("custom_fields_values", [])
        fields_set = set(fields)

        for field in custom_fields:
            field_name = field.get("field_name")

            if field_name in fields_set:
                result[field_name] = [item.get("value") for item in field.get("values", [])]

        return result

    # @staticmethod # TODO: сделать валидацию
    # def get_validated_lead(lead: dict, reason: dict) -> dict:
    #     lead = {}
    #     lead["id"] = amo_contact["id"]
    #     lead["amo_lead_id"] = lead["id"]
    #     lead["first_name"] = amo_contact["first_name"]
    #     lead["last_name"] = amo_contact["last_name"]
    #     lead["name"] = amo_contact["name"]
    #     lead["phone"] = None

    #     params = {}
    #     for cust_f in amo_contact["custom_fields_values"]:
    #         if cust_f.get("field_code") == "PHONE":
    #             contact["phone"] = AMOClientStatic.clear_phone_number(cust_f.get("values")[0]["value"])
    #         else:
    #             params[cust_f.get("field_name")] = cust_f.get("values")[0]["value"]

    #     contact["params"] = params
    #     return contact

    @staticmethod
    def clear_phone_number(phone: str) -> str | None:
        if type(phone) is not str:
            return None
        digits = re.findall(r"\d+", phone)
        phone = "".join(digits)  # phone.strip().replace("+", "").replace("-", "")
        if phone[0] == "8":
            phone = "7" + phone[1:]
        return phone

    @staticmethod
    def date_to_timestamp(date_str):
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            timestamp = int(date_obj.timestamp())
            return timestamp
        except Exception as err:
            logger.warning("cannot convert date: %s", err)
            return ""


class AMOClient(AMOClientData, AMOClientStatic):
    """Основной клиент"""

    def __init__(self, url_prefix, long_token):
        self.url = "https://" + url_prefix + self.base_url
        self.token = long_token
        self.headers = self._get_headers()

    def _get_headers(self) -> dict:
        headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
        return headers

    def _set_with_params_for_query(self, with_params: list[str]) -> dict:
        _dict = dict()
        if with_params:
            _dict["with"] = ",".join(param.strip() for param in with_params)
        return _dict

    def _get_default_with_param_for_leads(self) -> List:
        return self.leads_with

    async def _request_page(
        self, url: str, session: ClientSession, params: dict = {}
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        max_retries = 5  # Макс кол-во попыток
        for attempt in range(max_retries):
            response = await session.get(url, params=params)
            status, result = response.status, await response.read()
            if status in (http.HTTPStatus.OK, http.HTTPStatus.CREATED):
                return (status, json.loads(result))
            elif status == http.HTTPStatus.TOO_MANY_REQUESTS:  # 429
                wait_time = 1  # Время ожидания
                logger.warning("Too many requests. Waiting for %d seconds before retrying...", wait_time)
                await asyncio.sleep(wait_time)
            elif status == http.HTTPStatus.FORBIDDEN:  # 403
                logger.error("Access forbidden. Account may be blocked.")
                return status, {}
            else:
                logger.warning("_request_get status = %s result = %s", status, result)
                return status, {}

        logger.error("Max retries exceeded for request")
        return http.HTTPStatus.INTERNAL_SERVER_ERROR, {}

    async def _request_get(
        self, suffics_name, id=None, page: int = 1, limit: int = 250, filters: Optional[dict[str, int]] = None, **kwargs
    ) -> Tuple[int, Optional[Dict[str, Any]]]:
        params = {"limit": limit, "page": page}
        if filters:
            params.update(**self._filter_query(filters))

        if with_params := kwargs.pop("with", None):
            params.update(self._set_with_params_for_query(with_params))
        params.update(**kwargs)

        async with ClientSession(headers=self.headers) as session:
            url = self.url + self.suffics[suffics_name]
            if id:
                url += "/" + str(id)
            return await self._request_page(url, session, params=params)

    def _filter_query(self, filters: dict[str, int]) -> dict:
        filter_query = {}
        update_from = filters.pop("updated_at__from", None)
        update_to = filters.pop("updated_at__to", None)
        created_from = filters.pop("created_at__from", None)
        created_to = filters.pop("created_at__to", None)
        closed_from = filters.pop("closed_at__from", None)
        closed_to = filters.pop("closed_at__to", None)
        if update_from:
            filter_query["filter[updated_at][from]"] = update_from
        if update_to:
            filter_query["filter[updated_at][to]"] = update_to
        if created_from:
            filter_query["filter[created_at][from]"] = created_from
        if created_to:
            filter_query["filter[created_at][to]"] = created_to
        if closed_from:
            filter_query["filter[closed_at][from]"] = closed_from
        if closed_to:
            filter_query["filter[closed_at][to]"] = created_to
        filter_query.update({f"filter[{k}]": v for k, v in filters.items()})
        return filter_query

    async def _fetch_all_pages(
        self, cls: Type[T], suffics_name: str, filters: Optional[dict[str, int]] = None, **kwargs
    ) -> List[Any]:
        """Получить все страницы данных сущности."""
        all_items = []
        page = 1

        status, response = await self._request_get(suffics_name=suffics_name, page=page, filters=filters, **kwargs)
        first_page = cls(**response)
        all_items.extend(first_page.get_items())
        next_page = first_page.links.next.href if first_page.links.next else None

        async with ClientSession(headers=self.headers) as session:
            while next_page:
                status, result = await self._request_page(next_page, session)

                if status in (http.HTTPStatus.OK, http.HTTPStatus.CREATED):
                    pag_response = cls(**result)
                    all_items.extend(pag_response.get_items())

                    if pag_response.links.next:
                        next_page = pag_response.links.next.href
                    else:
                        break
                else:
                    logger.error("Failed to fetch data: status = %s, result = %s", status, result)
                    break

        return all_items

    async def get_leads(self, pipeline_id=None, filters: Optional[dict[str, int]] = None, **kwargs) -> List[Lead]:
        """Получить все лиды со связанной причиной"""
        with_params = kwargs.get("with", [])
        if len(with_params) == 0:
            with_params += self._get_default_with_param_for_leads()
            kwargs["with"] = with_params
        if pipeline_id:
            kwargs.update({"filter[pipeline_id]": pipeline_id})
        logger.debug("kwargs = %r", kwargs)

        return await self._fetch_all_pages(LeadResponse, suffics_name="leads", filters=filters, **kwargs)

    async def get_leads_with_params(
        self, with_params: list[str] = None, pipeline_id=None, filters: Optional[dict[str, int]] = None, **kwargs
    ) -> List[Lead]:
        kwargs.update({"with": with_params})
        return await self.get_leads(pipeline_id=pipeline_id, filters=filters, **kwargs)

    async def get_pipelines(self, **kwargs) -> List[Pipeline]:
        """Получить все воронки"""
        return await self._fetch_all_pages(PipelinesResponse, suffics_name="pipelines", **kwargs)

    async def get_contact_by_id(self, contact_id, **kwargs):  # TODO: сделать сущности
        status, result = await self._request_get(suffics_name=f"contacts", id=contact_id, **kwargs)
        return result

    async def get_contacts(self, filters: Optional[dict[str, int]] = None, **kwargs):
        with_params = kwargs.pop("with", [])
        with_params.append("leads")
        kwargs["with"] = with_params
        status, result = await self._request_get(suffics_name="contacts", filters=filters, **kwargs)
        return result
