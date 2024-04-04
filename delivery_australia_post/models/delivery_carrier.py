import requests
from odoo import fields, models, api
import logging
from odoo.exceptions import UserError
# https://webkul.com/blog/odoo-australia-shipping-integration/
_logger = logging.getLogger(__name__)

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
        ('standard', 'Standard Post'),
        ('express', 'Express Post'),
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

    def australia_post_rate_shipment(self, order):
        """Calculate the shipping rate with Australia Post for a given order.

         :param order: The sale.order record
         :return: A dictionary containing the shipment rate and other details.
         """

        res = {
            'success': True,
            'price': 10.00,  # Example fixed price
            'error_message': False,
            'warning_message': False,
        }
        total_weight = order.shipping_weight

        _logger.debug(
            " Australia post Shippping module rate_shipment for order %s ", res)
        _logger.debug(
            "   order.shipping_weight:%s ", total_weight)

        # Placeholder: Implement the API call to Australia Post here
        # Example return structure
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
        """Cancel the shipment with Australia Post.

        Args:
            picking: The stock.picking record for which to cancel the shipment.

        Returns:
            A dictionary indicating the success or failure of the cancellation.
        """
        # Implement actual cancellation logic with Australia Post's API
        # This is a placeholder example
        return {'success': True}

    def _australia_post_get_default_custom_package_code(self):
        """Returns a default package code for custom implementations.

        Returns:
            A string representing the default package code.
        """
        # Implement as needed for Australia Post specifics
        return 'DEFAULT_CODE'

    @api.model
    def australia_post_get_account_info(self, *args, **kwargs):
        # Placeholder for the API call
        try:
            # response = requests.get("your_api_endpoint", auth=("your_username", "your_password"))
            # response.raise_for_status()  # This will raise an exception for HTTP error responses
            # api_data = response.json()
            api_data = {
                'acc_hold': 'Account Holder Example',
                'name': 'Example Name',
                'validdate': '2024-01-01',
                'accNum': '123456789',
                'AccTo': '2025-01-01',
                # Assuming you have a list of dicts for the table part
                'table': [{'name': 'Item 1', 'code': 'Code 1', 'available_service_type': 'Dispatch'}, {'name': 'Item 2', 'code': 'Code 2', 'available_service_type': 'Return'}]
            }

        # Create the wizard with the fetched data
            wizard = self.env['australia.post.account.info.wizard'].create({
                'title': 'Account Info',
                'account_holder': api_data['acc_hold'],
                'name': api_data['name'],
                'valid_from': api_data['validdate'],
                'account_number': api_data['accNum'],
                'valid_to': api_data['AccTo'],
                'table_ids': [(0, 0, line) for line in api_data['table']]
            })
        except UserError as e:
            # Handle expected model-specific errors
            raise
        except Exception as e:
            # Handle unexpected errors, possibly logging them and giving a user-friendly message
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
