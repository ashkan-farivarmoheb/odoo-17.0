from .australia_post_repository import AustraliaPostRepository
from .australia_post_request import AustraliaPostRequest

from odoo import fields, models, _
import json
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockPickingAustraliaPost(models.Model):
    _inherit = 'stock.picking'
    shipment_id = fields.Char(string="Shipment Id", size=256)

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

    def send_to_shipper(self):
        if self.batch_id:
            _logger.debug('the StockPicking %s is included in %s', self.id, self.batch_id.id)
        super().send_to_shipper()

    def button_validate(self):
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
