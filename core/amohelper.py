import http
import json
import os
import re
import traceback
from aiohttp import ClientSession
from datetime import datetime, timezone
from .logger import get_logger


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


class AMOClient(AMOClientData, AMOClientStatic):
    """Основной клиент"""

    def __init__(self, url_prefix, long_token):
        self.url = "https://" + url_prefix + self.base_url
        self.token = long_token

    def _get_headers(self) -> dict:
        headers = {"Authorization": "Bearer " + self.token, "Content-Type": "application/json"}
        return headers

    async def _request_get(self, suffics_name, id=None, **kwargs):
        result = {}
        headers = self._get_headers()
        async with ClientSession(headers=headers) as session:
            url = self.url + self.suffics[suffics_name]
            if id:
                url += "/" + str(id)
            # logger.info(f'url = {url}')
            async with session.get(url=url, **kwargs) as response:
                # logger.info(f'resp.status = {response.status}, headers = {response.headers}')
                result = await response.read()
                status = response.status
            if status in (
                http.HTTPStatus.OK,
                http.HTTPStatus.CREATED,
            ):
                result = json.loads(result)
            else:
                logger.warning("_request_get status = %s result = %s", status, json.loads(result))
                result = {}
        return status, result

    async def get_leads_with_loss_reason(self, pipeline_id=None, **kwargs):
        """Получить лиды со связанной причиной"""
        kwargs["params"] = kwargs.get("params", {})
        kwargs["params"] |= {"with": "loss_reason"}
        if pipeline_id:
            kwargs["params"] |= {"filter[pipeline_id]": pipeline_id}
        logger.debug("kwargs = %r", kwargs)
        status, result = await self._request_get(suffics_name="leads", **kwargs)
        logger.debug(f"status get_leads = {status}")
        return result

    async def get_pipelines(self, **kwargs):
        status, result = await self._request_get(suffics_name="pipelines", **kwargs)
        return result

    async def get_contact_by_id(self, contact_id, **kwargs):
        status, result = await self._request_get(suffics_name=f"contacts", id=contact_id, **kwargs)
        return result

    async def get_contacts(self, **kwargs):
        kwargs["params"] = kwargs.get("params", {})
        kwargs["params"] |= {"with": "leads"}
        status, result = await self._request_get(suffics_name=f"contacts", **kwargs)
        return result
