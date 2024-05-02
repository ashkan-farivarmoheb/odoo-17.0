from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class StockPickingBatchAustraliaPost(models.Model):
    _inherit = "stock.picking.batch"
    order_id = fields.Char(string="Carrier Order Id", size=256)
