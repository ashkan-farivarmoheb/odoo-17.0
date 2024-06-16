import ast
from .australia_post_repository import AustraliaPostRepository
from .australia_post_request import AustraliaPostRequest
from .australia_post_helper import AustraliaPostHelper

from odoo import fields, models, api, _
import json
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


# https://webkul.com/blog/odoo-australia-shipping-integration/
# https://www.youtube.com/watch?v=cNgw9HTTMOQ
# https://github.com/OCA/delivery-carrier/blob/6fdd81598a7f5ff0c031623ec6193d667f447b5a/delivery_tnt_oca/models/delivery_carrier.py#L125
# https://github.com/OCA/delivery-carrier/blob/6fdd81598a7f5ff0c031623ec6193d667f447b5a/delivery_tnt_oca/models/tnt_request.py#L39


class DeliveryCarrierAustraliaPost(models.Model):
    _inherit = "delivery.carrier"

    australia_post_api_key = fields.Char(string="Australia Post API Key")
    australia_post_account_number = fields.Char(
        string="Australia Post Account Number")
    australia_post_api_password = fields.Char(
        string="Australia Post API Password", groups="base.group_system"
    )
    # australia_post_environment = fields.Selection([
    #     ('test_environment', 'Testing'),
    #     ('prod_environment', 'Production')
    # ], string="Environment", default='test_environment', help="Select the environment for Australia Post API.")

    delivery_type = fields.Selection(
        selection_add=[("auspost", "Australia Post")], ondelete={"auspost": "cascade"}
    )
    # Auspost  service type
    service_type = fields.Char(string="Type", readonly=True)
    service_product_id = fields.Char(string="Code", readonly=True)
    service_group = fields.Char(string="Group", readonly=True)

    tracking_link = fields.Char(
        string="Tracking Link",
        help="Tracking link(URL) useful to track the "
        "shipment or package from this URL.",
        size=256,
        default="https://auspost.com.au/mypost/track/#/details",
    )
    mail_template_id = fields.Many2one(
        "mail.template",
        "E-mail Template",
        help="choose mail template, default template is 'Shipping: Send by Email'",
        default=lambda self: self.env.ref(
            "stock.mail_template_data_delivery_confirmation"
        ).id,
    )

    is_automatic_shipment_mail = fields.Boolean(
        "Automatic Send Shipment Confirmation Mail",
        help="True: Send the shipment confirmation email to customer "
        "when tracking number is available.",
    )
    is_zip_required = fields.Boolean(
        "Is Zip Required?", help="mark as false if zip not required then.", default=True
    )

    authority_leave = fields.Boolean(
        string="Authority to Leave",
        help="Allow delivery without recipient signature.",
        default=False,
        copy=False,
    )
    allow_part_delivery = fields.Boolean(
        string="Allow Partial Delivery",
        help="Permit the delivery of orders in multiple shipments.",
        default=False,
        copy=False,
    )

    commercial_value = fields.Boolean(
        string="Commercial Value",
        help="Declare the value of goods for customs purposes.",
        default=False,
        copy=False,
    )
    classification_type = fields.Selection(
        [
            ("GIFT", "GIFT"),
            ("SAMPLE", "SAMPLE"),
            ("DOCUMENT", "DOCUMENT"),
            ("RETURN", "RETURN"),
            ("SALE_OF_GOODS", "SALE_OF_GOODS"),
        ],
        string="Classification Type",
        help="Category or classification of the goods.",
        default="DOCUMENT",
        copy=False,
    )

    # Label Setting fields
    label_layout_type = fields.Selection(
        [
            ("A4-1pp", "A4 - 1 page per sheet"),
            ("A4-2pp", "A4 - 2 pages per sheet"),
            ("A4-3pp", "A4 - 3 pages per sheet"),
            ("A4-4pp", "A4 - 4 pages per sheet"),
            ("A6-1pp", "A6 - 1 page per sheet"),
            ("Thermal-A6-1pp", "Thermal - A6 1 page per sheet"),
        ],
        string="Label Layout Type",
        help="Specifies the size and format of the printed label.",
    )
    branded = fields.Boolean(
        string="Branded Label",
        help="Use branded labels for shipments.",
        default=False,
        copy=False,
    )
    left_offset = fields.Float(
        string="Left Offset (mm)",
        help="Horizontal offset for label printing.",
        default=0.0,
        copy=False,
    )
    top_offset = fields.Float(
        string="Top Offset (mm)",
        help="Vertical offset for label printing.",
        default=0.0,
        copy=False,
    )

    auto_create_batch = fields.Boolean(
        string="Auto Create Batch",
        default=False,
        copy=False,
        help="If Auto Create Batch Is True Then Automatically " "Create The Batch.",
    )

    batch_limit = fields.Integer("Delivery Order Limit In Batch", default=100)

    auto_done_pickings = fields.Boolean(
        string="Auto Validate Delivery Orders",
        default=False,
        copy=False,
        help="True: Validate All Delivery Orders in Batch. "
        "False: User has to validate the batch manually.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Batch Responsible",
        help="Responsible person to process the batch",
    )

    _australia_post_repository_instance = None

    @api.onchange('delivery_type')
    def _onchange_delivery_type(self):
        """
        Automatically set the delivery_uom field to 'kg' when delivery_type is 'aus'.
        This provides real-time feedback in the form view.
        """
        if self.delivery_type == 'auspost':
            # self.delivery_uom = self._get_default_uom().name
            self.uom_id = self.env.ref('uom.product_uom_kgm')

    @api.model
    def create(self, vals):
        """
        Override the create method to set delivery_uom to 'kg' when delivery_type is 'aus'.

        @param vals: dict of values used to create the new record
        @return: newly created record
        """
        if vals.get('delivery_type') == 'auspost':
            vals['uom_id'] = self.env.ref('uom.product_uom_kgm').id
        return super(DeliveryCarrierAustraliaPost, self).create(vals)

    @api.model
    def write(self, vals):
        """
        Override the write method to set delivery_uom to 'kg' when delivery_type is 'aus'.

        @param vals: dict of values used to update the record
        @return: result of the parent class's write method
        """
        if 'delivery_type' in vals and vals['delivery_type'] == 'aus':
            vals['delivery_uom'] = 'kg'
        return super(DeliveryCarrierAustraliaPost, self).write(vals)

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

    def auspost_rate_shipment(self, order):
        """Calculate the shipping rate with Australia Post for a given order.

        :param order: The sale.order record
        :return: A dictionary containing the shipment rate and other details.
        """

        _logger.debug("auspost_rate_shipment")
        if not self.service_product_id:
            # service_product_id is not set, raise a UserError to notify the user
            raise UserError(
                _(
                    "The Australia Post Service Code is not configured in the Shipping Method settings. Please specify it before proceeding."
                )
            )

        try:
            australia_post_request = (
                self._get_australia_post_request()
            )  # self is the carrier

            rate_data = australia_post_request.create_rate_shipment_request(self,
                                                                            order
                                                                            )
            _logger.debug("auspost_rate_shipment :%s ", rate_data)

        except Exception as e:
            _logger.error(f"Error preparing shipping rates request: {str(e)}")
            return {"success": False, "error": str(e)}

        self.ensure_one()
        res = self._get_australia_post_repository().get_item_prices(
            source=rate_data["source"],
            destination=rate_data["destination"],
            items=rate_data["items"],
            carrier=self.read()[0],
        )

        if not res.get("data"):
            raise UserError(_("No account data returned from Australia Post."))
            # Create the wizard with the fetched data
        data = res["data"]
        if self.validate_shipment_rate(data):
            return {
                "success": res.get("success"),
                "price": self.get_price_by_product_id(data, self.service_product_id),
                "error_message": False,
                "warning_message": False,
            }

        else:
            errors = data.get("errors", [])
            if errors:
                error = errors[0]  # Taking first error from the list
                code = error.get("code", "No code provided")
                message = error.get("message", "No message provided")
                raise UserError(
                    _("Getting information wasn't successful. %s: %s" %
                      (code, message))
                )
            else:
                raise UserError(
                    _("Unknown error occurred while fetching shipping rates.")
                )

    def auspost_send_shipping(self, pickings):
        return [self.australia_post_create_shipping(p) for p in pickings][0]

    def _get_tracking_link(self, tracking_ref):
        _logger.debug("get_tracking_link %s   %s",
                      tracking_ref, self.tracking_link)

        base_url = (
            self.tracking_link.rstrip("/")
            if self.tracking_link
            else "https://auspost.com.au/mypost/track/#/details"
        )
        _logger.debug("get_tracking_link base_url %s", base_url)

        return f"{base_url}/{tracking_ref}" if tracking_ref and base_url else False

    def auspost_get_tracking_link(self, picking):
        return self._get_tracking_link(picking.carrier_tracking_ref)

    def auspost_cancel_shipment(self, picking):
        old_picking_carrier_tracking_refs = picking.carrier_tracking_ref
        if not old_picking_carrier_tracking_refs:
            raise UserError("carrier_tracking_ref is empty or invalid.")
        try:
            old_picking_carrier_tracking_refs = (
                ast.literal_eval(picking.carrier_tracking_ref)
                if picking.carrier_tracking_ref
                else False
            )
        except (ValueError, SyntaxError):
            if old_picking_carrier_tracking_refs == picking.carrier_tracking_ref:
                # single tracking ref Exists
                _logger.debug("auspost_cancel_shipment")
                try:
                    carrier = self.env["delivery.carrier"].search(
                        [("id", "=", picking.carrier_id.id)]
                    )
                    carrier.ensure_one()
                    carrier_record = carrier.read()[0]
                    res = self._get_australia_post_repository().delete_shipment(
                        [picking.shipment_id], carrier_record
                    )

                    if res.get("success"):
                        # Update the stock.quant.package model record
                        package = picking.package_ids
                        package.write({"tracking_no": False})

                except UserError as e:
                    raise e
                except Exception as e:
                    _logger.error("Failed to cancel shipment: %s", e)
                    raise UserError(
                        "There was a problem cancelling the shipment. Please try again later."
                    )

                return {"success": res.get("success")}
            else:
                raise UserError(
                    "carrier_tracking_ref is not a valid list or matching single string."
                )

        if isinstance(old_picking_carrier_tracking_refs, list):
            raise UserError(
                "There are multiple packages/tracking numbers. Please go to the packages and cancel them individually."
            )

    def australia_post_create_shipping(self, picking):
        res = []
        _logger.debug("australia_post_create_shipping")

        try:
            payload = json.dumps(
                self._get_australia_post_request().create_post_shipment_request(picking)
            )
            response = self._get_australia_post_repository().create_shipment(
                payload, picking.carrier_id.read()[0]
            )

            if not response.get("data"):
                raise UserError(
                    _("No shipments data returned from Australia Post."))
            # Process each shipment in the response
            for shipment in response.get("data", {}).get("shipments", []):
                picking.shipment_id = shipment.get("shipment_id")
                _logger.debug(
                    "australia_post_create_shipping for shipment %s",
                    picking.shipment_id,
                )
                items = shipment.get("items", [])
                _logger.debug(
                    "australia_post_create_shipping forssssssssssssssssss    items %s",
                    items,
                )

                if items:
                    # Create a list of dictionaries for each item's tracking details and exact price
                    for item in items:
                        item_info = {
                            "picking_id": picking.id,
                            "item_id": item["item_id"],
                            "item_reference": item["item_reference"],
                            "tracking_number": item["tracking_details"]["article_id"],
                            "exact_price": item["item_summary"]["total_cost"],
                        }
                        res.append(item_info)

            # _logger.debug(
            #             "australia_post_create_shipping Shipping response: %s", res)

        except UserError as e:
            raise e
        except Exception as e:
            _logger.error("Failed to create shipment: %s", e)
            raise UserError(
                _("There was a problem creating a shipment. Please try again later.")
            )
        return res

    @api.model
    def australia_post_get_account_info(self, carrier):

        carrier_record = self.env["delivery.carrier"].browse(carrier[0])
        carrier_record.ensure_one()
        carrier_record = carrier_record.read()[0]

        try:
            res = self.get_account_info(carrier_record)
            data = res.get("data")
            # Create the wizard with the fetched data
            info_wizard = AustraliaPostHelper.map_to_wizard_info(data)
            account_info_record = self.get_account_by_account_number(
                info_wizard["account_number"]
            )
            if not account_info_record:
                wizard = self.env["australia.post.account.info.wizard"].create(
                    info_wizard
                )
            else:
                wizard = account_info_record

            info_lines = AustraliaPostHelper.map_to_wizard_lines(
                data["postage_products"], wizard.id, carrier_record["id"]
            )

            existing_records = self.get_info_lines(wizard)
            self.update_or_insert_info_lines(existing_records, info_lines)
            # Remove records not present in info_lines
            self.remove_info_lines(existing_records, info_lines)

        except UserError as e:
            raise e
        except Exception as e:
            _logger.error("Failed to fetch account info: %s", e)
            raise UserError(
                _(
                    "There was a problem fetching the account information. Please try again later."
                )
            )

        # Return action to open the wizard
        return {
            "name": "Australia Post Account Info",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "australia.post.account.info.wizard",
            "target": "new",
            "res_id": wizard.id,
        }

    def remove_info_lines(self, existing_records, info_lines):
        records_to_remove = existing_records - existing_records.filtered(
            lambda r: r.product_id in [line["product_id"]
                                       for line in info_lines]
        )
        records_to_remove.unlink()

    def update_or_insert_info_lines(self, existing_records, info_lines):
        for line in info_lines:
            existing_record = existing_records.filtered(
                lambda r: r.product_id == line["product_id"]
            )
            if existing_record:
                existing_record.write(line)
            else:
                self.env["australia.post.account.info.line"].create(line)

    def get_info_lines(self, wizard):
        return self.env["australia.post.account.info.line"].search(
            [("wizard_id", "=", wizard.id)]
        )

    def get_account_by_account_number(self, account_number):
        return self.env["australia.post.account.info.wizard"].search(
            [("account_number", "=", account_number)]
        )

    def get_account_info(self, carrier_record):
        res = self._get_australia_post_repository().get_account(carrier_record)
        if not res.get("data"):
            raise UserError(_("No account data returned from Australia Post."))
        return res

    def get_price_by_product_id(self, res, product_id):
        # Assume res_json is obtained from res.json() where res is an instance of a response class
        for item in res["items"]:
            for price_info in item["prices"]:
                if price_info["product_id"] == product_id:
                    return price_info["calculated_price"]
        return None  # Return None if product_id is not found

    def validate_shipment_rate(self, data):
        return data and len(data["items"]) > 0 and data["items"][0]["prices"]
