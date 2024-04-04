from odoo import models, fields, api


class AustraliaPostAccountInfoWizard(models.TransientModel):
    _name = 'australia.post.account.info.wizard'
    _description = 'Australia Post Account Information'

    title = fields.Char(string='Title', readonly=True)
    account_holder = fields.Char(string='Account Holder', readonly=True)
    name = fields.Char(string='Name', readonly=True)
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
    name = fields.Char(string='Name', readonly=True)
    code = fields.Char(string='Code', readonly=True)
    available_service_type = fields.Char(
        string='Available Service Type', readonly=True)
