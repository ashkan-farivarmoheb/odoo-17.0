from .australia_post_repository import AustraliaPostRepository
from .australia_post_request import AustraliaPostRequest

import json
from odoo.exceptions import ValidationError
from odoo import fields, models, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingAustraliaPost(models.Model):
    _inherit = "stock.picking"
    shipment_id = fields.Char(string="Shipment Id", size=256)
    is_shipment_confirmation_send = fields.Boolean("Shipment Confirmation Send")

    send_to_shipper_process_done = fields.Boolean(
        "Send To Shipper (Done).",
        copy=False,
        readonly=True,
        help="This field indicates that send to shipper " "for picking is done.",
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

    _australia_post_request_instance = None
    _australia_post_repository_instance = None

    @classmethod
    def _get_australia_post_request(cls):
        """Retrieve or create an instance of AustraliaPostRequest with order and carrier details."""
        if cls._australia_post_request_instance is None:
            cls._australia_post_request_instance = AustraliaPostRequest.get_instance()
        return cls._australia_post_request_instance

    @classmethod
    def _get_australia_post_repository(cls):
        if cls._australia_post_repository_instance is None:
            cls._australia_post_repository_instance = (
                AustraliaPostRepository.get_instance()
            )
        return cls._australia_post_repository_instance

    def get_all_carriers(self):

        available_carriers = []
        new_carrier = ["auspost"]
        available_carriers.extend(new_carrier)
        return available_carriers

    def _action_done(self):
        """
        Done pickings and make visible download button and send to shipper button based on
        condition.
        @return: return  response for done process
        """
        avilable_carriers_list = self.get_all_wk_carriers()

        _logger.debug("Logging the StockPicking of self_: %s", self)
        res = False
        for picking in self:
            if self.carrier_id.delivery_type in avilable_carriers_list and not len(
                picking.package_ids
            ):
                raise UserError(
                    "Create the package first for picking %s before sending to shipper."
                    % (picking.name)
                )
            try:
                with self._cr.savepoint():
                    res = super(StockPickingAustraliaPost, picking)._action_done()

            except Exception as e:
                message = "Delivery Order : %s Description : %s" % (picking.name, e)
                picking.message_post(body=message)
                # if picking.batch_id:
                #     picking.batch_id.message_post(body=message)
                _logger.exception(
                    "Error while processing for send to Shipper - Picking : %s \n %s",
                    picking.name,
                    e,
                )
                continue

            # TODO: when the batching implemented uncomment this
            if picking.carrier_tracking_ref and picking.batch_id:
                picking.send_to_shipper_process_done = True
            # if picking.carrier_tracking_ref:
            #     picking.send_to_shipper_process_done = True

        pickings_ready_for_download = self.filtered(
            lambda x: x.send_to_shipper_process_done
        )
        if pickings_ready_for_download:
            pickings_ready_for_download.mapped("batch_id").ready_for_download = True

        return res

    def auto_shipment_confirm_mail(self):
        """
        Automatic send mail to the customer after placed order
        Note: should proper configuration in shipping instance required for
        send auto confirm mail.
        @return: return True if mail send successfully
        """
        _logger.debug(
            "auto_shipment_confirm_mail %s   %s",
            self.carrier_id,
            self.carrier_id.get_tracking_link,
        )
        self.ensure_one()
        ctx = dict(self._context) or {}
        carrier = self.carrier_id if self.carrier_id else False
        if carrier:
            email_template = carrier.mail_template_id
            if not email_template:
                raise ValidationError(
                    _(
                        "You must set the value of E-mail Template in Menu Settings >> Shipping Method."
                    )
                )
            if self.carrier_id.get_tracking_link(self):
                tracking_link = self.carrier_id.get_tracking_link(self)
                _logger.debug(
                    "auto_shipment_confirm_mail2 %s   %s %s",
                    tracking_link,
                    carrier,
                    email_template,
                )
                ctx.update({"tracking_link": tracking_link, "force_send": True})
                self.with_context(ctx).message_post_with_source(
                    email_template, email_layout_xmlid="mail.mail_notification_light"
                )
                self.write({"is_shipment_confirmation_send": True})
            else:
                raise ValidationError(
                    _(
                        "Tracking Link are not available please contact your Administrator."
                    )
                )
        return True

    def send_to_shipper(self):
        """
        Return send shipper dict if clicked Send Shipper Button else return none
        :return: Return send shipper dict if clicked Send Shipper Button else return none
        """

        self.ensure_one()
        available_carriers_list = self.get_all_carriers()
        packages = self.package_ids
        res = self.carrier_id.send_shipping(self)
        _logger.debug(
            "send to shippppper australiapost res:%s  ",
            self.carrier_id.send_shipping(self),
        )

        if (
            self.carrier_id.delivery_type in ["base_on_rule", "fixed"]
            or self.carrier_id.delivery_type not in available_carriers_list
        ):
            return super(StockPickingAustraliaPost, self).send_to_shipper()

        if not len(self.package_ids):
            raise ValidationError(
                "Create the package first for picking %s before sending to shipper."
                % (self.name)
            )

        _logger.debug("Sending to shipper base package_ids %s", self.package_ids)

        # if self.package_ids and len(res) != len(self.package_ids) :
        #     raise ValidationError("The number of shipping results does not match the number of packages.")

        _logger.debug("send to shippppper australiapost packages:%s  ", packages)

        carrier_tracking_refs = []

        if len(self.package_ids) > 0:
            if len(res) != len(self.package_ids):
                raise ValidationError(
                    "The number of shipping results does not match the number of packages."
                )
            # for package, ship_info in zip(self.package_ids, res):
            for package in self.package_ids:

                _logger.debug("send to shippppper australiapost res :%s  ", res)
                # Find the corresponding ship_info based on package.name
                ship_info = next(
                    (info for info in res if info["item_reference"] == package.name),
                    None,
                )

                if ship_info:
                    _logger.debug(
                        "send to shippppper australiapost pack:%s  ", ship_info
                    )

                    pack_tracking_number = ship_info.get("tracking_number", "").strip(
                        ","
                    )
                    carrier_tracking_refs.append(pack_tracking_number)

                    self.label_genrated = bool(self.carrier_tracking_ref)
                    # _logger.debug("send to shippppper australiapost package %s pack_tracking_number:%s  ",package,pack_tracking_number)

                    package.write(
                        {
                            "tracking_no": pack_tracking_number,
                            "order_id": self.sale_id.id if self.sale_id else False,
                            "picking_id": self.id,
                        },
                    )
                    msg = _(
                        "Shipment sent to carrier %s for expedition with tracking number %s"
                    ) % (self.carrier_id.delivery_type, pack_tracking_number)
                    if pack_tracking_number:
                        self.message_post(
                            body=msg,
                            subject="Attachments of tracking",
                            attachments=ship_info.get("attachments"),
                        )

                else:
                    raise ValidationError(
                        "No ship_info found for package with name %s." % (package.name)
                    )

                if ship_info and ship_info.get("weight"):
                    self.weight_shipment += float(ship_info.get("weight"))

            if carrier_tracking_refs:
                self.carrier_tracking_ref = (
                    carrier_tracking_refs[0]
                    if len(carrier_tracking_refs) == 1
                    else carrier_tracking_refs
                )

        else:
            # for index, item in enumerate(res):
            #     if item['picking_id'] == self.picking_id:
            #         res=res[index]
            res = [item for item in res if item["picking_id"] == self.id][0]

            self.carrier_tracking_ref = res.get("tracking_number", "")
            self.carrier_price = res.get("exact_price")
            self.label_genrated = bool(self.carrier_tracking_ref)
            self.date_delivery = res.get("date_delivery")
            if res.get("weight"):
                self.weight_shipment += float(res.get("weight"))

            _logger.debug(
                "send to shippppper australiapost shimpen_id:%s  ", self.shipment_id
            )

            msg = _(
                "Shipment sent to carrier %s for expedition with tracking number %s"
            ) % (self.carrier_id.delivery_type, self.carrier_tracking_ref)
            self.message_post(
                body=msg,
                subject="Attachments of tracking",
                attachments=res.get("attachments"),
            )

        carrier = self.carrier_id or False
        if carrier.is_automatic_shipment_mail:
            _logger.debug("is_automatic_shipment_mail is true")
            self.auto_shipment_confirm_mail()

        _logger.debug(
            "send to shippppper australiapost carrier_tracking_refs:%s  ",
            carrier_tracking_refs,
        )

        # except Exception as e:
        #     return self.carrier_id._shipping_genrated_message(e)

    def button_validate(self):
        available_carriers_list = self.get_all_carriers()

        if not self[0].carrier_id:
            raise ValidationError(
                _(
                    "Carrier is not specified for Stock Picking %s. please Choose a Carrier.",
                    self.name,
                )
            )
        try:
            res = super().button_validate()
            if (
                res
                and self.batch_id
                and (self.carrier_id.delivery_type in available_carriers_list)
            ):
                _logger.debug("button_validate request batch_id= %s", self.batch_id)

                payload = json.dumps(
                    self._get_australia_post_request().create_order_request(
                        self.batch_id
                    )
                )
                _logger.debug("button_validate payload= %s", payload)
                if len(self) > 0:
                    response = (
                        self._get_australia_post_repository().create_order_shipments(
                            payload, self[0].carrier_id.read()[0]
                        )
                    )
                    if not response.get("data"):
                        raise UserError(
                            _("No order data returned from Australia Post.")
                        )

                    data = response.get("data")
                    self.update_batch_details(self.batch_id, data)

            return res

        except UserError as e:
            raise e
        except Exception as e:
            _logger.error("Failed to create Order: %s", e)
            raise UserError(
                "There was a problem creating a Order. Please try again later."
            )

    def update_batch_details(self, batch, data):
        batch.order_id = data["order"]["order_id"]
        # if 'tracking_number' in data:
        #     batch.send_to_shipper_process_done = bool(data['shipments']['tracking_number'])
        #     batch.ready_for_download = bool(data['tracking_number'])

    def open_website_url(self):
        """Open tracking page.

        More than 1 tracking number: display a list of packages
        Else open directly the tracking page
        """
        self.ensure_one()
        avilable_carriers_list = self.get_all_carriers()

        if (
            self.carrier_id.delivery_type
            and (self.carrier_id.delivery_type not in ["base_on_rule", "fixed"])
            and (self.carrier_id.delivery_type in avilable_carriers_list)
        ):
            packages = self.package_ids
            if len(packages) == 0:
                raise UserError(_("No packages found for this picking"))
            if len(packages) == 1:
                return super().open_website_url()  # shortpath
            else:
                if not self._support_multi_tracking():
                    packages = packages[0]

            # display a list of pickings
            xmlid = "stock.action_package_view"
            action = self.env["ir.actions.act_window"]._for_xml_id(xmlid)
            action["domain"] = [("id", "in", packages.ids)]
            action["context"] = {"picking_id": self.id}
            return action
        else:
            return super().open_website_url()

    def _support_multi_tracking(self):
        # By default roulier carrier may have one tracking ref per pack.
        # override this method for your carrier if you always have a unique
        # tracking per picking
        return True

    def _roulier_generate_labels(self):
        """
        Return format expected by send_shipping : a list of dict (one dict per
        picking).
        {
            'exact_price': 0.0,
            'tracking_number': "concatenated numbers",
            'labels': list of dict of labels, managed by base_delivery_carrier_label
        }
        """
        label_info = []
        for picking in self:
            move_line_no_pack = picking.move_line_ids.filtered(
                lambda ml: ml.qty_done > 0.0 and not ml.result_package_id
            )
            if move_line_no_pack:
                raise UserError(
                    _(
                        "Some products have no destination package in picking %s, "
                        "please add a destination package in order to be able to "
                        "generate the carrier label."
                    )
                    % picking.name
                )
            label_info.append(picking.package_ids._generate_labels(picking))
        return label_info
