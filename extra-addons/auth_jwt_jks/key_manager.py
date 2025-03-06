from odoo import models, api
from . import JKSProvider
from odoo.tools import config

class KeyManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(KeyManager, cls).__new__(cls)
            cls._instance.initialize_keys()
        return cls._instance

    def initialize_keys(self):
        self.jks_provider = JKSProvider(config.options)
        self.public_key = self.jks_provider.load_public_key_from_jks()
        self.private_key = self.jks_provider.load_private_key_from_jks()

    def get_public_key(self):
        return self.public_key

    def get_private_key(self):
        return self.private_key
