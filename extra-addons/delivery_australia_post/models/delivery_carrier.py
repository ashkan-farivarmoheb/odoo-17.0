from .australia_post_repository import AustraliaPostRepository
from .australia_post_helper import AustraliaPostHelper

from odoo import fields, models, api, _
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# https://webkul.com/blog/odoo-australia-shipping-integration/
# https://www.youtube.com/watch?v=cNgw9HTTMOQ
# https://github.com/OCA/delivery-carrier/blob/6fdd81598a7f5ff0c031623ec6193d667f447b5a/delivery_tnt_oca/models/delivery_carrier.py#L125
# https://github.com/OCA/delivery-carrier/blob/6fdd81598a7f5ff0c031623ec6193d667f447b5a/delivery_tnt_oca/models/tnt_request.py#L39


class DeliveryCarrierAustraliaPost(models.Model):
    _inherit = 'delivery.carrier'

    australia_post_api_key = fields.Char(string="Australia Post API Key")
    australia_post_account_number = fields.Char(
        string="Australia Post Account Number")
    australia_post_api_password = fields.Char(
        string="Australia Post API Password", groups="base.group_system")
    australia_post_environment = fields.Selection([
        ('test_environment', 'Testing'),
        ('prod_environment', 'Production')
    ], string="Environment", default='test_environment', help="Select the environment for Australia Post API.")

    australia_post_service_code = fields.Selection([
        ('AUS_PARCEL_REGULAR', 'Standard Post'),
        ('AUS_PARCEL_EXPRESS', 'Express Post'),
        # Add more service codes as necessary
    ], string="Service Code")
    australia_post_return_service_code = fields.Selection([
        ('standardReturn', 'Standard Post Returns'),
        ('expressReturn', 'Express Post Returns'),
        # Add more service codes as necessary
    ], string="Return Service Code")
    delivery_type = fields.Selection(selection_add=[
        ('australia_post', 'Australia Post')
    ], ondelete={'australia_post': 'cascade'})

    _australia_post_repository_instance = None

    @classmethod
    def _get_australia_post_repository(cls):
        if cls._australia_post_repository_instance is None:
            cls._australia_post_repository_instance = AustraliaPostRepository.get_instance()
        return cls._australia_post_repository_instance

    def australia_post_rate_shipment(self, order):
        """Calculate the shipping rate with Australia Post for a given order.

         :param order: The sale.order record
         :return: A dictionary containing the shipment rate and other details.
         """

        if not self.australia_post_service_code:
            # australia_post_service_code is not set, raise a UserError to notify the user
            raise UserError(
                _("The Australia Post Service Code is not configured in the Shipping Method settings. Please specify it before proceeding."))
        request = {
            'length': "5",
            'width': "10",
            'height': "1",
            'weight': order.shipping_weight,
            'from_postcode': order.warehouse_id.partner_id.zip,
            'to_postcode': order.partner_shipping_id.zip,
            'service_code': self.australia_post_service_code
        }

        res = self._get_australia_post_repository().get_shipping_rates(data=request)
        # _logger.debug(
        #     " Australia post Shippping module rate_shipment for order %s ", res)

        return res

    def australia_post_send_shipping(self, pickings):
        """Send the shipping information to Australia Post and return tracking numbers.

        Args:
            pickings: The stock.picking records for which to send shipping information.

        Returns:
            A list of dictionaries with picking and tracking information.
        """
        # Replace the following logic with actual communication with Australia Post's API.
        # This is a placeholder example.
        res = []
        for picking in pickings:
            # Simulated API call and response handling
            # This should be obtained from Australia Post's response
            tracking_number = 'AP123456789AU'
            res.append(
                {'exact_price': 10.0, 'tracking_number': tracking_number})
        return res

    def australia_post_get_tracking_link(self, picking):
        """Generate a tracking link for the customer.

        Args:
            picking: The stock.picking record for which to generate a tracking link.

        Returns:
            A string containing the URL to track the shipment.
        """
        # Example tracking link, replace with real URL format provided by Australia Post
        return 'https://auspost.com.au/mypost/track/#/details/{}'.format(picking.carrier_tracking_ref)


    def australia_post_cancel_shipment(self, picking):

        try:
            carrier = self.env['delivery.carrier'].search([('id', '=', picking.carrier_id.id)])
            carrier.ensure_one()
            carrier_record = carrier.read()[0]
            res = self._get_australia_post_repository().delete_shipment([picking.carrier_tracking_ref], carrier_record)
        except UserError as e:
            raise e
        except Exception as e:
            _logger.error("Failed to cancel shipment: %s", e)
            raise UserError(
                "There was a problem cancelling the shipment. Please try again later.")

        return {'success': res.get('success')}

    def _australia_post_get_default_custom_package_code(self):
        """Returns a default package code for custom implementations.

        Returns:
            A string representing the default package code.
        """
        # Implement as needed for Australia Post specifics
        return 'DEFAULT_CODE'

    @api.model
    def australia_post_get_account_info(self, carrier):

        carrier_record = self.env['delivery.carrier'].browse(carrier[0])
        carrier_record.ensure_one()
        carrier_record = carrier_record.read()[0]

        try:
            res = self.get_account_info(carrier_record)
            data = res.get('data')
            # Create the wizard with the fetched data
            info_wizard = AustraliaPostHelper.map_to_wizard_info(data)
            account_info_record = self.get_account_by_account_number(info_wizard['account_number'])
            if not account_info_record:
                wizard = self.env['australia.post.account.info.wizard'].create(info_wizard)
            else:
                wizard = account_info_record

            info_lines = AustraliaPostHelper.map_to_wizard_lines(data['postage_products'], wizard.id)

            existing_records = self.get_info_lines(wizard)
            self.update_or_insert_info_lines(existing_records, info_lines)
            # Remove records not present in info_lines
            self.remove_info_lines(existing_records, info_lines)

        except UserError as e:
            raise e
        except Exception as e:
            _logger.error("Failed to fetch account info: %s", e)
            raise UserError(
                "There was a problem fetching the account information. Please try again later.")

        # Return action to open the wizard
        return {
            'name': 'Australia Post Account Info',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'australia.post.account.info.wizard',
            'target': 'new',
            'res_id': wizard.id,
        }

    def remove_info_lines(self, existing_records, info_lines):
        records_to_remove = existing_records - existing_records.filtered(
            lambda r: r.product_id in [line['product_id'] for line in info_lines])
        records_to_remove.unlink()

    def update_or_insert_info_lines(self, existing_records, info_lines):
        for line in info_lines:
            existing_record = existing_records.filtered(lambda r: r.product_id == line['product_id'])
            if existing_record:
                existing_record.write(line)
            else:
                self.env['australia.post.account.info.line'].create(line)

    def get_info_lines(self, wizard):
        return self.env['australia.post.account.info.line'].search([('wizard_id', '=', wizard.id)])

    def get_account_by_account_number(self, account_number):
        return self.env['australia.post.account.info.wizard'].search(
            [('account_number', '=', account_number)])

    def get_account_info(self, carrier_record):
        res = self._get_australia_post_repository().get_account(carrier_record)
        if not res.get('data'):
            raise UserError(
                _("No account data returned from Australia Post."))
        return res
