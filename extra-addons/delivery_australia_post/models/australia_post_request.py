import base64
import json
import logging
import re

import dicttoxml
import requests
import xmltodict

from odoo import _, fields, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
dicttoxml.LOG.setLevel(logging.ERROR)


class AustraliaPostRequest(object):
    def __init__(self, carrier, record):
        self.url = "https://express.tnt.com"
        self.carrier = carrier
        self.record = record
        self.appVersion = 1.0

        # self.product_type = self.carrier.tnt_product_type
        # self.product_code = self.carrier.tnt_product_code
        # self.product_service = self.carrier.tnt_product_service
        # self.service_option = self.carrier.tnt_service_option
        # self.username = self.carrier.tnt_oca_ws_username

        self.password = self.carrier.australia_post_api_password
        self.account = self.carrier.australia_post_account_number
        self.api_key = self.carrier.australia_post_api_key

        # self.default_packaging_id = self.carrier.tnt_default_packaging_id
        # self.use_packages_from_picking = self.carrier.tnt_use_packages_from_picking

        auth_encoding = "%s:%s" % (self.api_key, self.password)
        self.authorization = base64.b64encode(auth_encoding.encode("utf-8")).decode(
            "utf-8"
        )

    def _send_api_request(
        self, url, data=None, auth=True, content_type="application/json", accept="application/json"
    ):

        if data is None:
            data = {}
        tnt_last_request = ("URL: {}\nData: {}").format(self.url, data)
        self.carrier.log_xml(tnt_last_request, "tnt_last_request")
        try:
            headers = {"Content-Type": content_type,
                       "Accept": accept, "Account-Number": self.account}
            if auth:
                headers["Authorization"] = "Basic {}".format(
                    self.authorization)
            res = requests.post(
                url=url, data=data.encode("utf-8"), headers=headers, timeout=60
            )
            res.raise_for_status()
            self.carrier.log_xml(res.text or "", "tnt_last_response")
            res = res.text
        except requests.exceptions.Timeout:
            raise UserError(_("Timeout: the server did not reply within 60s"))
        except (ValueError, requests.exceptions.ConnectionError):
            raise UserError(_("Server not reachable, please try again later"))
        except requests.exceptions.HTTPError as e:
            raise UserError(
                _("{}\n{}".format(e, res.json().get("Message", "") if res.text else ""))
            )
        except Exception as e:
            raise UserError(_("Unexpected error: %s", e))

        return res


# https://developers.auspost.com.au/apis/shipping-and-tracking/reference/get-shipment-price
# example Req
# {
#     "shipments":[
#         {
#             "from":{
#                 "suburb": "MELBOURNE",
#                 "state": "VIC",
#                 "postcode": "3000"
#             },
#             "to":{
#                 "suburb":"SYDNEY",
#                 "state":"NSW",
#                 "postcode":"2000"
#             },
#             "items":[
#                 {
#                     "product_id":"7D55",
#                     "length":"5",
#                     "height":"1",
#                     "width":"10",
#                     "weight":"2"
#                 }
#             ]
#         }
#     ]
# }


# Example Response
#  {
#     "shipments": [
#         {
#             "from": {
#                 "type": "MERCHANT_LOCATION",
#                 "lines": [],
#                 "suburb": "MELBOURNE",
#                 "postcode": "3000",
#                 "state": "VIC",
#                 "country": "AU"
#             },
#             "to": {
#                 "lines": [],
#                 "suburb": "SYDNEY",
#                 "postcode": "2000",
#                 "state": "NSW",
#                 "country": "AU"
#             },
#             "items": [
#                 {
#                     "weight": 2,
#                     "height": 1,
#                     "length": 5,
#                     "width": 10,
#                     "product_id": "7D55"
#                 }
#             ],
#             "options": {},
#             "features": {},
#             "shipment_summary": {
#                 "total_cost": 20.46,
#                 "total_cost_ex_gst": 18.6,
#                 "shipping_cost": 9.30,
#                 "fuel_surcharge": 9.30,
#                 "total_gst": 1.86,
#                 "tracking_summary": {},
#                 "number_of_items": 1
#             },
#             "movement_type": "DESPATCH",
#             "charge_to_account": "0000000000"
#         }
#     ]
# }


# Example error

# {
#     "errors": [
#         {
#             "code": "44003",
#             "name": "DANGEROUS_GOODS_NOT_SUPPORTED_BY_PRODUCT_ERROR",
#             "message": "The product T28S specified in an item has indicated that dangerous goods will be included in the parcel, however, the product does not allow dangerous goods to be sent using the service.  Please choose a product that allows dangerous goods to be included within the parcel to be sent."
#         }
#     ]
# }


# {'id': 6, 'campaign_id': (4, 'Email Campaign - Products'),
#  'source_id': (10, 'Sale Promotion 1'),
#  'medium_id': (4, 'Email'), 'activity_ids': [],
#  'activity_state': False, 'activity_user_id': False,
#  'activity_type_id': False, 'activity_type_icon': False,
#  'activity_date_deadline': False, 'my_activity_date_deadline': False,
#  'activity_summary': False, 'activity_exception_decoration': False,
#  'activity_exception_icon': False, 'message_is_follower': True,
#  'message_follower_ids': [29, 47], 'message_partner_ids': [3, 15],
#  'message_ids': [378, 377, 376, 375, 374, 373, 372, 371, 370, 369, 368, 367, 366, 121],
#  'has_message': True, 'message_needaction': False, 'message_needaction_counter': 0,
#  'message_has_error': False, 'message_has_error_counter': 0,
#  'message_attachment_count': 0, 'rating_ids': [],
#  'website_message_ids': [], 'message_has_sms_error': False,
#  'access_url': '/my/orders/6', 'access_token': False,
#  'access_warning': '', 'name': 'S00006', 'company_id': (1, 'My Company (San Francisco)'),
#  'partner_id': (15, 'Lumber Inc'), 'state': 'sale', 'locked': False,
#  'client_order_ref': False, 'create_date': datetime.datetime(2024, 3, 25, 2, 50, 20, 606529),
#  'commitment_date': False, 'date_order': datetime.datetime(2024, 3, 25, 2, 50, 24),
#  'origin': False, 'reference': False, 'require_signature': True, 'require_payment': True,
#  'prepayment_percent': 1.0, 'signature': False, 'signed_by': False, 'signed_on': False,
#  'validity_date': datetime.date(2024, 4, 24), 'journal_id': False, 'note': False,
#  'partner_invoice_id': (15, 'Lumber Inc'), 'partner_shipping_id': (15, 'Lumber Inc'),
#  'fiscal_position_id': False, 'payment_term_id': False, 'pricelist_id': False,
#  'currency_id': (1, 'USD'), 'currency_rate': 1.0, 'user_id': (2, 'Mitchell Admin'),
#  'team_id': (5, 'Pre-Sales'), 'order_line': [13], 'amount_untaxed': 750.0,
#  'amount_tax': 112.5, 'amount_total': 862.5, 'amount_to_invoice': 862.5,
#  'amount_invoiced': 0.0, 'invoice_count': 0, 'invoice_ids': [], 'invoice_status': 'no',
#  'transaction_ids': [], 'authorized_transaction_ids': [], 'amount_paid': 0.0,
#  'analytic_account_id': False, 'tag_ids': [6], 'amount_undiscounted': 750.0,
#  'country_code': 'US', 'expected_date': datetime.datetime(2024, 3, 25, 2, 50, 24),
#  'is_expired': False, 'partner_credit_warning': '',
#  'tax_calculation_rounding_method': 'round_per_line',
#  'tax_country_id': (233, 'United States'),
#  'tax_totals': {'amount_untaxed': 750.0, 'amount_total': 862.5, 'formatted_amount_total': '$\xa0862.50',
#                 'formatted_amount_untaxed': '$\xa0750.00',
#                 'groups_by_subtotal': defaultdict(<class 'list'>,
#                                                   {'Untaxed Amount': [{'group_key': 1, 'tax_group_id': 1, 'tax_group_name': 'Tax 15%', 'tax_group_amount': 112.5, 'tax_group_base_amount': 750.0, 'formatted_tax_group_amount': '$\xa0112.50', 'formatted_tax_group_base_amount': '$\xa0750.00'
#                                                                        }
#                                                                       ]
#                                                    }
#                                                   )
#                 , 'subtotals': [{'name': 'Untaxed Amount', 'amount': 750.0, 'formatted_amount': '$\xa0750.00'}],
#                 'subtotals_order': ['Untaxed Amount'], 'display_tax_base': False},
#  'terms_type': 'html', 'type_name': 'Sales Order', 'show_update_fpos': False,
#  'has_active_pricelist': True, 'show_update_pricelist': False,
#  'display_name': 'S00006', 'create_uid': (1, 'OdooBot'),
#  'write_uid': (2, 'Mitchell Admin'), 'write_date': datetime.datetime(2024, 4, 2, 5, 25, 45, 387401),
#  'carrier_id': False, 'delivery_message': False, 'delivery_rating_success': False, 'delivery_set': False,
#  'recompute_delivery_price': False, 'is_all_service': False, 'shipping_weight': 0.01, 'sale_order_template_id': False,
#  'sale_order_option_ids': [], 'incoterm': False, 'incoterm_location': False, 'picking_policy': 'direct',
#  'warehouse_id': (1, 'YourCompany'), 'picking_ids': [], 'delivery_count': 0, 'delivery_status': False,
#  'procurement_group_id': False, 'effective_date': False,
#  'json_popover': '{"popoverTemplate": "sale_stock.DelayAlertWidget", "late_elements": []}',
#  'show_json_popover': False, 'website_order_line': [13], 'cart_quantity': 1, 'only_services': False,
#  'is_abandoned_cart': False,'cart_recovery_email_sent': False, 'website_id': False, 'shop_warning': False,
#  'amount_delivery': 0.0, 'access_point_address': False, 'carrier_price': 0.0, 'delivery_type': False,
#  'create_package': 'auto',
#  'wk_packaging_ids': []}


# Order_line
# {'id': [13], 'analytic_distribution': [False],
#  'analytic_distribution_search': [False],
#  'analytic_precision': [2],
#  'order_id': [(6, 'S00006')], 'sequence': [10],
#  'company_id': [(1, 'My Company (San Francisco)')],
#  'currency_id': [(1, 'USD')],
#  'order_partner_id': [(15, 'Lumber Inc')],
#  'salesman_id': [(2, 'Mitchell Admin')],
#  'state': ['sale'], 'tax_country_id': [(233, 'United States')],
#  'display_type': [False], 'is_downpayment': [False],
#  'is_expense': [False],
#  'product_id': [(12, '[FURN_0096] Customizable Desk (Steel, White)')],
#  'product_template_id': [(9, 'Customizable Desk')], 'product_uom_category_id': [(1, 'Unit')], 'product_custom_attribute_value_ids': [[]], 'product_no_variant_attribute_value_ids': [[]], 'name': ['[FURN_0096] Customizable Desk (Steel, White)\n160x80cm, with large legs.'], 'product_uom_qty': [5.0], 'product_uom': [(1, 'Units')], 'tax_id': [[1]], 'pricelist_item_id': [False], 'price_unit': [750.0], 'discount': [0.0], 'price_subtotal': [3750.0], 'price_tax': [562.5], 'price_total': [4312.5], 'price_reduce_taxexcl': [750.0], 'price_reduce_taxinc': [862.5], 'product_packaging_id': [False], 'product_packaging_qty': [0.0], 'customer_lead': [0.0], 'qty_delivered_method': ['manual'], 'qty_delivered': [0.0], 'qty_invoiced': [0.0], 'qty_to_invoice': [
#     0.0], 'analytic_line_ids': [[]], 'invoice_lines': [[]], 'invoice_status': ['no'], 'untaxed_amount_invoiced': [0.0],
#  'untaxed_amount_to_invoice': [0.0], 'product_type': ['product'], 'product_updatable': [False],
#  'product_uom_readonly': [True], 'tax_calculation_rounding_method': ['round_per_line'],
#  'display_name': ['S00006 - [FURN_0096] Customizable Desk (Steel, White) (Lumber Inc)'],
#  'create_uid': [(1, 'OdooBot')], 'create_date': [datetime.datetime(2024, 3, 25, 2, 50, 20, 606529)],
#  'write_uid': [(2, 'Mitchell Admin')], 'write_date': [datetime.datetime(2024, 4, 4, 1, 14, 31, 688700)],
#  'is_delivery': [False], 'product_qty': [5.0], 'recompute_delivery_price': [False],
#  'sale_order_option_ids': [[]], 'is_configurable_product': [True], 'product_template_attribute_value_ids': [[1, 3]],
#  'route_id': [False], 'move_ids': [[53]], 'virtual_available_at_date': [0.0],
#  'scheduled_date': [datetime.datetime(2024, 3, 25, 2, 50, 24)], 'forecast_expected_date': [False],
#  'free_qty_today': [5.0], 'qty_available_today': [5.0], 'warehouse_id': [(1, 'YourCompany')],
#  'qty_to_deliver': [5.0], 'is_mto': [False], 'display_qty_widget': [True], 'linked_line_id': [False],
#  'option_line_ids': [[]], 'name_short': ['Customizable Desk (Steel, White)'], 'shop_warning': [False]}
