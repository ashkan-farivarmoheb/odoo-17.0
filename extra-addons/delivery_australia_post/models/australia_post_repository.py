import base64
import json
import logging
import requests

from odoo import _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)

host = config.options.get("services_austpost_endpoint")
shipment_price_path = config.options.get(
    "services_austpost_shipmentprice_path")
account_details_path = config.options.get(
    "services_austpost_accountdetails_path")
create_shipment_path = config.options.get(
    "services_austpost_createshipment_path")
create_order_path = config.options.get("services_austpost_createorder_path")
service_rate_path = config.options.get("services_austpost_servicerate_path")
item_prices_path = config.options.get("services_austpost_get_item_prices_path")
delete_shipment_path = config.options.get(
    "services_austpost_delete_shipment_path")


def create_error_response(res_json):
    return {
        'success': False,
        'data': res_json
    }


def create_success_response(res_json):
    return {
        'success': True,
        'data': res_json
    }


def _private_get_account(carrier):
    if not carrier.get('australia_post_account_number'):
        raise UserError(
            _("Australia Post Account Number for getting shipping rate is missing."))
    else:
        return carrier.get('australia_post_account_number')


def _private_get_password(carrier):
    return carrier.get('australia_post_api_password')


def _private_get_api_key(carrier):
    return carrier.get('australia_post_api_key')


def _private_get_authentication(carrier):
    auth_encoding = "%s:%s" % (_private_get_account(
        carrier), _private_get_password(carrier))
    return " ".join(["Base", str(base64.b64encode(auth_encoding.encode("utf-8")))])


class AustraliaPostRepository(object):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        pass

    CONTENT_TYPE = "application/json"
    ACCEPT = "application/json"

    def get_shipping_rates(self, source=None, destination=None, items=None, carrier=None):
        response = None
        try:
            if source is None:
                raise UserError(
                    _("Source for getting shipping rate is missing."))
            if destination is None:
                raise UserError(
                    _("Destination for getting shipping rate is missing."))

            if items is None:
                raise UserError(
                    _("Items for getting shipping rate are missing."))

            if carrier is None:
                raise UserError(
                    _("carrier for getting shipping rate are missing."))

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": _private_get_authentication(carrier),
                "ACCOUNT-NUMBER": _private_get_account(carrier)
            }

            payload = json.dumps({"shipments": [{
                "from": source,
                "to": destination,
                "items": items
            }]})

            _logger.debug(
                'Initializing API Request get_shipping_rates payload: %s - headers: %s', payload, headers)
            res = requests.post(url="".join(
                [host, shipment_price_path]), headers=headers, data=payload)
            res_json = res.json()
            _logger.debug(
                'API response json get_shipping_rates: %s ', res_json)
            if res.status_code == 200:
                response = create_success_response(res_json)
            else:
                response = create_error_response(res_json)

        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 10s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response

    def get_account(self, carrier_record):
        response = None
        if not carrier_record:
            raise UserError(_("Carrier data is missing."))

        account_number = _private_get_account(carrier_record)

        try:
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": _private_get_authentication(carrier_record),
                "ACCOUNT-NUMBER": account_number
            }

            url = f"{host}{account_details_path.format(account_number=account_number)}"

            res = requests.get(url=url, headers=headers, timeout=10)
            res_json = res.json()
            _logger.error("res json: %s  res.status_code %s ",
                          res_json, res.status_code)

            if res.status_code == 200:
                response = create_success_response(res_json)
            else:
                response = create_error_response(res_json)

        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 10s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response

    def create_shipment(self, payload=None, carrier=None):
        _logger.debug(
            'create_shipment carrier: %s   payload: %s', carrier, payload)
        response = None

        try:
            if payload is None:
                raise UserError(
                    _("Payload for creating shipping is missing."))

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": _private_get_authentication(carrier)
            }

            res = requests.post(url="".join(
                [host, create_shipment_path]), headers=headers, data=payload)
            res_json = res.json()

            if res.status_code == 201:
                response = create_success_response(res_json)
                _logger.debug(
                    'create_shipment res: %s', res_json)
            else:
                response = create_error_response(res_json)

        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 10s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response

    def get_item_prices(self, source=None, destination=None, items=None, carrier=None):
        response = None
        try:
            if source is None:
                raise UserError(_("Source for getting item price is missing."))
            if destination is None:
                raise UserError(_("Destination for getting price is missing."))
            if items is None:
                raise UserError(_("Items for getting prices are missing."))
            if carrier is None:
                raise UserError(
                    _("carrier for getting shipping rate are missing."))

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": _private_get_authentication(carrier),
                "ACCOUNT-NUMBER": _private_get_account(carrier)
            }

            payload = json.dumps({
                "from": source,
                "to": destination,
                "items": items
            })
            _logger.debug(
                'Initializing API Request get_item_prices.payload: %s - headers: %s', payload, headers)

            res = requests.post(url="".join(
                [host, item_prices_path]), headers=headers, data=payload)
            res_json = res.json()
            _logger.debug(
                'API response json get_item_prices: %s ', res_json)
            if res.status_code == 200:
                response = create_success_response(res_json)
            else:
                response = create_error_response(res_json)
        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 10s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response

    def delete_shipment(self, shipment_ids, carrier=None):
        if not shipment_ids:
            raise UserError(_("Shipment Ids are is missing."))

        response = None
        try:
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": _private_get_authentication(carrier),
                "ACCOUNT-NUMBER": _private_get_account(carrier)
            }
            if len(shipment_ids) == 1:
                url = f"{host}{delete_shipment_path}/{shipment_ids[0]}"
                params = {}
            else:
                url = "".join([host, delete_shipment_path])
                params = {
                    'shipment_ids': shipment_ids
                }

            res = requests.delete(url=url, headers=headers,
                                  params=params, timeout=10)

            if res.status_code == 200:
                response = create_success_response(None)
            else:
                res_json = res.json()
                response = create_error_response(res_json)

        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 10s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response

    def create_order_shipments(self, payload=None, carrier=None):
        _logger.debug(
            'create_order_shipments carrier: %s   payload: %s', carrier, payload)
        return self._create_order_shipments(method="put", payload=payload, carrier=carrier)

    def create_order_including_from_shipments(self, payload=None, carrier=None):
        _logger.debug(
            'create_order_including_from_shipments carrier: %s   payload: %s', carrier, payload)
        return self._create_order_shipments(method="post", payload=payload, carrier=carrier)

    def _create_order_shipments(self, method="put", payload=None, carrier=None):
        _logger.debug(
            '_create_order_shipments carrier: %s   payload: %s', carrier, payload)

        try:
            if payload is None:
                raise UserError(_("Payload for creating shipping is missing."))

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": _private_get_authentication(carrier)
            }

            url = "".join([host, create_order_path])
            res = requests.request(method, url, headers=headers, data=payload)
            res_json = res.json()

            _logger.debug('res_json             %s', (res_json))

            if res.status_code == 200 and method == "put":
                response = create_success_response(res_json)
            elif res.status_code == 201 and method == "post":
                response = create_success_response(res_json)
            else:
                response = create_error_response(res_json)

        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 10s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response
