import base64
import json
import logging
import re

import requests


from odoo import _, fields, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AustraliaPostRequest(object):
    def __init__(self, carrier, record):
        self.carrier = carrier
        self.record = record
        self.appVersion = 1.0



  
  
  
    def _partner_to_shipping_data(self, partner):
        return {
            "country": partner.country_id.code or "AU",
            "suburb": partner.city,
            "postcode": partner.zip,
        }
    def _prepare_product(self,order):
        height =  max(self.default_packaging_id.height , 0.01)
        width =max(self.default_packaging_id.width , 0.01   )
        p_length =max(self.default_packaging_id.packaging_length, 0.01)
        
        return {
            'length': p_length,
            'width': width,
            'height': height,
            'weight': order.shipping_weight,
            'product_id': order.service_product_id
        }


    def _prepare_rate_shipment_data(self,order):

        return {

                "rateId": self.record.name,
                "source": self._partner_to_shipping_data(
                    self.record.warehouse_id.partner_id
                    or self.record.company_id.partner_id
                ),
                "destination": self._partner_to_shipping_data(
                    self.record.partner_shipping_id
                ),
                "collectionDateTime": self.record.expected_date,
                "items": self._prepare_product(order),
                "currency": self.record.currency_id.name,
 
        }