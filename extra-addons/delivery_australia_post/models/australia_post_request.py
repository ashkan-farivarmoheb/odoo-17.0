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
    def get_instance(cls, order):
        if cls._instance is None:
            cls._instance = cls(order)
        return cls._instance

    def __init__(self, order):
        self.order = order

        _logger.debug(
            'Initializing AustraliaPostRequest with order: %s', self.order)

        pass

    def _partner_to_shipping_data(self, partner):
        return {
            "country": partner.country_id.code or "AU",
            "suburb": partner.city,
            "postcode": partner.zip,
        }

    def _prepare_product(self):
        # height = max(order.default_packaging_id.height, 0.01)
        # width = max(order.default_packaging_id.width, 0.01)
        # p_length = max(order.default_packaging_id.packaging_length, 0.01)

        _logger.debug('Preparing product details for order: %s',
                      self.order.name)

        return [{
            'length': "5",
            'width': "10",
            'height': "1",
            'weight': self.order.shipping_weight,
        }]

    def _prepare_rate_shipment_data(self):
        _logger.debug('Preparing rate shipment data for order: %s',
                      self.order.name)
        return {
            "rateId": self.order.name,
            "source": self._partner_to_shipping_data(
                self.order.warehouse_id.partner_id
                or self.order.company_id.partner_id
            ),
            "destination": self._partner_to_shipping_data(
                self.order.partner_shipping_id
            ),
            "collectionDateTime": self.order.expected_date,
            "items": self._prepare_product(),
            "currency": self.order.currency_id.name,
        }
