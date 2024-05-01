{
    'name': 'Australia Post Shipping Integration',
    'version': '17.0.0.0',
    'summary': 'Integrate Australia Post shipping services with Odoo',
    'description': """Long description""",
    'author': 'FG',
    'category': 'Inventory/Delivery',
    'depends': ['odoo_shipping_service_apps', 'mail', 'contacts'],
    'data': [
        'views/delivery_carrier_views.xml',
        'views/delivery_carrier_extra_views.xml',
        'data/delivery_carrier_data.xml',
        'views/stock_picking_view.xml',
        'views/australia_post_account_wizard_view.xml',
        'security/ir.model.access.csv'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
