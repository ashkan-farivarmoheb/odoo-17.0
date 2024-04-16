import base64
import json
import logging

import requests

from odoo import _
from odoo.exceptions import UserError
from odoo.tools import config

_logger = logging.getLogger(__name__)
host = config.options.get("services_austpost_endpoint")
shipment_price_path = config.options.get("services_austpost_shipmentPrice_path")
account_details_path = config.options.get("services_austpost_accountDetails_path")
create_shipment_path = config.options.get("services_austpost_createShipment_path")
create_order_path = config.options.get("services_austpost_createOrder_path")
service_rate_path = config.options.get("services_austpost_serviceRate_path")
item_prices_path = config.options.get("services_austpost_get_item_prices_path")
delete_shipment_path = config.options.get("services_austpost_delete_shipment_path")


class AustraliaPostRepository(object):
    CONTENT_TYPE = "application/json"
    ACCEPT = "application/json"

    def __init__(self, carrier, record=None):
        self.carrier = carrier
        self.record = record
        self.appVersion = 1.0
        self.password = carrier.australia_post_api_password
        self.account = carrier.australia_post_account_number if carrier.australia_post_account_number else None
        self.api_key = carrier.australia_post_api_key
        auth_encoding = "%s:%s" % (self.account, self.password)
        self.authentication = " ".join(["Base", base64.b64encode(auth_encoding.encode("utf-8"))])

    def get_shipping_rates(self, source=None, destination=None, items=None):
        response = None
        try:
            if source is None:
                raise UserError(_("Source for getting shipping rate is missing."))
            if destination is None:
                raise UserError(_("Destination for getting shipping rate is missing."))
            if items is None:
                raise UserError(_("Items for getting shipping rate are missing."))

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": self.authentication,
                "ACCOUNT-NUMBER": self.account
            }

            payload = json.dumps({"shipments": [{
                "from": source,
                "to": destination,
                "items": items
            }]})
            res = requests.post(url="".join([host, create_shipment_path]), headers=headers, data=payload)
            res_json = res.json()

            if res.status_code == 200:
                response = self.create_success_response(res_json)
            else:
                response = self.create_error_response(res_json)

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

    def get_shipping_rates(self, data=None):
        response = None
        _logger.debug(" self.account2: %s ", self.account)
        _logger.debug(" self.carrier read2: %s ", self.carrier.read())

        try:
            if not self.api_key:
                raise UserError(
                    _("The Australia Post API Key is not configured in the Shipping Method settings. Please set it before proceeding."))
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "AUTH-KEY": self.api_key
            }

            if not data:
                raise UserError(
                    _("Data for shipping rate calculation is missing."))
            params = {
                'length': data['length'],
                'width': data['width'],
                'height': data['height'],
                'weight': data['weight'],
                'from_postcode': data['from_postcode'],
                'to_postcode': data['to_postcode'],
                'service_code': data['service_code']
            }

            res = requests.get(url="".join([host, service_rate_path]), params=params, headers=headers, timeout=10)
            res_json = res.json()

            if res.status_code == 200:
                response = {
                    'success': True,
                    'price': res_json['postage_result']['total_cost'],
                    'error_message': False,
                    'warning_message': False,
                }
            else:
                response = {
                    'success': False,
                    'price': -1,
                    'error_message': res_json['error']['errorMessage'],
                    'warning_message': res_json['error']['errorMessage'],
                }

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

        account_number = carrier_record.get('australia_post_account_number')

        try:
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": self.authentication,
                "ACCOUNT-NUMBER": account_number
            }

            url = f"{host}{account_details_path}{str(account_number)}"

            res = requests.get(url=url, headers=headers, timeout=10)
            res_json = res.json()
            _logger.error("res json: %s  res.status_code %s ",
                          res_json, res.status_code)

            if res.status_code == 200:
                response = self.create_success_response(res_json)
            else:
                response = self.create_error_response(res_json)

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

    def create_shipment(self, shipment_detail=None, source=None, destination=None, items=None):
        response = None

        try:
            if shipment_detail is None:
                raise UserError(_("Shipment details for creating shipping is missing."))
            if source is None:
                raise UserError(_("Source for creating shipping is missing."))
            if destination is None:
                raise UserError(_("Destination for creating shipping is missing."))
            if items is None:
                raise UserError(_("Items for creating shipping are missing."))

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": self.authentication
            }

            payload = json.dumps({"shipments": [{
                "shipment_reference": shipment_detail['shipment_reference'],
                "customer_reference_1": shipment_detail['customer_reference_1'],
                "customer_reference_2": shipment_detail['customer_reference_2'],
                "email_tracking_enabled": shipment_detail['email_tracking_enabled'],
                "from": source,
                "to": destination,
                "items": items
            }]})
            res = requests.post(url="".join([host, create_shipment_path]), headers=headers, data=payload)
            res_json = res.json()

            if res.status_code == 201:
                response = self.create_success_response(res_json)
            else:
                response = self.create_error_response(res_json)

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

    def get_item_prices(self, source=None, destination=None, items=None):
        response = None
        try:
            if source is None:
                raise UserError(_("Source for getting item price is missing."))
            if destination is None:
                raise UserError(_("Destination for getting price is missing."))
            if items is None:
                raise UserError(_("Items for getting prices are missing."))
            if items['product_ids'] is None:
                _logger.info("product_ids for getting prices are missing")

            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": self.authentication,
                "ACCOUNT-NUMBER": self.account
            }

            payload = json.dumps({
                "from": source,
                "to": destination,
                "items": items
            })
            res = requests.post(url="".join([host, item_prices_path]), headers=headers, data=payload)
            res_json = res.json()

            if res.status_code == 200:
                response = self.create_success_response(res_json)
            else:
                response = self.create_error_response(res_json)

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

    def delete_shipment(self, shipment_ids):
        if not shipment_ids:
            raise UserError(_("Shipment Ids are is missing."))

        response = None
        try:
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "Authentication": self.authentication,
                "ACCOUNT-NUMBER": self.account
            }
            if len(shipment_ids) == 1:
                url = f"{host}{delete_shipment_path}/{shipment_ids[0]}"
                params = {}
            else:
                url = "".join([host, delete_shipment_path])
                params = {
                    'shipment_ids': shipment_ids
                }

            res = requests.delete(url=url, headers=headers, params=params, timeout=10)

            if res.status_code == 200:
                response = self.create_success_response(None)
            else:
                res_json = res.json()
                response = self.create_error_response(res_json)

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


    def create_error_response(self, res_json):
        return {
            'success': False,
            'data': res_json
        }

    def create_success_response(self, res_json):
        return {
            'success': True,
            'data': res_json
        }
