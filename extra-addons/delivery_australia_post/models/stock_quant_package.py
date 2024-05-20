"""
Emipro Technologies Private Limited
Author : Vatsal Dharek : vatasld@emiprotechnologies.com
"""
# -*- coding: utf-8 -*-
from odoo import fields, models, _
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)
from ..decorator import implemented_by_carrier

class QuantPackage(models.Model):
    """
    Adding Tracking number field to Stock.Quant.package
    """
    _inherit = "stock.quant.package"

    tracking_no = fields.Char(string="Tracking Number",
                              help="In packages, Indicates all tracking number as per provider")
    item_id=fields.Char(string="Item Id", size=256)
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier")    
    # @implemented_by_carrier
    # def _get_tracking_link(self):
    #     pass
    
    
    def open_website_url(self):
        """Open website for parcel tracking.

        Each carrier should implement _get_tracking_link
        There is low chance you need to override this method.
        returns:
            action
        """
        self.ensure_one()
        base_url = self.tracking_link.rstrip(
            '/') if self.carrier_id.tracking_link else False
        
        
        url= f'{base_url}/{self.tracking_no}' if self.tracking_no else False
        
        if not base_url or not url:
            raise UserError(_("The tracking url is not available."))
        client_action = {
            "type": "ir.actions.act_url",
            "name": "Shipment Tracking Page",
            "target": "new",
            "url": url,
        }
        return client_action
    
    
    # def _get_tracking_link(self):
    #         """Build a tracking url.

    #         You have to implement it for your carrier.
    #         It's like :
    #             'https://the-carrier.com/?track=%s' % self.parcel_tracking
    #         returns:
    #             string (url)
    #         """
    #         self.carrier_id.get_tracking_link()
            
            
    #         _logger.warning("not implemented")