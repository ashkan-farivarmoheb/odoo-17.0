from odoo import models, fields


class AusPostPackageType(models.Model):
    _inherit = 'stock.package.type'

    # Extend the existing selection
    package_carrier_type = fields.Selection(
        selection_add=[
            ('auspost', 'auspost')
        ]
    )
