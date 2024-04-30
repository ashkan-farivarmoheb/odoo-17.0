from odoo import fields, models, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPickingAustraliaPost(models.Model):
    _inherit = 'stock.picking'
    shipment_id = fields.Char(string="Shipment Id", size=256)
