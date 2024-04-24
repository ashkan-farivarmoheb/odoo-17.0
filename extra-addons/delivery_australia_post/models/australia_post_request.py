import base64
import json
import logging
import re

import requests


from odoo import _, fields, tools
from odoo.exceptions import UserError

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

    def _prepare_product(self, order, service_product_id):
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

    def prepare_rate_shipment_data(self, order, service_product_id):
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
            "items": self._prepare_product(order, service_product_id),
            "currency": order.currency_id.name,
        }
