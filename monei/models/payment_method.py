from odoo import fields, models, api
from ..graphql.queries import PAYMENT_METHODS_QUERY
from ..services.api_service import MoneiAPIService

class MoneiPaymentMethod(models.TransientModel):
    _name = 'monei.payment.method'
    _description = 'MONEI Payment Method'
    _rec_name = 'display_name'

    code = fields.Char(string='Code', readonly=True)
    configured = fields.Boolean(string='Configured', readonly=True)
    enabled = fields.Boolean(string='Enabled', readonly=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('code')
    def _compute_display_name(self):
        """Convert payment method code to display name"""
        method_names = {
            'card': 'Credit Card',
            'alipay': 'Alipay',
            'bancontact': 'Bancontact',
            'bizum': 'Bizum',
            'cofidis': 'Cofidis',
            'cofidisLoan': 'Cofidis Loan',
            'mbway': 'MB WAY',
            'multibanco': 'Multibanco',
            'paypal': 'PayPal',
            'sepa': 'SEPA'
        }
        for method in self:
            method.display_name = method_names.get(method.code, method.code.replace('_', ' ').title())

    @api.model
    def get_payment_methods(self):
        """Fetch payment methods from MONEI API"""
        api_service = MoneiAPIService(self.env)
        response = api_service.execute_query(PAYMENT_METHODS_QUERY)
        
        self.search([]).unlink()  # Clear existing records
        
        payment_methods = self.env['monei.payment.method']  # Empty recordset
        if response.get('data', {}).get('availablePaymentMethods'):
            for method in response['data']['availablePaymentMethods']:
                # Only create records for configured and enabled methods
                if method.get('configured') and method.get('enabled'):
                    payment_methods |= self.create({
                        'code': method['paymentMethod'],
                        'configured': method['configured'],
                        'enabled': method['enabled'],
                    })
        
        return payment_methods  # Return recordset instead of list 