from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..graphql.mutations import CREATE_PAYMENT_MUTATION
from ..services.api_service import MoneiAPIService
from datetime import datetime, timedelta
from time import mktime, sleep
import re

class MoneiPaymentCreateWizard(models.TransientModel):
    _name = 'monei.payment.create.wizard'
    _description = 'MONEI Create Payment Wizard'
    _inherit = ['monei.mixin']

    sale_order_id = fields.Many2one(
        'sale.order',
        string='Order ID',
        domain=[('state', 'in', ['sale', 'done'])],
    )
    
    amount = fields.Float(string='Amount', required=True)
    currency = fields.Selection([
        ('EUR', 'EUR'),
    ], string='Currency', required=True, default='EUR')
    
    payment_methods = fields.Many2many(
        'monei.payment.method',
        string='Allowed Payment Methods',
        required=True
    )
    
    expiration_date = fields.Date(
        string='Expiration Date',
        required=True,
        default=lambda self: fields.Date.today() + timedelta(days=7)
    )
    manual_capture = fields.Boolean(string='Manual Capture', default=False)
    
    customer_name = fields.Char(string='Customer Name')
    customer_email = fields.Char(string='Customer Email')
    customer_phone = fields.Char(string='Customer Phone')

    description = fields.Text(string='Description')
    
    billing_country = fields.Char(string='Billing Country')
    billing_state = fields.Char(string='Billing State')
    billing_city = fields.Char(string='Billing City')
    billing_zip = fields.Char(string='Billing Zip')
    billing_address = fields.Char(string='Billing Address')

    shipping_country = fields.Char(string='Shipping Country')
    shipping_state = fields.Char(string='Shipping State')
    shipping_city = fields.Char(string='Shipping City')
    shipping_zip = fields.Char(string='Shipping Zip')
    shipping_address = fields.Char(string='Shipping Address')

    @api.constrains('amount')
    def _check_amount(self):
        for wizard in self:
            if wizard.amount <= 0:
                raise UserError(_('Amount must be positive'))

    @api.constrains('customer_email')
    def _check_email(self):
        """Validate email format"""
        for record in self:
            if record.customer_email:
                self._validate_email(record.customer_email, 'customer_email')

    @api.constrains('customer_phone')
    def _check_phone_format(self):
        """Validate phone number format"""
        for record in self:
            if record.customer_phone:
                self._validate_phone(record.customer_phone, 'customer_phone')

    def _date_to_timestamp(self, date):
        """Convert date to Unix timestamp"""
        if not date:
            return None
        # Convert date to datetime at end of day (23:59:59)
        dt = datetime.combine(date, datetime.max.time())
        return int(mktime(dt.timetuple()))

    def _wait_for_payment(self, payment_id, api_service, retries=10, delay=1):
        """
        Wait for payment to be available in the API
        Args:
            payment_id: Payment ID to check for
            api_service: API service instance
            retries: Number of retries left
            delay: Delay between retries in seconds
        Returns:
            bool: True if payment was found, False otherwise
        """
        if retries <= 0:
            return False

        check_query = """
        query Charge {
            charge(id: "%s") {
                id
            }
        }
        """ % payment_id

        try:
            check_response = api_service.execute_query(check_query)
            if check_response.get('data', {}).get('charge', {}).get('id'):
                return True
        except Exception:
            # Ignore errors during check and continue retrying
            pass

        sleep(delay)
        return self._wait_for_payment(payment_id, api_service, retries - 1, delay)

    def action_create(self):
        self.ensure_one()
        
        # Prepare customer details, only include if email is valid
        customer = None
        if self.customer_name or self.customer_email or self.customer_phone:
            customer = {}
            if self.customer_name:
                customer['name'] = self.customer_name
            if self.customer_email:
                customer['email'] = self._validate_email(self.customer_email, 'customer_email')
            if self.customer_phone:
                customer['phone'] = self._validate_phone(self.customer_phone, 'customer_phone')

        api_service = MoneiAPIService(self.env)
        variables = {
            'input': {
                'amount': int(round(self.amount * 100)),
                'currency': self.currency,
                'orderId': self.sale_order_id.name if self.sale_order_id else None,
                'description': self.description,
                'expireAt': self._date_to_timestamp(self.expiration_date),
                'allowedPaymentMethods': self.payment_methods.mapped('code'),
                'customer': customer,
                'billingDetails': {
                    'address': {
                        'country': self.billing_country,
                        'state': self.billing_state,
                        'city': self.billing_city,
                        'zip': self.billing_zip,
                        'line1': self.billing_address,
                    }
                } if self.billing_country or self.billing_state or self.billing_city or self.billing_zip or self.billing_address else None,
                'shippingDetails': {
                    'address': {
                        'country': self.shipping_country,
                        'state': self.shipping_state,
                        'city': self.shipping_city,
                        'zip': self.shipping_zip,
                        'line1': self.shipping_address,
                    }
                } if self.shipping_country or self.shipping_state or self.shipping_city or self.shipping_zip or self.shipping_address else None,
            }
        }
        
        # Add manual capture if enabled
        if self.manual_capture:
            variables['input']['transactionType'] = 'AUTH'
        
        # Remove None values from the input
        variables['input'] = {k: v for k, v in variables['input'].items() if v is not None}
        
        try:
            response = api_service.execute_mutation(CREATE_PAYMENT_MUTATION, variables)
            if response.get('data', {}).get('createPayment'):
                result = response['data']['createPayment']
                
                self._log_info(f"Create payment response: {result}")
                
                # Wait for payment to be available
                payment_id = result.get('id')
                if payment_id:
                    if self._wait_for_payment(payment_id, api_service):
                        # Payment found, sync all payments
                        self.env['monei.payment'].action_sync_payments()
                        
                        # Find the created payment record
                        payment = self.env['monei.payment'].search([('name', '=', payment_id)], limit=1)
                        if payment:
                            # Open send link wizard
                            return {
                                'type': 'ir.actions.act_window',
                                'name': _('Send Payment Link'),
                                'res_model': 'monei.payment.send.link.wizard',
                                'view_mode': 'form',
                                'target': 'new',
                                'context': {
                                    'default_payment_id': payment.id,
                                    'default_customer_email': payment.customer_email or self.customer_email,
                                    'default_customer_phone': payment.customer_phone or self.customer_phone,
                                }
                            }
                    else:
                        # Payment not found after retries, show warning
                        return {
                            'name': _('MONEI Payments'),
                            'type': 'ir.actions.act_window',
                            'res_model': 'monei.payment',
                            'view_mode': 'tree,form',
                            'target': 'main',
                            'context': {
                                'notification': {
                                    'type': 'warning',
                                    'title': _('Warning'),
                                    'message': _('Payment created but automatic sync failed. Please refresh the payments manually.'),
                                    'sticky': True,
                                }
                            }
                        }
                
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
                            'message': _('Payment created successfully'),
                            'sticky': False,
                        }
                    }
                }
        except Exception as e:
            raise UserError(_('Failed to create payment: %s') % str(e)) 

    @api.onchange('sale_order_id')
    def _onchange_sale_order(self):
        """Update fields when sale order is selected"""
        if self.sale_order_id:
            partner = self.sale_order_id.partner_id
            self.amount = self.sale_order_id.amount_total
            
            # Update customer information
            self.customer_name = partner.name
            self.customer_email = partner.email
            self.customer_phone = partner.phone

            # Update billing information
            invoice_partner = self.sale_order_id.partner_invoice_id or partner
            self.billing_country = invoice_partner.country_id.code
            self.billing_state = invoice_partner.state_id.name
            self.billing_city = invoice_partner.city
            self.billing_zip = invoice_partner.zip
            self.billing_address = invoice_partner.street

            # Update shipping information
            delivery_partner = self.sale_order_id.partner_shipping_id or partner
            self.shipping_country = delivery_partner.country_id.code
            self.shipping_state = delivery_partner.state_id.name
            self.shipping_city = delivery_partner.city
            self.shipping_zip = delivery_partner.zip
            self.shipping_address = delivery_partner.street

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Get active_id from context (if coming from sale order)
        if self.env.context.get('active_model') == 'sale.order':
            sale_order = self.env['sale.order'].browse(self.env.context.get('active_id'))
            if sale_order:
                res['sale_order_id'] = sale_order.id
                
        if 'payment_methods' in fields_list:
            payment_methods = self.env['monei.payment.method'].get_payment_methods()
            res['payment_methods'] = [(6, 0, payment_methods.ids)]
        return res 