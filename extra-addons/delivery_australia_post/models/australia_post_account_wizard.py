from odoo import models, fields, api
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class AustraliaPostAccountInfoWizard(models.TransientModel):
    _name = 'australia.post.account.info.wizard'
    _description = 'Australia Post Account Information'
    title = fields.Char(string='Title', readonly=True)
    name = fields.Char(string='Account Holder Name', readonly=True)
    valid_from = fields.Date(string='Valid From', readonly=True)
    account_number = fields.Char(string='Account Number', readonly=True)
    valid_to = fields.Date(string='Valid To', readonly=True)
    expired = fields.Boolean(string='Expired', readonly=True)
    merchant_location_id = fields.Char(
        string='Merchant Location Id', readonly=True)
    credit_blocked = fields.Boolean(string='Credit Blocked', readonly=True)

    # Example for the table, adjust according to your data structure
    # Consider creating another TransientModel for the table lines if it's a list of items
    table_ids = fields.One2many(
        'australia.post.account.info.line', 'wizard_id', string='Table',  readonly=True)

    _sql_constraints = [
        ('info_wizard_account_number_uk', 'UNIQUE(account_number)',
         'Account Number must be unique!')
    ]

    @api.constrains('account_number')
    def _check_unique_name(self):
        # Check uniqueness of 'name' field using Python constraint
        for record in self:
            if self.search([('account_number', '=', record.account_number), ('id', '!=', record.id)]):
                raise ValidationError("Duplicate Account Number")


class AustraliaPostAccountInfoLine(models.TransientModel):
    _name = 'australia.post.account.info.line'
    _description = 'Australia Post Account Information Line'

    wizard_id = fields.Many2one(
        'australia.post.account.info.wizard', string='Wizard', readonly=True)
    carrier = fields.Many2one(
        'delivery.carrier', string='Carrier', readonly=True)

    type = fields.Char(string='Type', readonly=True)
    product_id = fields.Char(string='Code', readonly=True)
    group = fields.Char(
        string='Group', readonly=True)

    def add_new_shipping_service(self):
        carrier_model = self.env['delivery.carrier']

        if self.carrier:
            carrier_record = carrier_model.browse(self.carrier)
            self.carrier.ensure_one()
            delivery_type_label = dict(self.carrier.fields_get(allfields=['delivery_type'])[
                                       'delivery_type']['selection'])[self.carrier.delivery_type]
            new_name = f"{delivery_type_label} ({self.type})"
            # new_name = f"{self.carrier.delivery_type} ({self.type})"
            self.carrier.write({
                'name': new_name,
                'service_group': self.group,
                'service_product_id': self.product_id,
                'service_type': self.type
            })
            _logger.debug("Carrier updated successfully for line %s", self.id)
        else:
            _logger.error(
                "No carrier ID found for service line ID: %s", self.id)
