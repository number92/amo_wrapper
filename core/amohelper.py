import http
import json
import os
import re
import traceback
from aiohttp import ClientSession
from datetime import datetime, timezone
from .logger import get_logger
from typing import Dict, List, Any, Iterable, Optional

logger = get_logger(__name__)

client = os.getenv("CLIENT", "turboagency")


class AMOClientData:
    base_url = ".amocrm.ru"
    suffics = {
        "leads": "/api/v4/leads",
        "contacts": "/api/v4/contacts",
        "pipelines": "/api/v4/leads/pipelines",
        "pipeline": "/api/v4/leads/pipelines/{id}",
    }


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

    def _get_headers(self) -> dict:
        headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
        return headers

    async def _request_get(
        self,
        suffics_name,
        id=None,
        page: int = 1,
        limit: int = 250,
        filters: Optional[dict[str, int]] = None,
        **kwargs,
    ):
        params = {"limit": limit, "page": page}
        if filters:
            params.update(**self._create_filter_query(filters))
        headers = self._get_headers()
        with_params: list | None = kwargs.pop("with", None)
        if with_params:
            params["with"] = ",".join(param for param in with_params)
        params.update(**kwargs)
        async with ClientSession(headers=headers) as session:
            url = self.url + self.suffics[suffics_name]
            if id:
                url += "/" + str(id)
            # logger.info(f'url = {url}')
            async with session.get(url=url, params=params) as response:
                # logger.info(f'resp.status = {response.status}, headers = {response.headers}')
                result = await response.read()
                status = response.status
            if status in (
                http.HTTPStatus.OK,
                http.HTTPStatus.CREATED,
            ):
                result = json.loads(result)
            else:
                logger.warning("_request_get status = %s result = %s", status, result)
                result = {}
        return status, result

    def _create_filter_query(self, filters: dict[str, int]) -> dict:
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

    async def get_leads_with_loss_reason(self, pipeline_id=None, filters: Optional[dict[str, int]] = None, **kwargs):
        """Получить лиды со связанной причиной"""
        with_params = kwargs.pop("with", [])
        with_params.append("loss_reason")
        kwargs["with"] = with_params
        if pipeline_id:
            kwargs.update({"filter[pipeline_id]": pipeline_id})
        logger.debug("kwargs = %r", kwargs)
        status, result = await self._request_get(suffics_name="leads", filters=filters, **kwargs)
        logger.debug(f"status get_leads = {status}")
        return result

    async def get_pipelines(self, **kwargs):
        status, result = await self._request_get(suffics_name="pipelines", **kwargs)
        return result

    async def get_contact_by_id(self, contact_id, **kwargs):
        status, result = await self._request_get(suffics_name=f"contacts", id=contact_id, **kwargs)
        return result

    async def get_contacts(self, filters: Optional[dict[str, int]] = None, **kwargs):
        with_params = kwargs.pop("with", [])
        with_params.append("leads")
        kwargs["with"] = with_params
        status, result = await self._request_get(suffics_name="contacts", filters=filters, **kwargs)
        return result
