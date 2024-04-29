from .australia_post_helper import AustraliaPostHelper
import logging
import re
import json


_logger = logging.getLogger(__name__)


class AustraliaPostRequest(object):

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        pass

    def _partner_to_shipping_data(self, partner):
        return {
            "country": partner.country_id.code or "AU",
            "suburb": partner.city,
            "postcode": partner.zip,
        }

    def _prepare_rate_shipment_items(self, order, service_product_id):
        _logger.debug('Preparing product details for order: %s',
                      order.name)

        return [{
            'length': "5",
            'width': "10",
            'height': "1",
            'weight': order.shipping_weight,
            'item_reference': order.name,
            'product_ids': [service_product_id]
        }]

    def create_rate_shipment_request(self, order, service_product_id):
        _logger.debug('Preparing rate shipment data for order: %s',
                      order.name)
        return {
            "rateId": order.name,
            "source": self._partner_to_shipping_data(
                order.warehouse_id.partner_id
                or order.company_id.partner_id
            ),
            "destination": self._partner_to_shipping_data(
                order.partner_shipping_id
            ),
            "collectionDateTime": order.expected_date,
            "items": self._prepare_rate_shipment_items(order, service_product_id),
            "currency": order.currency_id.name,
        }

    def create_post_shipment_request(self, picking, email_tracking, allow_part_delivery, authority_leave):
        product_names = ", ".join([self._extract_product_name(move.product_id.product_tmpl_id.name) for move in picking.move_ids])
        shipment_request = {
            "shipment_reference": picking.sale_id.id,
            "customer_reference_1": picking.sale_id.name,
            "customer_reference_2": product_names,
            "email_tracking_enabled": email_tracking,
            "from": AustraliaPostHelper.map_res_partner_to_shipment(picking.sale_id.warehouse_id.partner_id),
            "to": AustraliaPostHelper.map_res_partner_to_shipment(picking.partner_id),
            "items": AustraliaPostHelper.map_shipment_items(picking, allow_part_delivery, authority_leave)
        }
        return json.dumps({"shipments": [shipment_request]})

    def _extract_product_name(self, name):
        extracted = name
        pattern = r'"en_US": "([^"]*)"'
        match = re.search(pattern, name)
        if match:
            extracted = match.group(1)
        return extracted

