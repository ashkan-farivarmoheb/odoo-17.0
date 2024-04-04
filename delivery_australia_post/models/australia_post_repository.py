import base64
import logging
import requests
from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AustraliaPostRepository(object):
    CONTENT_TYPE = "application/json"
    ACCEPT = "application/json"

    def __init__(self, carrier, record):
        self.url = "https://digitalapi.auspost.com.au"
        self.calculate_rate_path = "/postage/parcel/domestic/service.json"
        self.carrier = carrier
        self.record = record
        self.appVersion = 1.0
        self.password = self.carrier.australia_post_api_password
        self.account = self.carrier.australia_post_account_number
        self.api_key = self.carrier.australia_post_api_key

        auth_encoding = "%s:%s" % (self.account, self.password)
        self.authorization = base64.b64encode(auth_encoding.encode("utf-8")).decode("utf-8")

    def get_shipping_rates(self, data=None):
        response = None
        try:
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "AUTH-KEY": self.api_key
            }

            params = {
                'length': data.length,
                'width': data.width,
                'height': data.height,
                'weight': data.weight,
                'from_postcode': data.sender_postcode,
                'to_postcode': data.receiver_postcode,
                'service_code': data.service_code
            }

            res = requests.get(url="".join([self.url, self.calculate_rate_path]), params=params, headers=headers,
                               timeout=10)
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
                _("{}\n{}".format(e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response
