from .australia_post_repository import AustraliaPostRepository
from .australia_post_request import AustraliaPostRequest

import json
from odoo.exceptions import ValidationError
from odoo import fields, models, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingAustraliaPost(models.Model):
    _inherit = 'stock.picking'
    shipment_id = fields.Char(string="Shipment Id", size=256)
    is_shipment_confirmation_send = fields.Boolean(
        'Shipment Confirmation Send')

    send_to_shipper_process_done = fields.Boolean(
        "Send To Shipper (Done).",
        copy=False,
        readonly=True,
        help="This field indicates that send to shipper " "for picking is done.",
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
            cls._australia_post_repository_instance = AustraliaPostRepository.get_instance(
            )
        return cls._australia_post_repository_instance

    def get_all_carriers(self):
        return ["auspost"]

    def _action_done(self):
        """
        Done pickings and make visible download button and send to shipper button based on
        condition.
        @return: return  response for done process
       """

        _logger.debug("Logging the StockPicking of self_: %s", self)
        res = False
        for picking in self:
            try:
                with self._cr.savepoint():
                    res = super(StockPickingAustraliaPost,
                                picking)._action_done()

            except Exception as e:
                message = "Delivery Order : %s Description : %s" % (
                    picking.name, e)
                picking.message_post(body=message)
                # if picking.batch_id:
                #     picking.batch_id.message_post(body=message)
                _logger.exception("Error while processing for send to Shipper - Picking : %s \n %s",
                                  picking.name, e)
                continue

            # TODO: when the batching implemented uncomment this
            if picking.carrier_tracking_ref and picking.batch_id:
                picking.send_to_shipper_process_done = True
            # if picking.carrier_tracking_ref:
            #     picking.send_to_shipper_process_done = True

        pickings_ready_for_download = self.filtered(
            lambda x: x.send_to_shipper_process_done)
        if pickings_ready_for_download:
            pickings_ready_for_download.mapped(
                'batch_id').ready_for_download = True

        return res

    def auto_shipment_confirm_mail(self):
        """
        Automatic send mail to the customer after placed order
        Note: should proper configuration in shipping instance required for
        send auto confirm mail.
        @return: return True if mail send successfully
        """
        _logger.debug('auto_shipment_confirm_mail %s   %s',
                      self.carrier_id, self.carrier_id.get_tracking_link)
        self.ensure_one()
        ctx = dict(self._context) or {}
        carrier = self.carrier_id if self.carrier_id else False
        if carrier:
            email_template = carrier.mail_template_id
            if not email_template:
                raise ValidationError(_(
                    'You must set the value of E-mail Template in Menu Settings >> Shipping Method.'))
            if self.carrier_id.get_tracking_link(self):
                tracking_link = self.carrier_id.get_tracking_link(self)
                _logger.debug('auto_shipment_confirm_mail2 %s   %s %s',
                              tracking_link, carrier, email_template)
                ctx.update(
                    {'tracking_link': tracking_link, 'force_send': True})
                self.with_context(ctx). \
                    message_post_with_source(email_template,
                                             email_layout_xmlid='mail.mail_notification_light')
                self.write({'is_shipment_confirmation_send': True})
            else:
                raise ValidationError(
                    _('Tracking Link are not available please contact your Administrator.'))
        return True

    def send_to_shipper(self):
        """
        Return send shipper dict if clicked Send Shipper Button else return none
        :return: Return send shipper dict if clicked Send Shipper Button else return none
        """

        self.ensure_one()
        avilable_carriers_list = self.get_all_wk_carriers()

        if self.carrier_id.delivery_type and (self.carrier_id.delivery_type not in ['base_on_rule', 'fixed']) and (self.carrier_id.delivery_type in avilable_carriers_list):
            if not self.batch_id and not len(self.package_ids):
                raise ValidationError(
                    'Create the package first for picking %s before sending to shipper.' % (self.name))
            else:
                # try:
                _logger.debug(
                    "send to shippppper base package_ids %s", self.package_ids)
                res = self.carrier_id.send_shipping(self)

                self.carrier_price = res.get('exact_price')
                self.carrier_tracking_ref = res.get(
                    'tracking_number', []) and res.get('tracking_number').strip(',')
                self.label_genrated = bool(self.carrier_tracking_ref)
                self.date_delivery = res.get('date_delivery')
                if res.get(
                        'weight'):
                    self.weight_shipment = float(res.get('weight'))

                msg = _("Shipment sent to carrier %s for expedition with tracking number %s") % (
                    self.carrier_id.delivery_type, self.carrier_tracking_ref)
                self.message_post(
                    body=msg,
                    subject="Attachments of tracking",
                    attachments=res.get('attachments')
                )
                # except Exception as e:
                #     return self.carrier_id._shipping_genrated_message(e)
        else:
            return super(StockPickingAustraliaPost, self).send_to_shipper()

        _logger.debug("send to shipper: %s", self)

        # res = super(StockPickingAustraliaPost, self).send_to_shipper()
        carrier = self.carrier_id or False
        if carrier and carrier.delivery_type and (carrier.delivery_type in ['auspost']) and carrier.is_automatic_shipment_mail:
            _logger.debug("is_automatic_shipment_mail is true")
            self.auto_shipment_confirm_mail()
        if self.package_ids:
            self.package_ids.write(
                {'tracking_no': self.carrier_tracking_ref, 'order_id': self.sale_id})
        return res

    def button_validate(self):
        if not self[0].carrier_id:
            raise ValidationError(
                _('Carrier is not specified for Stock Picking %s. please Choose a Carrier.', self.name))
        res = super().button_validate()
        if res is True and self.batch_id:
            payload = json.dumps(self._get_australia_post_request()
                                 .create_order_request(self.batch_id))
            if len(self) > 0:
                response = (self._get_australia_post_repository()
                            .create_order_shipments(payload, self[0].carrier_id.read()[0]))
                if not response.get('data'):
                    raise UserError(
                        _("No order data returned from Australia Post."))

                data = response.get('data')
                self.update_batch_details(self.batch_id, data)

        return res

    def update_batch_details(self, batch, data):
        batch.order_id = data['order']['order_id']
