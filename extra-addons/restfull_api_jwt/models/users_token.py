from  ..utils.models_name import ModelsName
from odoo import fields, models

class UsersToken(models.Model):
    _name = ModelsName.authUsersTokens
    # Replace with your module and model name

    # Add fields
    # type = fields.Char('type')
    type = fields.Char(string='Type')  # Added string parameter for the field label

    revoked = fields.Boolean(readonly=True, default=False)
    # user_id = fields.Many2one('res.users', int='User')
    user_id = fields.Many2one('res.users', string='User')  # Changed int to string for the field label


    def revoked_token(self):
        for rec in self:
            rec.revoked = True

    @staticmethod
    def toMap(user_id,type,revoked=False):
       return {'user_id':user_id,'type':type,'revoked':revoked}
