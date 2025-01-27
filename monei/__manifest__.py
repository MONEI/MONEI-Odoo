{
    'name': 'MONEI',
    'version': '1.0.0',
    'category': 'Accounting',
    'sequence': 350,
    'website': 'https://monei.com',
    'summary': 'MONEI Payment Data',
    'description': """MONEI Payment Data""",
    'depends': ['base', 'sale'],
    'data': [
        'security/ir.model.access.csv',
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
    'license': 'Other proprietary',
    'external_dependencies': {
        'python': ['requests'],
    },
    "images": ["static/description/banner.png"],
    'assets': {
        'web.assets_backend': [
            'monei/static/description/icon.png',
            'monei/static/src/css/payment_methods.css',
            'monei/static/src/img/payment_methods/*.svg',
        ],
    },
}