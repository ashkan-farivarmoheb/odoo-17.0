# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ADVAITH BG (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

{
    'name': 'Theme Silon',
    'version': '17.0.1.0.0',
    'category': 'Theme/eCommerce',
    'summary': 'Attractive and unique front-end theme for eCommerce websites',
    'description': 'Attractive and unique front-end theme for eCommerce websites',
    'author': 'FG',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['web', 'website', 'website_mass_mailing', 'website_sale_wishlist'],
    'data': [
        'data/silon_configuration_data.xml',
        'security/ir.model.access.csv',
        'views/silon_configuration_views.xml',
        'views/snippets/index/most_popular_templates.xml',
        'views/snippets/index/banner_templates.xml',
        'views/snippets/index/offer_templates.xml',
        'views/snippets/index/features_templates.xml',
        'views/snippets/index/features_templates_2.xml',
        'views/snippets/index/parallax_card_templates.xml',
        'views/snippets/index/sticky_onScroll_templates.xml',
        'views/snippets/index/stacked_cards_templates.xml',
        'views/snippets/index/carousal_cards_templates.xml',
        'views/snippets/index/continues_carousal_cards_templates.xml',
        'views/snippets/index/journals_templates.xml',
        'views/snippets/index/follow_us_templates.xml',
        'views/snippets/about_us/about_us_templates.xml',
        'views/snippets/index/featured_products_templates.xml',
        'views/snippets/index/trending_templates.xml',
        'views/snippets/index/type_effect_title_template.xml',
        'views/megamenu_template.xml',
        'views/footer_templates.xml',
        'views/header_templates.xml',
        'views/contact_us_templates.xml',
        'views/cart_templates.xml',
        'views/product_templates.xml',
        'views/products_templates.xml',
        'views/layout_templates.xml',

    ],
    'assets': {
        'web._assets_primary_variables': [
            "theme_silon/static/src/scss/primary_variables.scss",
        ],
        'web.assets_frontend': [
            'theme_silon/static/src/css/font-awesome.min.css',
            'theme_silon/static/src/scss/_variables.scss',
            'theme_silon/static/src/scss/_normalize.scss',
            'theme_silon/static/src/scss/_common.scss',
            'theme_silon/static/src/scss/components/_buttons.scss',
            'theme_silon/static/src/scss/layout/_header.scss',
            'theme_silon/static/src/scss/layout/_footer.scss',
            'theme_silon/static/src/scss/layout/_navigation.scss',
            'theme_silon/static/src/scss/components/_banner.scss',
            'theme_silon/static/src/scss/components/_product.scss',
            'theme_silon/static/src/scss/pages/home/_offers.scss',
            'theme_silon/static/src/scss/pages/home/_features.scss',
            'theme_silon/static/src/scss/pages/home/_features_2.scss',
            'theme_silon/static/src/scss/pages/home/_sticky-onScroll.scss',
            'theme_silon/static/src/scss/pages/home/_stacked-cards.scss',
            'theme_silon/static/src/scss/pages/home/_continues-carousal-cards.scss',
            'theme_silon/static/src/scss/pages/home/_parallax-card.scss',
            'theme_silon/static/src/scss/pages/home/_type_effect.scss',
            'theme_silon/static/src/scss/pages/odoo-erp/s_tabs.scss',
            'theme_silon/static/src/scss/pages/home/_journal.scss',
            'theme_silon/static/src/scss/pages/home/_trending.scss',
            'theme_silon/static/src/scss/pages/home/_follow-us.scss',
            'theme_silon/static/src/scss/pages/home/_most-popular.scss',
            'theme_silon/static/src/scss/pages/_maincontents.scss',
            'theme_silon/static/src/scss/pages/_product.scss',
            'theme_silon/static/src/scss/pages/_about.scss',
            'theme_silon/static/src/scss/pages/_preview.scss',
            'theme_silon/static/src/scss/pages/_contact.scss',
            'theme_silon/static/src/scss/pages/_cart.scss',
            'theme_silon/static/src/js/most_popular.js',
            'theme_silon/static/src/js/featured_product.js',
            'theme_silon/static/src/js/trending.js',
            'theme_silon/static/src/js/parallax-effect.js',
            'theme_silon/static/src/js/type_effect.js',
            'theme_silon/static/src/js/continues_carousal_cards.js',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
