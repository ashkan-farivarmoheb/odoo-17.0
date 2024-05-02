from odoo import models, fields
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class AusPostPackageType(models.Model):
    _inherit = 'stock.package.type'

    # Extend the existing selection
    package_carrier_type = fields.Selection(
        selection_add=[
            ('auspost', 'auspost')
        ]
    )

    
