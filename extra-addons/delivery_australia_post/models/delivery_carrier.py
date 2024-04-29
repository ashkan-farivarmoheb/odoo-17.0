from .australia_post_repository import AustraliaPostRepository
from .australia_post_request import AustraliaPostRequest
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

    delivery_type = fields.Selection(selection_add=[
        ('australia_post', 'Australia Post')
    ], ondelete={'australia_post': 'cascade'})
    # Auspost  service type
    service_type = fields.Char(string='Type', readonly=True)
    service_product_id = fields.Char(string='Code', readonly=True)
    service_group = fields.Char(
        string='Group', readonly=True)

# TODO: functions of these need to be reviewed and tested
    tracking_link = fields.Char(string="Tracking Link",
                                help="Tracking link(URL) useful to track the "
                                     "shipment or package from this URL.",
                                size=256)
    mail_template_id = fields.Many2one('mail.template', 'E-mail Template',
                                       help="choose mail template ",
                                       #    default=lambda self: self.env.ref('delivery_australia_post.email_template_shipment_tracking_ept').id)
                                       )

    is_automatic_shipment_mail = fields.Boolean('Automatic Send Shipment Confirmation Mail',
                                                help="True: Send the shipment confirmation email to customer "
                                                     "when tracking number is available.")
    is_zip_required = fields.Boolean('Is Zip Required?',
                                     help="mark as false if zip not required then.",
                                     default=True)

    authority_leave = fields.Boolean(
        string="Authority to Leave",
        help="Allow delivery without recipient signature.",
        default=False,
        copy=False
    )
    allow_part_delivery = fields.Boolean(
        string="Allow Partial Delivery",
        help="Permit the delivery of orders in multiple shipments.",
        default=False,
        copy=False
    )
    email_tracking = fields.Boolean(
        string="Email Tracking Enabled",
        help="Send tracking information to customers via email.",
        default=False,
        copy=False
    )
    stock_package_type_id = fields.Many2one('stock.package.type',
                                            string="Package Type",
                                            help="Type of packaging used for delivery.",
                                            copy=False,
                                            )
    commercial_value = fields.Boolean(
        string="Commercial Value",
        help="Declare the value of goods for customs purposes.",
        default=False,
        copy=False
    )
    classification_type = fields.Selection([
        ('GIFT', 'GIFT'),
        ('SAMPLE', 'SAMPLE'),
        ('DOCUMENT', 'DOCUMENT'),
        ('RETURN', 'RETURN'),
        ('SALE_OF_GOODS', 'SALE_OF_GOODS')
    ],
        string="Classification Type",
        help="Category or classification of the goods.",
        default='DOCUMENT',
        copy=False
    )

    # Label Setting fields
    label_layout_type = fields.Selection([
        ('A4-1pp', 'A4 - 1 page per sheet'),
        ('A4-2pp', 'A4 - 2 pages per sheet'),
        ('A4-3pp', 'A4 - 3 pages per sheet'),
        ('A4-4pp', 'A4 - 4 pages per sheet'),
        ('A6-1pp', 'A6 - 1 page per sheet'),
        ('Thermal-A6-1pp', 'Thermal - A6 1 page per sheet')
    ], string="Label Layout Type", help="Specifies the size and format of the printed label.")
    branded = fields.Boolean(
        string="Branded Label",
        help="Use branded labels for shipments.",
        default=False,
        copy=False
    )
    left_offset = fields.Float(
        string="Left Offset (mm)",
        help="Horizontal offset for label printing.",
        default=0.0,
        copy=False
    )
    top_offset = fields.Float(
        string="Top Offset (mm)",
        help="Vertical offset for label printing.",
        default=0.0,
        copy=False
    )

    auto_create_batch = fields.Boolean(string="Auto Create Batch",
                                       default=False,
                                       copy=False,
                                       help="If Auto Create Batch Is True Then Automatically "
                                            "Create The Batch.")

    @api.onchange('auto_create_batch')
    def _on_change_auto_create_batch(self):
        cron = self.env.ref(
            'delivery_carrier.auto_create_batch_picking') or False
        if cron and not cron.active and self.auto_create_batch:
            cron.active = True

    batch_limit = fields.Integer('Delivery Order Limit In Batch', default=100)

    auto_done_pickings = fields.Boolean(string="Auto Validate Delivery Orders",
                                        default=False,
                                        copy=False,
                                        help="True: Validate All Delivery Orders in Batch. "
                                             "False: User has to validate the batch manually.")
    user_id = fields.Many2one('res.users',
                              string='Batch Responsible',
                              help='Responsible person to process the batch')
    use_existing_batch_cronjob = fields.Boolean(string="Use Existing Batch",
                                                default=False,
                                                copy=False,
                                                help="""True: Delivery orders will be added to existing batch in
                                                draft state for carrier.
                                                False: New batch will be created every time and all the
                                                delivery order will be added to new Batch.""")

# TODO: functions of above need to be reviewed and tested
    _australia_post_repository_instance = None

    @classmethod
    def _get_australia_post_repository(cls):
        if cls._australia_post_repository_instance is None:
            cls._australia_post_repository_instance = AustraliaPostRepository.get_instance(
            )
        return cls._australia_post_repository_instance

    _australia_post_request_instance = None

    @classmethod
    def _get_australia_post_request(cls):
        """Retrieve or create an instance of AustraliaPostRequest with order and carrier details."""
        if cls._australia_post_request_instance is None:
            cls._australia_post_request_instance = AustraliaPostRequest.get_instance()
        return cls._australia_post_request_instance

    def australia_post_rate_shipment(self, order):
        """Calculate the shipping rate with Australia Post for a given order.

         :param order: The sale.order record
         :return: A dictionary containing the shipment rate and other details.
         """
        try:
            australia_post_request = self._get_australia_post_request()  # self is the carrier

            rate_data = australia_post_request.create_rate_shipment_request(order, self.service_product_id)
            _logger.debug('rate_data -------%s ', rate_data)

        except Exception as e:
            # Log the error and handle appropriately
            print(f"Error preparing shipping rates request: {str(e)}")
            return {'success': False, 'error': str(e)}

        if not self.service_product_id:
            # service_product_id is not set, raise a UserError to notify the user
            raise UserError(
                _("The Australia Post Service Code is not configured in the Shipping Method settings. Please specify it before proceeding."))

        self.ensure_one()
        res = self._get_australia_post_repository().get_item_prices(
            source=rate_data['source'],
            destination=rate_data['destination'],
            items=rate_data['items'],
            carrier=self.read()[0]  # self is the carrier
        )
        _logger.debug('data -------%s ', res)
        if not res.get('data'):
            raise UserError(
                _("No account data returned from Australia Post."))
            # Create the wizard with the fetched data
        data = res['data']
        _logger.debug('data -------%s ', data)
        if self.validate_shipment_rate(data):
            return {
                "success": res.get('success'),
                "price":  self.get_price_by_product_id(
                    data, self.service_product_id),
                "error_message": False,
                "warning_message": False,
            }

        else:
            errors = data.get('errors', [])
            if errors:
                error = errors[0]  # Taking first error from the list
                code = error.get('code', "No code provided")
                message = error.get('message', "No message provided")
                raise UserError(
                    _("Getting information wasn't successful. %s: %s" % (code, message)))
            else:
                raise UserError(
                    _("Unknown error occurred while fetching shipping rates."))

    def australia_post_send_shipping(self, pickings):
        return [self.australia_post_create_shipping(p) for p in pickings]

    def australia_post_create_shipping(self, picking):
        res = None
        try:
            payload = self._get_australia_post_request().create_post_shipment_request(picking, self.email_tracking, self.allow_part_delivery, self.authority_leave)
            response = self._get_australia_post_repository().create_shipment(payload, picking.carrier_id.read()[0])
            if not response.get('data'):
                raise UserError(
                    _("No shipments data returned from Australia Post."))
            for shipment in response.get('data')['shipments']:
                picking.shipment_id = shipment['shipment_id']
                if len(shipment['items']) > 0:
                    res = {
                        "exact_price": shipment['shipment_summary']['total_cost'],
                        'tracking_number': shipment['items'][0]['tracking_details']['article_id'] if shipment['items'][0]['tracking_details'] else ''
                    }
        except UserError as e:
            raise e
        except Exception as e:
            _logger.error("Failed to create shipment: %s", e)
            raise UserError(
                "There was a problem creating a shipment. Please try again later.")
        return res

    def australia_post_get_tracking_link(self, picking):
        """Generate a tracking link for the customer.

        Args:
            picking: The stock.picking record for which to generate a tracking link.

        Returns:
            A string containing the URL to track the shipment.
        """

        base_url = self.tracking_link.rstrip(
            '/') if self.tracking_link else 'https://auspost.com.au/mypost/track/#/details'

        # Example tracking link, replace with real URL format provided by Australia Post

        return f'{base_url}/{picking.carrier_tracking_ref}'

    def australia_post_cancel_shipment(self, picking):

        try:
            carrier = self.env['delivery.carrier'].search(
                [('id', '=', picking.carrier_id.id)])
            carrier.ensure_one()
            carrier_record = carrier.read()[0]
            res = self._get_australia_post_repository().delete_shipment(
                [picking.shipment_id], carrier_record)
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
            account_info_record = self.get_account_by_account_number(
                info_wizard['account_number'])
            if not account_info_record:
                wizard = self.env['australia.post.account.info.wizard'].create(
                    info_wizard)
            else:
                wizard = account_info_record

            info_lines = AustraliaPostHelper.map_to_wizard_lines(
                data['postage_products'], wizard.id, carrier_record['id'])

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
            existing_record = existing_records.filtered(
                lambda r: r.product_id == line['product_id'])
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

    def get_price_by_product_id(self, res, product_id):
        # Assume res_json is obtained from res.json() where res is an instance of a response class
        for item in res['items']:
            for price_info in item['prices']:
                if price_info['product_id'] == product_id:
                    return price_info['calculated_price']
        return None  # Return None if product_id is not found

    def validate_shipment_rate(self, data):
        return (data and len(data['items']) > 0
                and data['items'][0]['prices'])
