from odoo import models, fields, api


class AustraliaPostAccountInfoWizard(models.TransientModel):
    _name = 'australia.post.account.info.wizard'
    _description = 'Australia Post Account Information'

    title = fields.Char(string='Title', readonly=True)
    name = fields.Char(string='Account Holder Name', readonly=True)
    valid_from = fields.Date(string='Valid From', readonly=True)
    account_number = fields.Char(string='Account Number', readonly=True)
    valid_to = fields.Date(string='Valid To', readonly=True)

    # Example for the table, adjust according to your data structure
    # Consider creating another TransientModel for the table lines if it's a list of items
    table_ids = fields.One2many(
        'australia.post.account.info.line', 'wizard_id', string='Table',  readonly=True)


class AustraliaPostAccountInfoLine(models.TransientModel):
    _name = 'australia.post.account.info.line'
    _description = 'Australia Post Account Information Line'

    wizard_id = fields.Many2one(
        'australia.post.account.info.wizard', string='Wizard', readonly=True)
    type = fields.Char(string='Type', readonly=True)
    product_id = fields.Char(string='Code', readonly=True)
    group = fields.Char(
        string='Group', readonly=True)
