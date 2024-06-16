import json
import logging
import re
from itertools import groupby, chain
from functools import reduce
from odoo.tools import config

from .australia_post_helper import AustraliaPostHelper

_logger = logging.getLogger(__name__)

parcels_size = int(config.options.get("services_austpost_label_parcelssize", 50))

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

    def create_post_labels_batch_request(self, pickings):
        packages = [package_id for picking in pickings for package_id in picking.package_ids]
        group_by_carrier = self._group_by_carrier(packages)

        # Aggregate results with carrier's id as the key
        label_reqs = reduce(
            lambda acc, carrier_label_reqs: {
                **acc,
                **{carrier: acc.get(carrier, []) + carrier_label_reqs[carrier] for carrier in carrier_label_reqs}
            },
            map(self._create_label_requests_for_service_type, group_by_carrier.items()),
            {}
        )

        return label_reqs

    def _create_label_requests_for_service_type(self, service_type_item):
        carrier, packages = service_type_item
        split_packages = [packages[i:i + parcels_size]
                          for i in range(0, len(packages), parcels_size)]
        carrier.ensure_one()

        return {
            carrier: [self._create_label_request(carrier, pkgs) for pkgs in split_packages]
        }

    def _create_label_request(self, carrier, packages):
        preferences = [self._create_label_preferences(
            AustraliaPostHelper.map_pickings_to_preferences(carrier))]

        group_by_shipments = {
            k: list(v) for k, v in groupby(
                sorted(packages, key=lambda package: package.picking_id.shipment_id),
                key=lambda package: package.picking_id.shipment_id
            )
        }

        shipments = list(map(self._get_label_shipment, group_by_shipments.items()))

        return json.dumps({
            "wait_for_label_url": True,
            "unlabelled_articles_only": False,
            "preferences": preferences,
            "shipments": shipments
        })

    def _get_label_shipment(self, shipment_packages_item):
        shipment, packages = shipment_packages_item
        return {
            "shipment_id": shipment,
            "items": self._get_item_ids(packages)
        }

    def _group_by_carrier(self, packages):
        return {
            k: list(v) for k, v in groupby(
                sorted(packages, key=lambda package: package.picking_id.carrier_id),
                key=lambda package: package.picking_id.carrier_id
            )
        }

    def _create_label_group(self, metadata):
        return {
            "group": metadata["group"],
            "layout": metadata["layout"],
            "branded": metadata["branded"],
            "left_offset": metadata["left_offset"],
            "top_offset": metadata["top_offset"]
        }

    def _create_label_preferences(self, preference):
        return {
            "type": preference["type"],
            "format": preference["format"],
            "groups": [self._create_label_group(preference["metadata"])]
        }

    def _get_item_ids(self, packages):
        return list(map(lambda package: {"item_id": package.item_id}, packages))
