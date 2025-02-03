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


class AMOClientData:  # TODO переписать под мулти
    base_url = ".amocrm.ru"
    suffics = {
        "leads": "/api/v4/leads",
        "contacts": "/api/v4/contacts",
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
    def get_validated_contact(amo_contact: dict, lead: dict, schools: list[dict], partner: str) -> dict:
        contact = {}
        contact["id"] = int(datetime.now(timezone.utc).timestamp() * 10**6)  # amo_contact['id']
        contact["amo_id"] = amo_contact["id"]
        contact["amo_lead_id"] = lead["id"]
        contact["first_name"] = amo_contact["first_name"]
        contact["last_name"] = amo_contact["last_name"]
        contact["name"] = amo_contact["name"]
        contact["phone"] = None
        contact["partner"] = partner
        params = {}
        for cust_f in amo_contact["custom_fields_values"]:
            if cust_f.get("field_code") == "PHONE":
                contact["phone"] = AMOClientStatic.clear_phone_number(cust_f.get("values")[0]["value"])
            else:
                params[cust_f.get("field_name")] = cust_f.get("values")[0]["value"]
                if cust_f.get("field_name") == "Школа":
                    try:
                        school_number = int(cust_f.get("values")[0]["value"])
                        params["school_id"] = None
                        for school in schools:
                            logger.debug(f"school = {school}, school_number = {school_number}")
                            if school.get("number") == school_number:
                                params["school_id"] = school.get("id")
                    except Exception as e:
                        logger.warning(f"{traceback.format_exc()}")
        contact["params"] = params
        return contact

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

    def __init__(self, url_prefix, long_token, pipelines, pipelines_statuses):
        self.url = "https://" + url_prefix + self.base_url
        self.token = long_token
        self.pipelines = pipelines
        self.pipelines_statuses = pipelines_statuses

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

    async def _request_patch(self, suffics_name, json_data, **kwargs):
        result = {}
        headers = self._get_headers()
        async with ClientSession(headers=headers) as session:
            url = self.url + self.suffics[suffics_name]
            logger.info(f"url = {url}")
            async with session.patch(url=url, data=json_data, **kwargs) as response:
                # logger.info(f'resp.status = {response.status}, headers = {response.headers}')
                result = await response.read()
                status = response.status
            if status in (
                http.HTTPStatus.OK,
                http.HTTPStatus.CREATED,
            ):

                result = json.loads(result)
        return status, result

    async def get_leads(self, pipeline_id=None, **kwargs):
        pesult = []
        kwargs["params"] = kwargs.get("params", {})
        kwargs["params"] |= {"with": "contacts"}
        if pipeline_id:
            kwargs["params"] |= {"filter[pipeline_id]": pipeline_id}
        logger.debug("kwargs = %r", kwargs)
        status, result = await self._request_get(suffics_name="leads", **kwargs)
        logger.debug(f"status get_leads = {status}")
        return result

    async def patch_leads(self, json_data, **kwargs):
        json_data = json.dumps(json_data)
        status, result = await self._request_patch(suffics_name="leads", json_data=json_data, **kwargs)
        return result

    async def get_piplines(self, **kwargs):
        result = await self._request_get(suffics_name="pipelines", **kwargs)
        return result

    async def get_contact(self, contact_id, **kwargs):
        status, result = await self._request_get(suffics_name=f"contacts", id=contact_id)
        return result

    async def lead_done(self, lead_id):
        new_pipeline_id = self.pipelines["Записаны"]
        new_status_id = self.pipelines_statuses[new_pipeline_id]["Успешно реализовано"]
        data_patch_leads = [
            {
                "id": lead_id,
                "pipeline_id": new_pipeline_id,
                "status_id": new_status_id,
            },
        ]
        logger.debug(f"data_patch_leads = {data_patch_leads}")
        result = await self.patch_leads(json_data=data_patch_leads)
        return result

    async def update_lead_status(self, lead_id, status):
        new_pipeline_name = self._get_new_pipeline_name(status)
        new_status_name = self._get_new_status_name(status)
        new_pipeline_id = self.pipelines[new_pipeline_name]
        logger.debug("new_pipeline_id=%r, new_status_name=%r", new_pipeline_id, new_status_name)
        logger.debug(f"self.pipelines_statuses[new_pipeline_id] = {self.pipelines_statuses[new_pipeline_id]}")
        new_status_id = self.pipelines_statuses[new_pipeline_id][new_status_name]
        logger.debug(
            "new_pipeline_name=%r, new_status_name=%r, new_pipeline_id=%r, new_status_id=%r",
            new_pipeline_name,
            new_status_name,
            new_pipeline_id,
            new_status_id,
        )
        data_patch_leads = [
            {
                "id": lead_id,
                "pipeline_id": int(new_pipeline_id),
                "status_id": new_status_id,
            },
        ]
        logger.debug(f"data_patch_leads = {data_patch_leads}")
        result = await self.patch_leads(json_data=data_patch_leads)

        return result

    def pipelines_get(self, key):
        return int(self.pipelines[key])

    @classmethod
    def _get_new_pipeline_name(cls, status):
        return cls._conv_code2name.get(status, {}).get("pipeline")

    @classmethod
    def _get_new_status_name(cls, status):
        return cls._conv_code2name.get(status, {}).get("pipeline_status")

    _conv_code2name = {
        1: {"name": "Выбрал курс", "pipeline": "Записаны", "pipeline_status": "Записаны_Первичный_контакт"},
        2: {"name": "Нужна связь с менеджером", "pipeline": "Human", "pipeline_status": "Human_Первичный_контакт"},
        3: {"name": "Не отвечает", "pipeline": "Не_отвечает", "pipeline_status": "Не_отвечает_Первичный_контакт"},
        4: {"name": "Отказ", "pipeline": "Отказ", "pipeline_status": "Отказ_Первичный_контакт"},
    }
