from ..graphql.mutations import REFUND_PAYMENT_MUTATION
from ..services.api_service import MoneiAPIService
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class MoneiPaymentRefundWizard(models.TransientModel):
    _name = 'monei.payment.refund.wizard'
    _description = 'MONEI Payment Refund Wizard'
    _inherit = ['monei.mixin']

    payment_id = fields.Many2one('monei.payment', string='Payment', required=True)
    amount = fields.Float(string='Amount', required=True)
    reason = fields.Selection([
        ('duplicated', 'Duplicated'),
        ('fraudulent', 'Fraudulent'),
        ('requested_by_customer', 'Requested by Customer'),
        ('order_canceled', 'Order Canceled')
    ], string='Reason')

    @api.constrains('amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise UserError(_('Amount must be positive'))
            if wizard.amount > (wizard.payment_id.amount - wizard.payment_id.refunded_amount):
                raise UserError(_('Cannot refund more than the remaining amount'))

    def action_refund(self):
        self.ensure_one()
        
        api_service = MoneiAPIService(self.env)
        variables = {
            'input': {
                'paymentId': self.payment_id.name,
                'amount': int(round(self.amount * 100)),
            }
        }
        
        if self.reason:
            variables['input']['refundReason'] = self.reason
        
        try:
            response = api_service.execute_mutation(REFUND_PAYMENT_MUTATION, variables)
            if response.get('data', {}).get('refundPayment'):
                result = response['data']['refundPayment']
                                
                # Safe conversion for amounts
                refunded_amount = result.get('refundedAmount')
                last_refund_amount = result.get('lastRefundAmount')
                
                # Safe handling of updatedAt
                updated_at = result.get('updatedAt')
                
                self.payment_id.write({
                    'status': result.get('status'),
                    'status_code': result.get('statusCode', ''),
                    'status_message': result.get('statusMessage', ''),
                    'refunded_amount': float(refunded_amount) / 100 if refunded_amount is not None else 0,
                    'last_refund_amount': float(last_refund_amount) / 100 if last_refund_amount is not None else 0,
                    'last_refund_reason': result.get('lastRefundReason') if result.get('lastRefundReason') is not None else '',
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
                            'message': _('Payment refunded successfully'),
                            'sticky': False,
                        }
                    }
                }
        except Exception as e:
            raise UserError(_('Failed to refund payment: %s') % str(e))