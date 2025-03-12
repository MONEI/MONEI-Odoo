{
    'name': 'MONEI',
    'author': 'MONEI',
    'version': '1.0.0',
    'category': 'Accounting',
    'sequence': 350,
    'website': 'https://monei.com',
    'summary': 'MONEI Payment Integration',
    'description': """
MONEI Payment Integration for Odoo
=================================
This module integrates MONEI payment services with Odoo.
    """,
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/res_config_views.xml',
        'views/send_link_wizard_views.xml',
        'views/sync_wizard_views.xml',
        'views/create_wizard_views.xml',
        'views/monei_payment_views.xml',
        'views/monei_menus.xml',
        'views/cancel_wizard_views.xml',
        'views/refund_wizard_views.xml',
        'views/capture_wizard_views.xml',
        'views/sale_order_views.xml',
    ],
    'application': True,
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'license': 'LGPL-3',
    'external_dependencies': {
        'python': ['requests'],
    },
    "images": ["static/description/banner.png"],
    'assets': {
        'web.assets_backend': [
            'monei/static/src/css/payment_methods.css',
            'monei/static/src/img/payment_methods/*.svg',
        ],
        'web.assets_common': [
            'monei/static/description/icon.png',
        ],
    },
}