import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..graphql.mutations import SEND_PAYMENT_LINK_MUTATION
from ..services.api_service import MoneiAPIService

class MoneiPaymentSendLinkWizard(models.TransientModel):
    _name = 'monei.payment.send.link.wizard'
    _description = 'MONEI Send Payment Link Wizard'
    _inherit = ['monei.mixin']

    payment_id = fields.Many2one('monei.payment', string='Payment', required=True)
    channel = fields.Selection([
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
        ('SMS', 'SMS')
    ], string='Channel', required=True, default='EMAIL')
    notification_email = fields.Char(string='Send to Email')
    notification_phone = fields.Char(string='Send to Phone')
    language = fields.Selection([
        ('en', 'English'),
        ('es', 'Spanish'),
        ('ca', 'Catalan'),
        ('pt', 'Portuguese'),
        ('de', 'German'),
        ('it', 'Italian'),
        ('fr', 'French')
    ], string='Language', default='en')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get payment from context or active_id
        payment_id = self.env.context.get('default_payment_id') or self.env.context.get('active_id')
        if payment_id:
            payment = self.env['monei.payment'].browse(payment_id)
            if payment.exists():
                res.update({
                    'payment_id': payment.id,
                    'notification_email': self.env.context.get('default_notification_email') or payment.customer_email,
                    'notification_phone': self.env.context.get('default_notification_phone') or payment.customer_phone,
                })
        return res

    @api.constrains('channel', 'notification_email', 'notification_phone')
    def _check_contact_format(self):
        """Validate email and phone formats"""
        for record in self:
            if record.channel == 'EMAIL' and record.notification_email:
                self._validate_email(record.notification_email, 'notification_email')
            if record.channel in ['WHATSAPP', 'SMS'] and record.notification_phone:
                self._validate_phone(record.notification_phone, 'notification_phone')

    def action_send_link(self):
        self.ensure_one()

        # Validate channel requirements
        if self.channel == 'EMAIL':
            if not self.notification_email:
                raise UserError(_('Email is required for email channel'))
            clean_email = self._validate_email(self.notification_email, 'notification_email')
        elif self.channel in ['WHATSAPP', 'SMS']:
            if not self.notification_phone:
                raise UserError(_('Phone is required for %s channel') % self.channel.lower())
            clean_phone = self._validate_phone(self.notification_phone, 'notification_phone')

        api_service = MoneiAPIService(self.env)
        variables = {
            'input': {
                'paymentId': self.payment_id.name,
                'channel': self.channel,
                'language': self.language,
            }
        }

        if self.channel == 'EMAIL':
            variables['input']['customerEmail'] = clean_email
        elif self.channel in ['WHATSAPP', 'SMS']:
            variables['input']['customerPhone'] = clean_phone

        try:
            response = api_service.execute_mutation(SEND_PAYMENT_LINK_MUTATION, variables)
            if response.get('data', {}).get('sendPaymentLink'):
                return {
                    'name': _('MONEI Payments'),
                    'type': 'ir.actions.act_window',
                    'res_model': 'monei.payment',
                    'view_mode': 'tree,form',
                    'target': 'main',
                    'context': {
                        'notification': {
                            'type': 'success',
                            'title': _('Success'),
                            'message': _('Payment link sent successfully'),
                            'sticky': False,
                        }
                    }
                }
        except Exception as e:
            raise UserError(_('Failed to send payment link: %s') % str(e)) 