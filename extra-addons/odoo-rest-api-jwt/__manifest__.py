# -*- coding: utf-8 -*-
{
    'name': "odoo-rest-api-jwt",
    'summary': """
        Odoo REST API JWT Auth""",
    'description': """
        Odoo REST API JWT Auth
    """,

    'author': "FG",
    'category': 'developers,Tools',
    "version": "17.1",
    'depends': ['auth_jwt', 'base'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
    'external_dependencies': {
        'python': ['pypeg2']
    }
}
