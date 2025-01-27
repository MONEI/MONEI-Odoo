from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..graphql.mutations import CANCEL_PAYMENT_MUTATION
from ..services.api_service import MoneiAPIService

class MoneiPaymentCancelWizard(models.TransientModel):
    _name = 'monei.payment.cancel.wizard'
    _description = 'MONEI Payment Cancel Wizard'
    _inherit = ['monei.mixin']

    payment_id = fields.Many2one('monei.payment', string='Payment', required=True)
    reason = fields.Selection([
        ('requested_by_customer', 'Requested by Customer'),
        ('fraudulent', 'Fraudulent'),
        ('duplicate', 'Duplicate'),
        ('order_canceled', 'Order Canceled')
    ], string='Reason')

    def action_cancel(self):
        self.ensure_one()
        api_service = MoneiAPIService(self.env)
        
        variables = {
            'input': {
                'paymentId': self.payment_id.name,
            }
        }
        
        # Only add cancellationReason if it's set
        if self.reason:
            variables['input']['cancellationReason'] = self.reason
        
        try:
            response = api_service.execute_mutation(CANCEL_PAYMENT_MUTATION, variables)
            if response.get('data', {}).get('cancelPayment'):
                result = response['data']['cancelPayment']
                
                # Safe handling of updatedAt
                updated_at = result.get('updatedAt')
                
                self.payment_id.write({
                    'status': result.get('status'),
                    'status_code': result.get('statusCode', ''),
                    'status_message': result.get('statusMessage', ''),
                    'cancellation_reason': result.get('cancellationReason'),
                    'updated_at': self._parse_datetime(updated_at) if updated_at else False,
                })
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'monei.payment',
                    'res_id': self.payment_id.id,
                    'view_mode': 'form',
                    'target': 'main',
                    'context': {
                        'notification': {
                            'type': 'success',
                            'title': _('Success'),
                            'message': _('Payment canceled successfully.'),
                            'sticky': False,
                        }
                    }
                }
        except Exception as e:
            raise UserError(_('Failed to cancel payment: %s') % str(e)) 