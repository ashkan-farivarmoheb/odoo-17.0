# -*- coding: utf-8 -*-
from . import controllers
from . import models
from . import service
from . import utils

from odoo import models, api
from odoo.addons.auth_jwt_jks.key_manager import KeyManager

class RestfullApiJwt(models.Model):
    _name = 'restfull.api.jwt'

    @api.model
    def post_init(self):
        super(RestfullApiJwt, self).post_init()
        # Initialize KeyManager at startup
        KeyManager()  # This will initialize the keys
