from odoo.exceptions import ValidationError
from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPickingAustraliaPost(models.Model):
    _inherit = 'stock.picking'
    shipment_id = fields.Char(string="Shipment Id", size=256)
    is_shipment_confirmation_send = fields.Boolean(
        'Shipment Confirmation Send')

    send_to_shipper_process_done = fields.Boolean('Send To Shipper (Done).', copy=False,
                                                  readonly=True,
                                                  help="This field indicates that send to shipper "
                                                       "for picking is done.")

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
            # if picking.carrier_tracking_ref and picking.batch_id:
            #     picking.send_to_shipper_process_done = True
            if picking.carrier_tracking_ref:
                picking.send_to_shipper_process_done = True

        # pickings_ready_for_download = self.filtered(
        #     lambda x: x.send_to_shipper_process_done)
        # if pickings_ready_for_download:
        #     pickings_ready_for_download.mapped(
        #         'batch_id').ready_for_download = True

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
        shipping_instance = self.carrier_id if self.carrier_id else False
        if shipping_instance:
            email_template = shipping_instance.mail_template_id
            if not email_template:
                raise ValidationError(_(
                    'You must set the value of E-mail Template in Menu Settings >> Shipping Method.'))
            if self.carrier_id.get_tracking_link(self):
                tracking_link = self.carrier_id.get_tracking_link(self)
                _logger.debug('auto_shipment_confirm_mail2 %s   %s %s',
                              tracking_link, shipping_instance, email_template)
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
        _logger.debug("send to shippppper: %s", self)

        res = super().send_to_shipper()
        carrier = self.carrier_id or False
        if carrier and carrier.is_automatic_shipment_mail:
            _logger.debug("is_automatic_shipment_mail is true")
            self.auto_shipment_confirm_mail()
        if self.package_ids:
            self.package_ids.write({'tracking_no': self.carrier_tracking_ref})
        return res
