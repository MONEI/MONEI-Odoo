from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..graphql.mutations import CAPTURE_PAYMENT_MUTATION
from ..services.api_service import MoneiAPIService

class MoneiPaymentCaptureWizard(models.TransientModel):
    _name = 'monei.payment.capture.wizard'
    _description = 'MONEI Payment Capture Wizard'
    _inherit = ['monei.mixin']


    payment_id = fields.Many2one('monei.payment', string='Payment', required=True)
    amount = fields.Float(string='Amount')

    @api.constrains('amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.amount and wizard.amount <= 0:
                raise UserError(_('Amount must be positive'))
            if wizard.amount and wizard.amount > wizard.payment_id.amount:
                raise UserError(_('Cannot capture more than the authorized amount'))

    def action_capture(self):
        self.ensure_one()
        
        api_service = MoneiAPIService(self.env)
        variables = {
            'input': {
                'paymentId': self.payment_id.name,
            }
        }
        
        if self.amount:
            variables['input']['amount'] = int(round(self.amount * 100))
        
        response = api_service.execute_mutation(CAPTURE_PAYMENT_MUTATION, variables)
        
        if response.get('data', {}).get('capturePayment'):
            result = response['data']['capturePayment']
            
            self._log_info(f"Capture response: {result}")
            
            # Safe conversion for amount
            captured_amount = result.get('amount')
            updated_at = result.get('updatedAt')
            
            self.payment_id.write({
                'status': result.get('status'),
                'status_code': result.get('statusCode', ''),
                'status_message': result.get('statusMessage', ''),
                'captured_amount': float(captured_amount) / 100 if captured_amount is not None else 0,
                'updated_at': self._parse_datetime(updated_at) if updated_at else False,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Payment captured successfully'),
                    'type': 'success',
                }
            } 