import logging
import re

from .australia_post_helper import AustraliaPostHelper

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

    def create_rate_shipment_request(self, carrier, order):
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
            "items": AustraliaPostHelper.map_rate_shipment_items(carrier,order),
            "currency": order.currency_id.name,
        }

    def create_post_shipment_request(self, picking):
        shipment_request = self._create_post_shipment_request(picking)
        return {"shipments": [shipment_request]}

    def create_order_including_shipments_request(self, batch):
        return {
            "order_reference": batch.name,
            "payment_method": "CHARGE_TO_ACCOUNT",
            "shipments": [self._create_post_shipment_request(p) for p in batch.picking_ids]
        }

    def create_order_request(self, batch):
        # TODO: for producttion the following need to be commented
        _logger.debug('create_order_request  batch []= %s ', batch)
        shipment_ids = []

        for p in batch.picking_ids:
            shipment_ids.append(p.shipment_id)
        _logger.debug('create_order_request  shipment_ids []= %s ', [
                      {"shipment_id": s} for s in shipment_ids])

# TODO: for producttion the following need to be uncommented
        shipment_ids = set()
        [shipment_ids.add(p.shipment_id) for p in batch.picking_ids]
        _logger.debug('create_order_request  shipment_ids set= %s ', [
                      {"shipment_id": s} for s in shipment_ids])
        return {
            "order_reference": batch.name,
            "payment_method": "CHARGE_TO_ACCOUNT",
            "shipments": [{"shipment_id": s} for s in shipment_ids]
        }

    def _extract_product_name(self, name):
        extracted = name
        pattern = r'"en_US": "([^"]*)"'
        match = re.search(pattern, name)
        if match:
            extracted = match.group(1)
        return extracted

    def _create_post_shipment_request(self, picking):
        product_names = ", ".join(
            [self._extract_product_name(move.product_id.product_tmpl_id.name) for move in picking.move_ids])
        shipment_request = {
            "shipment_reference": picking.id,
            "customer_reference_1": picking.sale_id.id,
            "customer_reference_2": product_names,
            "email_tracking_enabled": picking.is_automatic_shipment_mail if picking.is_automatic_shipment_mail and picking.partner_id.email else False,
            "from": AustraliaPostHelper.map_res_partner_to_shipment(picking.sale_id.warehouse_id.partner_id),
            "to": AustraliaPostHelper.map_res_partner_to_shipment(picking.partner_id),
            "items": AustraliaPostHelper.map_shipment_items(picking)
        }
        return shipment_request
