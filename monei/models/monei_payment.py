from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
import logging
from ..graphql.queries import CHARGE_QUERY, STORES_QUERY, CHARGES_QUERY
from ..services.api_service import MoneiAPIService
from markupsafe import Markup
from ..graphql.mutations import CANCEL_PAYMENT_MUTATION, REFUND_PAYMENT_MUTATION, CAPTURE_PAYMENT_MUTATION
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class MoneiPayment(models.Model):
    _name = 'monei.payment'
    _inherit = ['monei.mixin']
    _description = 'MONEI Payment'
    _order = 'payment_date desc, id desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(string='Payment ID', required=True, readonly=True)
    order_id = fields.Char(string='Order ID', readonly=True)
    checkout_id = fields.Char(string='Checkout ID', readonly=True)
    authorization_code = fields.Char(string='Authorization Code', readonly=True)
    livemode = fields.Boolean(string='Live Mode', readonly=True)
    
    # Amount Information
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        help='Payment amount'
    )
    currency = fields.Selection([
        ('EUR', 'EUR'),
    ], string='Currency', required=True, default='EUR')
    refunded_amount = fields.Monetary(
        string='Refunded Amount',
        currency_field='currency_id',
        help='Total refunded amount'
    )
    last_refund_amount = fields.Monetary(
        string='Last Refund Amount',
        currency_field='currency_id',
        help='Amount of the last refund'
    )
    last_refund_reason = fields.Selection([
        ('duplicated', 'Duplicated'),
        ('fraudulent', 'Fraudulent'),
        ('requested_by_customer', 'Requested by Customer'),
        ('order_canceled', 'Order Canceled')
    ], string='Refund Reason', readonly=True)

    # Status Information
    status = fields.Selection([
        ('SUCCEEDED', 'Succeeded'),
        ('PENDING', 'Pending'),
        ('FAILED', 'Failed'),
        ('CANCELED', 'Canceled'),
        ('REFUNDED', 'Refunded'),
        ('PARTIALLY_REFUNDED', 'Partially Refunded'),
        ('AUTHORIZED', 'Authorized'),
        ('EXPIRED', 'Expired'),
    ], string='Status', readonly=True)
    status_code = fields.Char(string='Status Code', readonly=True)
    status_message = fields.Text(string='Status Message', readonly=True)
    cancellation_reason = fields.Selection([
        ('fraudulent', 'Fraudulent'),
        ('duplicated', 'Duplicated'),
        ('requested_by_customer', 'Requested by Customer'),
        ('order_canceled', 'Order Canceled')
    ], string='Cancellation Reason', readonly=True)

    # Dates
    payment_date = fields.Datetime(string='Created At', readonly=True)
    updated_at = fields.Datetime(string='Updated At', readonly=True)
    page_opened_at = fields.Datetime(string='Page Opened At', readonly=True)

    # IDs and References
    account_id = fields.Char(string='Account ID', readonly=True)
    store_id = fields.Char(string='Store ID', readonly=True)
    store_name = fields.Char(string='Store Name', readonly=True)
    subscription_id = fields.Char(string='Subscription ID', readonly=True)
    terminal_id = fields.Char(string='Terminal ID', readonly=True)
    provider_id = fields.Char(string='Provider ID', readonly=True)
    provider_internal_id = fields.Char(string='Provider Internal ID', readonly=True)
    provider_reference_id = fields.Char(string='Provider Reference ID', readonly=True)
    point_of_sale_id = fields.Char(string='Point of Sale ID', readonly=True)
    sequence_id = fields.Char(string='Sequence ID', readonly=True)

    # Description
    description = fields.Text(string='Description', readonly=True)
    descriptor = fields.Char(string='Descriptor', readonly=True)

    # Customer Information
    customer_name = fields.Char(string='Customer Name', readonly=True)
    customer_email = fields.Char(string='Customer Email', readonly=True)
    customer_phone = fields.Char(string='Customer Phone', readonly=True)

    # Payment Method
    payment_method = fields.Char(string='Payment Method', readonly=True)
    card_brand = fields.Char(string='Card Brand', readonly=True)
    card_last4 = fields.Char(string='Card Last 4', readonly=True)
    card_type = fields.Char(string='Card Type', readonly=True)
    card_country = fields.Char(string='Card Country', readonly=True)
    cardholder_name = fields.Char(string='Cardholder Name', readonly=True)
    cardholder_email = fields.Char(string='Cardholder Email', readonly=True)
    card_expiration = fields.Char(string='Card Expiration', readonly=True)
    card_bank = fields.Char(string='Card Bank', readonly=True)
    tokenization_method = fields.Char(string='Tokenization Method', readonly=True)
    three_d_secure = fields.Boolean(string='3D Secure', readonly=True)
    three_d_secure_version = fields.Char(string='3D Secure Version', readonly=True)
    three_d_secure_flow = fields.Char(string='3D Secure Flow', readonly=True)

    # Shop Information
    shop_name = fields.Char(string='Shop Name', readonly=True)
    shop_country = fields.Char(string='Shop Country', readonly=True)

    # Shipping Details
    shipping_name = fields.Char(string='Shipping Name', readonly=True)
    shipping_email = fields.Char(string='Shipping Email', readonly=True)
    shipping_phone = fields.Char(string='Shipping Phone', readonly=True)
    shipping_company = fields.Char(string='Shipping Company', readonly=True)
    shipping_tax_id = fields.Char(string='Shipping Tax ID', readonly=True)
    
    # Shipping Address
    shipping_street = fields.Char(string='Shipping Street', readonly=True)
    shipping_street2 = fields.Char(string='Shipping Street 2', readonly=True)
    shipping_city = fields.Char(string='Shipping City', readonly=True)
    shipping_state = fields.Char(string='Shipping State', readonly=True)
    shipping_zip = fields.Char(string='Shipping ZIP', readonly=True)
    shipping_country = fields.Char(string='Shipping Country', readonly=True)

    # Billing Details
    billing_name = fields.Char(string='Billing Name', readonly=True)
    billing_email = fields.Char(string='Billing Email', readonly=True)
    billing_phone = fields.Char(string='Billing Phone', readonly=True)
    billing_company = fields.Char(string='Billing Company', readonly=True)
    billing_tax_id = fields.Char(string='Billing Tax ID', readonly=True)
    
    # Billing Address
    billing_street = fields.Char(string='Billing Street', readonly=True)
    billing_street2 = fields.Char(string='Billing Street 2', readonly=True)
    billing_city = fields.Char(string='Billing City', readonly=True)
    billing_state = fields.Char(string='Billing State', readonly=True)
    billing_zip = fields.Char(string='Billing ZIP', readonly=True)
    billing_country = fields.Char(string='Billing Country', readonly=True)
    
    # Billing Plan
    billing_plan = fields.Char(string='Billing Plan', readonly=True)
    
    # Session Details
    session_ip = fields.Char(string='Session IP', readonly=True)
    session_user_agent = fields.Char(string='Session User Agent', readonly=True)
    session_country = fields.Char(string='Session Country', readonly=True)
    session_lang = fields.Char(string='Session Language', readonly=True)
    session_device_type = fields.Char(string='Session Device Type', readonly=True)
    session_device_model = fields.Char(string='Session Device Model', readonly=True)
    session_browser = fields.Char(string='Session Browser', readonly=True)
    session_browser_version = fields.Char(string='Session Browser Version', readonly=True)
    session_browser_accept = fields.Char(string='Session Browser Accept', readonly=True)
    session_browser_color_depth = fields.Integer(string='Session Browser Color Depth', readonly=True)
    session_browser_screen_height = fields.Integer(string='Session Browser Screen Height', readonly=True)
    session_browser_screen_width = fields.Integer(string='Session Browser Screen Width', readonly=True)
    session_browser_timezone_offset = fields.Integer(string='Session Browser Timezone Offset', readonly=True)
    session_os = fields.Char(string='Session OS', readonly=True)
    session_os_version = fields.Char(string='Session OS Version', readonly=True)
    session_source = fields.Char(string='Session Source', readonly=True)
    session_source_version = fields.Char(string='Session Source Version', readonly=True)

    # Trace Details
    trace_ip = fields.Char(string='Trace IP', readonly=True)
    trace_user_agent = fields.Char(string='Trace User Agent', readonly=True)
    trace_country = fields.Char(string='Trace Country', readonly=True)
    trace_lang = fields.Char(string='Trace Language', readonly=True)
    trace_device_type = fields.Char(string='Trace Device Type', readonly=True)
    trace_device_model = fields.Char(string='Trace Device Model', readonly=True)
    trace_browser = fields.Char(string='Trace Browser', readonly=True)
    trace_browser_version = fields.Char(string='Trace Browser Version', readonly=True)
    trace_browser_accept = fields.Char(string='Trace Browser Accept', readonly=True)
    trace_os = fields.Char(string='Trace OS', readonly=True)
    trace_os_version = fields.Char(string='Trace OS Version', readonly=True)
    trace_source = fields.Char(string='Trace Source', readonly=True)
    trace_source_version = fields.Char(string='Trace Source Version', readonly=True)
    trace_user_id = fields.Char(string='Trace User ID', readonly=True)
    trace_user_email = fields.Char(string='Trace User Email', readonly=True)
    trace_user_name = fields.Char(string='Trace User Name', readonly=True)

    # Metadata
    metadata = fields.Text(string='Metadata', readonly=True)

    # Additional Payment Method Fields
    payment_method_type = fields.Selection([
        ('card', 'Card'),
        ('cardPresent', 'Card Present'),
        ('bizum', 'Bizum'),
        ('paypal', 'PayPal'),
        ('cofidis', 'Cofidis'),
        ('cofidisLoan', 'Cofidis Loan'),
        ('trustly', 'Trustly'),
        ('sepa', 'SEPA'),
        ('klarna', 'Klarna'),
        ('mbway', 'MB WAY')
    ], string='Payment Method Type', readonly=True)
    
    # PayPal specific fields
    paypal_order_id = fields.Char(string='PayPal Order ID', readonly=True)
    paypal_payer_id = fields.Char(string='PayPal Payer ID', readonly=True)
    paypal_email = fields.Char(string='PayPal Email', readonly=True)
    paypal_name = fields.Char(string='PayPal Name', readonly=True)

    # Bizum specific fields
    bizum_phone = fields.Char(string='Bizum Phone', readonly=True)
    bizum_integration_type = fields.Char(string='Bizum Integration Type', readonly=True)

    # SEPA specific fields
    sepa_accountholder_name = fields.Char(string='SEPA Account Holder Name', readonly=True)
    sepa_accountholder_email = fields.Char(string='SEPA Account Holder Email', readonly=True)
    sepa_country_code = fields.Char(string='SEPA Country Code', readonly=True)
    sepa_bank_name = fields.Char(string='SEPA Bank Name', readonly=True)
    sepa_bank_code = fields.Char(string='SEPA Bank Code', readonly=True)
    sepa_bic = fields.Char(string='SEPA BIC', readonly=True)
    sepa_last4 = fields.Char(string='SEPA Last 4', readonly=True)

    # Klarna specific fields
    klarna_billing_category = fields.Char(string='Klarna Billing Category', readonly=True)
    klarna_auth_payment_method = fields.Char(string='Klarna Auth Payment Method', readonly=True)

    # Computed Fields
    customer_display = fields.Char(
        string='Customer',
        compute='_compute_customer_display',
        store=False,
        readonly=True
    )

    payment_method_display = fields.Html(
        string='Payment Method',
        compute='_compute_payment_method_display',
        store=False,
        readonly=True
    )

    # Add these computed fields
    cancellation_reason_display = fields.Char(
        string='Cancellation Reason',
        compute='_compute_cancellation_reason_display',
        store=False,
        readonly=True
    )

    last_refund_reason_display = fields.Char(
        string='Refund Reason',
        compute='_compute_last_refund_reason_display',
        store=False,
        readonly=True
    )

    # Add the sale order relation
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        ondelete='set null',
        copy=False,
        index=True
    )
    # Add computed field for better UX
    sale_order_amount = fields.Monetary(
        related='sale_order_id.amount_total',
        string='Order Amount',
        readonly=True,
        currency_field='currency_id'
    )
    sale_order_state = fields.Selection(
        related='sale_order_id.state',
        string='Order State',
        readonly=True
    )
    sale_order_date = fields.Datetime(
        related='sale_order_id.date_order',
        string='Order Date',
        readonly=True
    )
    sale_order_partner_id = fields.Many2one(
        related='sale_order_id.partner_id',
        string='Customer',
        readonly=True
    )

    # Add currency_id field for monetary fields
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        compute='_compute_currency_id',
        store=True
    )

    payment_url = fields.Char(
        string='Payment URL',
        compute='_compute_payment_url',
        help='Link to view the payment in MONEI Dashboard'
    )

    # Add sync field to trigger sync on form open
    sync_status = fields.Char(
        string='Sync Status',
        compute='_action_sync_single_payment',
        store=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override to auto-link with sale order and sync information
        
        Args:
            vals_list (list): List of dictionaries containing values for creation
            
        Returns:
            recordset: Created records
        """
        # Ensure vals_list is a list
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        records = super().create(vals_list)
        
        # Process each created record
        for record in records:
            if record.order_id:
                sale_order = self.env['sale.order'].search([
                    ('name', '=', record.order_id)
                ], limit=1)
                if sale_order:
                    record.sale_order_id = sale_order.id
                    record._sync_order_information(sale_order)
        
        return records

    @api.depends('payment_method', 'customer_phone', 'bizum_phone', 'customer_email', 
                'paypal_email', 'cardholder_email', 'customer_name')
    def _compute_customer_display(self):
        for record in self:
            if record.payment_method == 'bizum':
                record.customer_display = record.bizum_phone or record.customer_phone or record.customer_name or ''
            else:
                # Try to get any available email
                email = (record.customer_email or 
                        record.paypal_email or 
                        record.cardholder_email)
                
                record.customer_display = email or record.customer_name or ''

    @api.depends('payment_method', 'card_brand', 'card_last4', 'tokenization_method')
    def _compute_payment_method_display(self):
        for record in self:
            icon_path = '/monei/static/src/img/payment_methods'
            
            # Build icons HTML
            icons_html = ''
            
            # Add tokenization method icon if exists
            if record.tokenization_method:
                icons_html += f'<img src="{icon_path}/{record.tokenization_method.lower()}.svg" class="payment-method-icon me-2"/>'
            
            # Add payment method/card brand icon
            if not record.payment_method:
                # Handle empty payment method
                icons_html += ''
                text_html = ''
            elif record.payment_method == 'card':
                brand = record.card_brand or 'default'
                icons_html += f'<img src="{icon_path}/{brand.lower()}.svg" class="payment-method-icon me-2"/>'
                
                # Only show last4 for cards
                last4 = record.card_last4 or '****'
                text_html = f'<span class="ms-1">•••• {last4}</span>'
            else:
                method = record.payment_method or 'unknown'
                icons_html += f'<img src="{icon_path}/{method.lower()}.svg" class="payment-method-icon me-2"/>'
                text_html = ''  # No text for non-card methods
            
            # Combine icons and text
            record.payment_method_display = Markup(
                f'<div class="d-flex align-items-center">'
                f'{icons_html}'
                f'{text_html}'
                f'</div>'
            )

    @api.depends('cancellation_reason')
    def _compute_cancellation_reason_display(self):
        cancel_selection = dict(self._fields['cancellation_reason'].selection or [])
        for record in self:
            record.cancellation_reason_display = cancel_selection.get(record.cancellation_reason, '')

    @api.depends('last_refund_reason')
    def _compute_last_refund_reason_display(self):
        refund_selection = dict(self._fields['last_refund_reason'].selection or [])
        for record in self:
            record.last_refund_reason_display = refund_selection.get(record.last_refund_reason, '')

    @api.model
    def action_sync_payments(self, date_from=None, date_to=None, is_cron=False):
        """Sync payments from MONEI API
        Args:
            date_from (datetime, optional): Start date for sync. Defaults to None.
            date_to (datetime, optional): End date for sync. Defaults to None.
            is_cron (bool, optional): Whether this is called from cron. If True and no dates specified,
                                    will sync last 24 hours. Defaults to False.
        """
        api_service = MoneiAPIService(self.env)
        self._log_info('Starting MONEI payment sync')
        self._log_info(f'Sync mode: {"Cron" if is_cron else "Manual"}')

        try:
            # If cron mode and no dates specified, set date range to last 24 hours
            if is_cron:
                date_from = fields.Datetime.subtract(fields.Datetime.now(), days=1)
                date_to = fields.Datetime.now()
                self._log_info(f'Cron mode: syncing from {date_from} to {date_to}')
            elif date_from or date_to:
                self._log_info(f'Date range: from {date_from or "beginning"} to {date_to or "now"}')
            else:
                self._log_info('No date range specified - syncing all payments')

            # Get stores data once at the beginning
            stores_response = api_service.execute_query(STORES_QUERY)
            stores = stores_response['data']['stores'].get('items', []) or []
            stores_by_id = {store['id']: store['name'] for store in stores}
            self._log_info(f'Found {len(stores)} stores to process')

            # Initialize counters for total operation
            total_added = 0
            total_updated = 0
            total_skipped = 0
            total_deleted = 0
            
            # Keep track of all payment IDs from API
            synced_payment_ids = set()
            
            def sync_batch(start_from=0):
                nonlocal total_added, total_updated, total_skipped
                
                self._log_info(f'Processing batch starting from offset {start_from}')
                
                # Build filter parts
                filter_parts = []
                
                filter_parts.append(f'size: 1000')
                
                # Add from parameter
                if start_from > 0:
                    filter_parts.append(f'from: {start_from}')
                
                # Build createdAt filter if dates are provided
                if date_from or date_to:
                    filter_values = []
                    if date_from:
                        filter_values.append(str(int(date_from.timestamp())))
                    if date_to:
                        filter_values.append(str(int(date_to.timestamp())))
                    if filter_values:
                        filter_parts.append(f'filter: {{createdAt: {{range: [{", ".join(filter_values)}]}}}}')
                
                # Combine filter parts
                filter_str = f'({", ".join(filter_parts)})' if filter_parts else ''
                
                query = CHARGES_QUERY % filter_str
                response_data = api_service.execute_query(query)
                
                if 'data' in response_data:
                    payments = response_data['data']['charges'].get('items', []) or []
                    total_payments = response_data['data']['charges']['total']
                    
                    self._log_info(f'Retrieved {len(payments)} payments from API (Total available: {total_payments})')
                    
                    # Add payment IDs to synced set
                    batch_payment_ids = []
                    
                    # Add payment IDs to synced set
                    for payment in payments:
                        if payment and isinstance(payment, dict):
                            payment_id = payment.get('id')
                            if payment_id:
                                synced_payment_ids.add(payment_id)
                                batch_payment_ids.append(payment_id)
                    
                    self._log_info(f'Processing {len(batch_payment_ids)} valid payments from current batch')
                    
                    # Process current batch with stores data from closure
                    added, updated, skipped = self._process_payment_batch(payments, stores_by_id)
                    
                    total_added += added
                    total_updated += updated
                    total_skipped += skipped
                    
                    self._log_info(f'Batch results - Added: {added}, Updated: {updated}, Skipped: {skipped}')
                    
                    # If we got a full batch (1000 payments), there might be more
                    if len(payments) == 1000 and (start_from + len(payments)) < total_payments:
                        next_batch = start_from + len(payments)
                        self._log_info(f'Batch complete, moving to next batch at offset {next_batch}')
                        # Recursive call for next batch
                        sync_batch(next_batch)
                    else:
                        self._log_info('No more batches to process')
            
            # Start the sync process
            sync_batch()
            
            # Find and delete payments that no longer exist in API
            domain = [('name', 'not in', list(synced_payment_ids))]
            if date_from:
                domain.append(('payment_date', '>=', date_from))
            if date_to:
                domain.append(('payment_date', '<=', date_to))
                
            self._log_info('Checking for obsolete payments...')
            
            payments_to_delete = self.search(domain)
            if payments_to_delete:
                total_deleted = len(payments_to_delete)
                payment_details = [
                    f"- {payment.name} ({payment.payment_date.strftime('%Y-%m-%d %H:%M:%S')})"
                    for payment in payments_to_delete
                ]
                self._log_info(f'Found {total_deleted} payment(s) no longer in MONEI:')
                for detail in payment_details:
                    self._log_info(detail)
                payments_to_delete.unlink()
                self._log_info(f'Successfully removed {total_deleted} obsolete payment(s)')
            else:
                self._log_info('No obsolete payments found')
            
            # Log final totals
            self._log_info(f'Sync complete - Total Added: {total_added}, Updated: {total_updated}, Skipped: {total_skipped}, Deleted: {total_deleted}')
            
            # Prepare result message
            message = []
            if total_added > 0:
                message.append(_('%d new payments synchronized') % total_added)
            if total_updated > 0:
                message.append(_('%d existing payments updated') % total_updated)
            if total_deleted > 0:
                message.append(_('%d obsolete payments removed') % total_deleted)
            if total_skipped > 0:
                message.append(_('%d payments unchanged') % total_skipped)
            
            if not message:
                message = [_('No changes found')]

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'title': _('Information'),
                    'message': ' and '.join(message),
                    'fadeout': 'slow',
                    'next': {
                        'type': 'ir.actions.act_window_close',
                    }
                },
            }

        except Exception as e:
            error_msg = f'Failed to sync payments: {str(e)}'
            self._log_error(error_msg)
            raise UserError(_(error_msg))

    def _prepare_payment_vals(self, payment_data):
        """Prepare payment values from API data"""
        # Get card details if available
        card_data = self._safe_get(payment_data, 'paymentMethod', 'card') or {}
        
        # Safely convert amounts, defaulting to 0 if None
        amount = payment_data.get('amount')
        amount = float(amount if amount is not None else 0) / 100.0
        
        refunded_amount = payment_data.get('refundedAmount')
        refunded_amount = float(refunded_amount if refunded_amount is not None else 0) / 100.0
        
        last_refund_amount = payment_data.get('lastRefundAmount')
        last_refund_amount = float(last_refund_amount if last_refund_amount is not None else 0) / 100.0

        return {
            'name': payment_data.get('id'),
            'order_id': payment_data.get('orderId'),
            'checkout_id': payment_data.get('checkoutId'),
            'authorization_code': payment_data.get('authorizationCode'),
            'livemode': payment_data.get('livemode', False),
            
            'amount': amount,
            'currency': payment_data.get('currency', ''),
            'refunded_amount': refunded_amount,
            'last_refund_amount': last_refund_amount,
            'last_refund_reason': payment_data.get('lastRefundReason'),
            
            'status': payment_data.get('status', 'PENDING'),
            'status_code': str(payment_data.get('statusCode', '')),
            'status_message': payment_data.get('statusMessage', ''),
            'cancellation_reason': payment_data.get('cancellationReason', ''),
            
            'payment_date': self._parse_datetime(payment_data.get('createdAt')),
            'updated_at': self._parse_datetime(payment_data.get('updatedAt')),
            'page_opened_at': self._parse_datetime(payment_data.get('pageOpenedAt')),
            
            'account_id': payment_data.get('accountId', ''),
            'store_id': payment_data.get('storeId'),
            'subscription_id': payment_data.get('subscriptionId', ''),
            'terminal_id': payment_data.get('terminalId', ''),
            'provider_id': payment_data.get('providerId', ''),
            'provider_internal_id': payment_data.get('providerInternalId', ''),
            'provider_reference_id': payment_data.get('providerReferenceId', ''),
            'point_of_sale_id': payment_data.get('pointOfSaleId', ''),
            'sequence_id': payment_data.get('sequenceId', ''),
            'description': payment_data.get('description', ''),
            'descriptor': payment_data.get('descriptor', ''),
            
            'customer_name': self._safe_get(payment_data, 'customer', 'name', default=''),
            'customer_email': self._safe_get(payment_data, 'customer', 'email', default=''),
            'customer_phone': self._safe_get(payment_data, 'customer', 'phone', default=''),
            'payment_method': self._safe_get(payment_data, 'paymentMethod', 'method', default=''),
            
            'shipping_name': self._safe_get(payment_data, 'shippingDetails', 'name', default=''),
            'shipping_email': self._safe_get(payment_data, 'shippingDetails', 'email', default=''),
            'shipping_phone': self._safe_get(payment_data, 'shippingDetails', 'phone', default=''),
            'shipping_company': self._safe_get(payment_data, 'shippingDetails', 'company', default=''),
            'shipping_tax_id': self._safe_get(payment_data, 'shippingDetails', 'taxId', default=''),
            'shipping_street': self._safe_get(payment_data, 'shippingDetails', 'address', 'line1', default=''),
            'shipping_street2': self._safe_get(payment_data, 'shippingDetails', 'address', 'line2', default=''),
            'shipping_city': self._safe_get(payment_data, 'shippingDetails', 'address', 'city', default=''),
            'shipping_state': self._safe_get(payment_data, 'shippingDetails', 'address', 'state', default=''),
            'shipping_zip': self._safe_get(payment_data, 'shippingDetails', 'address', 'zip', default=''),
            'shipping_country': self._safe_get(payment_data, 'shippingDetails', 'address', 'country', default=''),
            
            'billing_name': self._safe_get(payment_data, 'billingDetails', 'name', default=''),
            'billing_email': self._safe_get(payment_data, 'billingDetails', 'email', default=''),
            'billing_phone': self._safe_get(payment_data, 'billingDetails', 'phone', default=''),
            'billing_company': self._safe_get(payment_data, 'billingDetails', 'company', default=''),
            'billing_tax_id': self._safe_get(payment_data, 'billingDetails', 'taxId', default=''),
            'billing_street': self._safe_get(payment_data, 'billingDetails', 'address', 'line1', default=''),
            'billing_street2': self._safe_get(payment_data, 'billingDetails', 'address', 'line2', default=''),
            'billing_city': self._safe_get(payment_data, 'billingDetails', 'address', 'city', default=''),
            'billing_state': self._safe_get(payment_data, 'billingDetails', 'address', 'state', default=''),
            'billing_zip': self._safe_get(payment_data, 'billingDetails', 'address', 'zip', default=''),
            'billing_country': self._safe_get(payment_data, 'billingDetails', 'address', 'country', default=''),
            
            # Card details
            'card_brand': card_data.get('brand'),
            'card_last4': card_data.get('last4'),
            'card_type': card_data.get('type'),
            'card_country': card_data.get('country'),
            'cardholder_name': card_data.get('cardholderName'),
            'cardholder_email': card_data.get('cardholderEmail'),
            'card_expiration': card_data.get('expiration'),
            'card_bank': card_data.get('bank'),
            'tokenization_method': card_data.get('tokenizationMethod'),
            'three_d_secure': card_data.get('threeDSecure'),
            'three_d_secure_version': card_data.get('threeDSecureVersion'),
            'three_d_secure_flow': card_data.get('threeDSecureFlow'),
            
            # Shop details
            'shop_name': self._safe_get(payment_data, 'shop', 'name'),
            'shop_country': self._safe_get(payment_data, 'shop', 'country'),

            # Billing Plan
            'billing_plan': payment_data.get('billingPlan'),

            # Session Details
            'session_ip': self._safe_get(payment_data, 'sessionDetails', 'ip'),
            'session_user_agent': self._safe_get(payment_data, 'sessionDetails', 'userAgent'),
            'session_country': self._safe_get(payment_data, 'sessionDetails', 'countryCode'),
            'session_lang': self._safe_get(payment_data, 'sessionDetails', 'lang'),
            'session_device_type': self._safe_get(payment_data, 'sessionDetails', 'deviceType'),
            'session_device_model': self._safe_get(payment_data, 'sessionDetails', 'deviceModel'),
            'session_browser': self._safe_get(payment_data, 'sessionDetails', 'browser'),
            'session_browser_version': self._safe_get(payment_data, 'sessionDetails', 'browserVersion'),
            'session_browser_accept': self._safe_get(payment_data, 'sessionDetails', 'browserAccept'),
            'session_browser_color_depth': self._safe_get(payment_data, 'sessionDetails', 'browserColorDepth'),
            'session_browser_screen_height': self._safe_get(payment_data, 'sessionDetails', 'browserScreenHeight'),
            'session_browser_screen_width': self._safe_get(payment_data, 'sessionDetails', 'browserScreenWidth'),
            'session_browser_timezone_offset': self._safe_get(payment_data, 'sessionDetails', 'browserTimezoneOffset'),
            'session_os': self._safe_get(payment_data, 'sessionDetails', 'os'),
            'session_os_version': self._safe_get(payment_data, 'sessionDetails', 'osVersion'),
            'session_source': self._safe_get(payment_data, 'sessionDetails', 'source'),
            'session_source_version': self._safe_get(payment_data, 'sessionDetails', 'sourceVersion'),

            # Trace Details
            'trace_ip': self._safe_get(payment_data, 'traceDetails', 'ip'),
            'trace_user_agent': self._safe_get(payment_data, 'traceDetails', 'userAgent'),
            'trace_country': self._safe_get(payment_data, 'traceDetails', 'countryCode'),
            'trace_lang': self._safe_get(payment_data, 'traceDetails', 'lang'),
            'trace_device_type': self._safe_get(payment_data, 'traceDetails', 'deviceType'),
            'trace_device_model': self._safe_get(payment_data, 'traceDetails', 'deviceModel'),
            'trace_browser': self._safe_get(payment_data, 'traceDetails', 'browser'),
            'trace_browser_version': self._safe_get(payment_data, 'traceDetails', 'browserVersion'),
            'trace_browser_accept': self._safe_get(payment_data, 'traceDetails', 'browserAccept'),
            'trace_os': self._safe_get(payment_data, 'traceDetails', 'os'),
            'trace_os_version': self._safe_get(payment_data, 'traceDetails', 'osVersion'),
            'trace_source': self._safe_get(payment_data, 'traceDetails', 'source'),
            'trace_source_version': self._safe_get(payment_data, 'traceDetails', 'sourceVersion'),
            'trace_user_id': self._safe_get(payment_data, 'traceDetails', 'userId'),
            'trace_user_email': self._safe_get(payment_data, 'traceDetails', 'userEmail'),
            'trace_user_name': self._safe_get(payment_data, 'traceDetails', 'userName'),

            # Metadata
            'metadata': json.dumps(payment_data.get('metadata', [])),

            # Payment Method Type and Details
            'payment_method_type': self._safe_get(payment_data, 'paymentMethod', 'method'),

            # PayPal Details
            'paypal_order_id': self._safe_get(payment_data, 'paymentMethod', 'paypal', 'orderId'),
            'paypal_payer_id': self._safe_get(payment_data, 'paymentMethod', 'paypal', 'payerId'),
            'paypal_email': self._safe_get(payment_data, 'paymentMethod', 'paypal', 'email'),
            'paypal_name': self._safe_get(payment_data, 'paymentMethod', 'paypal', 'name'),

            # Bizum Details
            'bizum_phone': self._safe_get(payment_data, 'paymentMethod', 'bizum', 'phoneNumber'),
            'bizum_integration_type': self._safe_get(payment_data, 'paymentMethod', 'bizum', 'integrationType'),

            # SEPA Details
            'sepa_accountholder_name': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'accountholderName'),
            'sepa_accountholder_email': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'accountholderEmail'),
            'sepa_country_code': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'countryCode'),
            'sepa_bank_name': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'bankName'),
            'sepa_bank_code': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'bankCode'),
            'sepa_bic': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'bic'),
            'sepa_last4': self._safe_get(payment_data, 'paymentMethod', 'sepa', 'last4'),

            # Klarna Details
            'klarna_billing_category': self._safe_get(payment_data, 'paymentMethod', 'klarna', 'billingCategory'),
            'klarna_auth_payment_method': self._safe_get(payment_data, 'paymentMethod', 'klarna', 'authPaymentMethod'),
        }

    def _needs_payment_update(self, payment_data):
        """Check if payment needs to be updated based on updated_at timestamp.
        
        Args:
            payment_data (dict): Payment data from API
            
        Returns:
            bool: True if payment needs update, False otherwise
        """
        # Format the API datetime to match Odoo's format
        api_updated_at = self._parse_datetime(payment_data.get('updatedAt'))
        
        # If API updated_at is newer than our record's updated_at, we need an update
        if api_updated_at and (not self.updated_at or api_updated_at > self.updated_at):
            self._log_info(f'Payment needs update: API timestamp {api_updated_at} is newer than record timestamp {self.updated_at}')
            return True
            
        return False

    @api.depends('name')
    def _action_sync_single_payment(self):
        """Sync a single payment from MONEI API"""
        for record in self:
            record.sync_status = 'synced'  # Default status
            
            if not record.name:
                continue
                
            record._log_info(f'Syncing payment {record.name}')
            
            # Check if sync is disabled in settings
            disable_sync = record.env['ir.config_parameter'].sudo().get_param('monei.disable_sync_on_load', 'False') == 'True'
            
            record._log_info(f'Sync disabled: {disable_sync}')
            
            if disable_sync:
                record.sync_status = 'disabled'
                continue
                
            api_service = MoneiAPIService(record.env)
            
            try:
                response_data = api_service.execute_query(CHARGE_QUERY, {'id': record.name})
                
                if 'data' in response_data and 'charge' in response_data['data']:
                    payment_data = response_data['data']['charge']
                    if payment_data:
                        if record._needs_payment_update(payment_data):
                            vals = record._prepare_payment_vals(payment_data)
                            record.write(vals)
                            record._log_info(f'Payment {record.name} updated')
                            record.sync_status = 'updated'
                        else:
                            record._log_info(f'Payment {record.name} unchanged')
                            record.sync_status = 'unchanged'

            except Exception as e:
                record._log_error(f'Failed to sync payment {record.name}: {e}')
                record.sync_status = 'error'

    def _process_payment_batch(self, payments, stores_by_id):
        """Process a batch of payments and return counters"""
        added = 0
        updated = 0
        skipped = 0
        
        for payment in payments:
            if not payment or not isinstance(payment, dict):
                self._log_warning(f'Invalid payment data: {payment}')
                continue

            payment_id = payment.get('id')
            if not payment_id:
                self._log_warning('Payment without ID, skipping')
                continue

            try:
                vals = self._prepare_payment_vals(payment)
                vals['store_name'] = stores_by_id.get(payment.get('storeId'), '')

                existing = self.search([('name', '=', payment_id)])
                if existing:
                    if existing._needs_payment_update(payment):
                        existing.write(vals)
                        updated += 1
                    else:
                        skipped += 1
                else:
                    self.create(vals)
                    added += 1

            except Exception as e:
                self._log_error(f'Error processing payment {payment_id}: {e}')
                continue
        
        return added, updated, skipped

    def action_capture_payment(self):
        self.ensure_one()
        if self.status != 'AUTHORIZED':
            raise UserError(_('Only authorized payments can be captured.'))
        
        # Open wizard to enter capture amount
        return {
            'name': _('Capture Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'monei.payment.capture.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_id': self.id,
                'default_amount': self.amount,
            }
        }

    def action_refund_payment(self):
        self.ensure_one()
        if self.status not in ['SUCCEEDED', 'PARTIALLY_REFUNDED']:
            raise UserError(_('Only succeeded or partially refunded payments can be refunded.'))
        
        # Open wizard to enter refund amount and reason
        return {
            'name': _('Refund Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'monei.payment.refund.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_id': self.id,
                'default_amount': self.amount - self.refunded_amount,
            }
        }

    def action_cancel_payment(self):
        self.ensure_one()
        if self.status not in ['PENDING', 'AUTHORIZED']:
            raise UserError(_('Only pending or authorized payments can be cancelled.'))
        
        # Open wizard to enter cancellation reason
        return {
            'name': _('Cancel Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'monei.payment.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_id': self.id,
            }
        }

    def action_send_payment_link(self):
        self.ensure_one()
        return {
            'name': _('Send Payment Link'),
            'type': 'ir.actions.act_window',
            'res_model': 'monei.payment.send.link.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_id': self.id,
                'active_id': self.id,
                'default_notification_email': self.customer_email,
                'default_notification_phone': self.customer_phone,
            }
        } 

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'context': {'create': False},
        } 

    def _sync_order_information(self, sale_order):
        """Sync customer and address information from sale order"""
        self.ensure_one()
        partner = sale_order.partner_id
        
        # Update customer information
        vals = {
            'customer_name': partner.name,
            'customer_email': partner.email,
            'customer_phone': partner.phone,
        }

        # Update billing information
        invoice_partner = sale_order.partner_invoice_id or partner
        vals.update({
            'billing_name': invoice_partner.name,
            'billing_email': invoice_partner.email,
            'billing_phone': invoice_partner.phone,
            'billing_company': invoice_partner.company_name or invoice_partner.commercial_company_name,
            'billing_tax_id': invoice_partner.vat,
            'billing_street': invoice_partner.street,
            'billing_street2': invoice_partner.street2,
            'billing_city': invoice_partner.city,
            'billing_state': invoice_partner.state_id.name,
            'billing_zip': invoice_partner.zip,
            'billing_country': invoice_partner.country_id.code,
        })

        # Update shipping information
        delivery_partner = sale_order.partner_shipping_id or partner
        vals.update({
            'shipping_name': delivery_partner.name,
            'shipping_email': delivery_partner.email,
            'shipping_phone': delivery_partner.phone,
            'shipping_company': delivery_partner.company_name or delivery_partner.commercial_company_name,
            'shipping_tax_id': delivery_partner.vat,
            'shipping_street': delivery_partner.street,
            'shipping_street2': delivery_partner.street2,
            'shipping_city': delivery_partner.city,
            'shipping_state': delivery_partner.state_id.name,
            'shipping_zip': delivery_partner.zip,
            'shipping_country': delivery_partner.country_id.code,
        })

        self.write(vals)

    def action_link_orders(self):
        """Link payments with their corresponding sale orders"""
        linked = 0
        for payment in self.search([('sale_order_id', '=', False)]):
            if payment.order_id:
                sale_order = self.env['sale.order'].search([
                    ('name', '=', payment.order_id)
                ], limit=1)
                if sale_order:
                    payment.sale_order_id = sale_order.id
                    payment._sync_order_information(sale_order)
                    linked += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Orders Linked'),
                'message': _('%d payments linked to orders') % linked if linked else _('No new links found'),
                'type': 'info',
                'sticky': False,
            }
        } 

    @api.depends('currency')
    def _compute_currency_id(self):
        """Get the res.currency record corresponding to the currency code"""
        for record in self:
            if record.currency:
                record.currency_id = self.env['res.currency'].search([
                    ('name', '=', record.currency)
                ], limit=1)
            else:
                record.currency_id = False
            self._log_info(f'Currency ID computed for payment {record.id}: {record.currency_id}')   
            self._log_info(record.currency_id.name) 
            

    @api.depends('name')
    def _compute_payment_url(self):
        api_service = MoneiAPIService(self.env)
        for record in self:
            if record.name:
                record.payment_url = api_service._get_payment_url(record.name)
            else:
                record.payment_url = False
            
