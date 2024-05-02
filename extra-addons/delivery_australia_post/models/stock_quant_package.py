"""
Emipro Technologies Private Limited
Author : Vatsal Dharek : vatasld@emiprotechnologies.com
"""
# -*- coding: utf-8 -*-
from odoo import fields, models


class QuantPackage(models.Model):
    """
    Adding Tracking number field to Stock.Quant.package
    """
    _inherit = "stock.quant.package"

    tracking_no = fields.Char(string="Tracking Number",
                              help="In packages, Indicates all tracking number as per provider")
