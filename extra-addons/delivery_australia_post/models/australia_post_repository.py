import base64
import logging
import requests
from odoo import _
from odoo.exceptions import UserError
import json

_logger = logging.getLogger(__name__)


class AustraliaPostRepository(object):
    CONTENT_TYPE = "application/json"
    ACCEPT = "application/json"

    def __init__(self, carrier, record=None):
        self.url = "https://digitalapi.auspost.com.au"
        self.calculate_rate_path = "/postage/parcel/domestic/calculate.json"
        self.get_account_path = "/shipping/v1/accounts/"
        self.carrier = carrier
        self.record = record
        self.appVersion = 1.0
        self.password = carrier.australia_post_api_password
        self.account = carrier.australia_post_account_number if carrier.australia_post_account_number else None

        auth_encoding = "%s:%s" % (self.account, self.password)
        self.authorization = base64.b64encode(
            auth_encoding.encode("utf-8")).decode("utf-8")

    def get_shipping_rates(self, data=None):
        response = None
        _logger.debug(" self.account2: %s ", self.account)
        _logger.debug(" self.carrier read2: %s ",  self.carrier.read())

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
                _("{}\n{}".format(
                    e, response['error_message'] if response else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return response

    def get_account(self, carrier_record):
        response = None
        account_number = carrier_record.get(
            'australia_post_account_number')

        try:
            headers = {
                "Content-Type": AustraliaPostRepository.CONTENT_TYPE,
                "Accept": AustraliaPostRepository.ACCEPT,
                "ACCOUNT-NUMBER": account_number
            }

            params = {
                'account_number': str(account_number),
            }
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # TODO: get real api response using the following url when have access to real account code uncomment following res

            # res = requests.get(url="".join([self.url, self.get_account_path, account_number]), params=params, headers=headers,
            #                    timeout=10)
# /////////////////////////////////////////////////////////////////////////////////////////////////////
         # TODO:remove simulated_json_data and res when you have when have access to real account api
            simulated_json_data = {
                "account_number": str(account_number),
                "name": "Abc Xyz Co",
                "valid_from": "2014-02-24",
                "valid_to": "2999-12-31",
                "expired": False,
                "addresses": [
                    {
                        "type": "MERCHANT_LOCATION",
                        "lines": [
                            "1 Main Street",
                            "Melbourne"
                        ],
                        "suburb": "CHADSTONE",
                        "postcode": "3000",
                        "state": "VIC"
                    }
                ],
                "details": {
                    "abn": "123456789",
                           "acn": "123456789",
                           "contact_number": "0312345678",
                           "email_address": "abcxyz_DONOTUSE@abcxyz.com.au",
                           "lodgement_postcode": "3000"
                },
                "postage_products": [


                    {
                        "type": "PARCEL POST",
                        "group": "Parcel Post",
                        "product_id": "T28",
                        "contract": {
                            "valid_from": "2014-01-31",
                            "valid_to": "2015-01-31",
                            "expired": False,
                            "volumetric_pricing": True,
                            "max_item_count": 0,
                            "cubing_factor": 250
                        },
                        "authority_to_leave_threshold": 500,
                        "features": {
                            "TRANSIT_COVER": {
                                "type": "TRANSIT_COVER",
                                "attributes": {
                                    "rate": 1.5,
                                    "included_cover": 200,
                                    "maximum_cover": 5000
                                },
                                "bundled": True
                            }
                        },
                        "options": {
                            "signature_on_delivery_option": False,
                            "authority_to_leave_option": True
                        }
                    },
                    {
                        "type": "EXPRESS POST",
                        "group": "Express Post",
                        "product_id": "E34",
                        "contract": {
                            "valid_from": "2014-01-31",
                            "valid_to": "2015-01-31",
                            "expired": False,
                            "volumetric_pricing": True,
                            "max_item_count": 0,
                            "cubing_factor": 250
                        },
                        "options": {
                            "signature_on_delivery_option": False,
                            "authority_to_leave_option": True
                        }
                    },
                    {
                        "type": "EXPRESS POST + SIGNATURE",
                        "group": "Express Post",
                        "product_id": "E34S",
                        "contract": {
                            "valid_from": "2014-01-31",
                            "valid_to": "2015-01-31",
                            "expired": False,
                            "volumetric_pricing": True,
                            "max_item_count": 0,
                            "cubing_factor": 250
                        },
                        "options": {
                            "signature_on_delivery_option": True,
                            "authority_to_leave_option": True
                        }
                    },
                    {
                        "type": "PARCEL POST + SIGNATURE",
                        "group": "Parcel Post",
                        "product_id": "T28S",
                        "contract": {
                            "valid_from": "2014-01-31",
                            "valid_to": "2015-01-31",
                            "expired": False,
                            "volumetric_pricing": True,
                            "max_item_count": 0,
                            "cubing_factor": 250
                        },
                        "options": {
                            "signature_on_delivery_option": True,
                            "authority_to_leave_option": True
                        }
                    }
                ],
                "merchant_location_id": "ABC",
                "credit_blocked": False
            }
            error_data = {
                "error": {
                    "message": "An error occurred"
                }
            }
            res = MockResponse(simulated_json_data, 200)
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////
            res_json = res.json()
            _logger.error("res json: %s  res.status_code %s ",
                          res_json, res.status_code)

            if res.status_code == 200:
                data = {
                    'name': res_json['name'],
                    'valid_from': res_json['valid_from'],
                    'account_number': res_json['account_number'],
                    'valid_to': res_json['valid_to'],
                    'table_ids': [(0, 0, {'type': line['type'], 'group': line['group'], 'product_id': line['product_id']}) for line in res_json['postage_products']], }

                response = {
                    'success': True,
                    'data': data,
                    'error_message': False,
                    'warning_message': False,
                }
            else:
                response = {
                    'success': False,
                    'data': {},
                    'error_message': res_json['error']['message'],
                    'warning_message': res_json['error']['message'],
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


# TODO:remove MockResponse
class MockResponse:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data
