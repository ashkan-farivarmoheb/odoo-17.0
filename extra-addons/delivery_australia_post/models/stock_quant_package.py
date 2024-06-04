# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
import ast
from .australia_post_request import AustraliaPostRequest
from .australia_post_repository import AustraliaPostRepository
from odoo import fields, models, _, api
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QuantPackage(models.Model):
    """
    Adding Tracking number field to Stock.Quant.package
    """

    _inherit = "stock.quant.package"

    tracking_no = fields.Char(
        string="Tracking Number",
        help="In packages, Indicates all tracking number as per provider",
    )
    item_id = fields.Char(string="Item Id", size=256)
    picking_id = fields.Many2one("stock.picking", string="Picking")
    authority_leave = fields.Boolean(
        string="Authority to Leave",
        help="Allow delivery without recipient signature.",
        store=True,
        readonly=False
    )

    allow_part_delivery = fields.Boolean(
        string="Allow Partial Delivery",
        help="Permit the delivery of orders in multiple shipments.",
        store=True,
        readonly=False
    )

    @classmethod
    def _get_australia_post_repository(cls):
        if cls._australia_post_repository_instance is None:
            cls._australia_post_repository_instance = (
                AustraliaPostRepository.get_instance()
            )
        return cls._australia_post_repository_instance

    _australia_post_request_instance = None

    @classmethod
    def _get_australia_post_request(cls):
        """Retrieve or create an instance of AustraliaPostRequest with order and carrier details."""
        if cls._australia_post_request_instance is None:
            cls._australia_post_request_instance = AustraliaPostRequest.get_instance()
        return cls._australia_post_request_instance

    def open_website_url(self):
        """Open website for parcel tracking.

        Each carrier should implement _get_tracking_link
        There is low chance you need to override this method.
        returns:
            action
        """
        self.ensure_one()
        if self.picking_id.carrier_id.delivery_type == "auspost":
            url = self.picking_id.carrier_id._get_tracking_link(
                self.tracking_no)
        else:
            raise ValidationError(_("Shipping method is not AUSPOST"))

        if not url:
            raise UserError(_("The tracking url is not available."))
        client_action = {
            "type": "ir.actions.act_url",
            "name": "Shipment Tracking Page",
            "target": "new",
            "url": url,
        }
        return client_action

    def cancel_item(self):
        if self.tracking_no and self.picking_id.carrier_id.delivery_type == "auspost":
            _logger.debug("cancel_item")
            try:
                carrier = self.picking_id.carrier_id
                carrier.ensure_one()
                carrier_record = carrier.read()[0]
                old_picking_carrier_tracking_refs = self.picking_id.carrier_tracking_ref
                if not old_picking_carrier_tracking_refs:
                    raise UserError(
                        "carrier_tracking_ref is empty or invalid.")
                try:
                    old_picking_carrier_tracking_refs = (
                        ast.literal_eval(self.picking_id.carrier_tracking_ref)
                        if self.picking_id.carrier_tracking_ref
                        else False
                    )

                except (ValueError, SyntaxError):
                    if old_picking_carrier_tracking_refs == self.tracking_no:
                        _logger.debug(
                            "It is a single string matching the tracking number"
                        )
                        # Single tracking ref Exists
                        self.picking_id.cancel_shipment()
                    else:
                        raise UserError(
                            "carrier_tracking_ref is not a valid list or matching single string."
                        )

                # Multi tracking ref Exists
                if isinstance(old_picking_carrier_tracking_refs, list):
                    res = self._get_australia_post_repository().delete_item(
                        [self.picking_id.shipment_id], [
                            self.id], carrier_record
                    )
                    _logger.debug("its list now")

                    if res.get("success"):
                        old_picking_carrier_tracking_refs.remove(
                            self.tracking_no)
                        new_picking_carrier_tracking_refs = (
                            str(old_picking_carrier_tracking_refs)
                            if len(old_picking_carrier_tracking_refs) > 1
                            else (
                                old_picking_carrier_tracking_refs[0]
                                if len(old_picking_carrier_tracking_refs) == 1
                                else False
                            )
                        )

                        package_tracking_no = self.tracking_no

                        # Update the stock.quant.package model record
                        self.write({"tracking_no": False})

                        self.picking_id.write(
                            {"carrier_tracking_ref": new_picking_carrier_tracking_refs}
                        )

                        msg = f"Package {self.name} with tracking number {package_tracking_no} has been canceled"
                        self.picking_id.message_post(body=msg)

                        return {"success": res.get("success")}
                    else:
                        raise UserError(
                            "Failed to delete the item from the Australia Post repository."
                        )

            except UserError as e:
                raise e
            except Exception as e:
                _logger.error("Failed to cancel shipment: %s", e)
                raise UserError(
                    "There was a problem cancelling the shipment. Please try again later."
                )
        else:
            raise UserError(
                "There are no tracking number associated with this record.")
