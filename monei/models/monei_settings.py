import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import requests
from odoo.tools import config
from datetime import datetime, timedelta
from ..utils.date_utils import get_month_date_range
import logging
import json
from ..services.api_service import MoneiAPIService

logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    monei_api_key = fields.Char(
        string="API Key", 
        config_parameter='monei.api_key',
        help="Your MONEI API Key"
    )
    
    disable_sync_on_load = fields.Boolean(
        string="Disable Sync on Load",
        config_parameter='monei.disable_sync_on_load',
        help="If checked, payments won't be automatically synced when opening their form"
    )

    enable_cron_sync = fields.Boolean(
        string="Enable Automatic Sync",
        config_parameter='monei.enable_cron_sync',
        help="If checked, payments will be automatically synced based on the configured interval"
    )

    cron_interval_number = fields.Integer(
        string="Interval Number",
        config_parameter='monei.cron_interval_number',
        default=1,
        help="Repeat every x."
    )

    cron_interval_type = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months')
    ], string='Interval Unit', 
       config_parameter='monei.cron_interval_type',
       default='days',
       help="Interval Unit of automatic sync"
    )
    
    def set_values(self):
        """Override to handle payment deletion when API key changes and update cron job.
        Also ensures sync settings can only be enabled with a valid API key."""
        old_api_key = self.env['ir.config_parameter'].sudo().get_param('monei.api_key')
        
        # Check API key by testing connection only if it's changed and not empty
        is_valid_api_key = False
        connection_error = None
        
        if self.monei_api_key and self.monei_api_key != old_api_key:
            try:
                api_service = MoneiAPIService(self.env)
                api_service.test_connection(self.monei_api_key)
                is_valid_api_key = True
            except Exception as e:
                logger.warning("API Key validation failed: %s", str(e))
                connection_error = str(e)
                is_valid_api_key = False
                # Raise validation error if API key changed and connection failed
                raise ValidationError(_("Could not connect with the provided API key: %s") % str(e))
        elif self.monei_api_key:
            # If API key exists but hasn't changed, consider it valid
            is_valid_api_key = True
        
        # If API key is invalid or empty, prevent enabling sync settings
        if not is_valid_api_key:
            # Force sync settings to disabled
            self.enable_cron_sync = False
            self.disable_sync_on_load = False
            
            # If trying to modify sync settings without valid API key, show warning
            if (self.env['ir.config_parameter'].sudo().get_param('monei.enable_cron_sync') != str(self.enable_cron_sync) or
                self.env['ir.config_parameter'].sudo().get_param('monei.disable_sync_on_load') != str(self.disable_sync_on_load)):
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Warning'),
                        'message': _('Sync settings cannot be modified without a working API key.'),
                        'type': 'warning',
                        'sticky': True,
                    }
                }
        
        
        # Save new values
        res = super().set_values()
        
        # Update cron job
        cron_sudo = self.env.ref('monei.ir_cron_sync_monei_payments').sudo()
        if cron_sudo:
            cron_sudo.write({
                'active': self.enable_cron_sync and is_valid_api_key,
                'interval_number': self.cron_interval_number,
                'interval_type': self.cron_interval_type,
            })
        
        # If API key changed and is valid, delete all payments
        if self.monei_api_key != old_api_key and is_valid_api_key:
            self.env['monei.payment'].sudo().search([]).unlink()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning'),
                    'message': _('API configuration changed. All existing payments have been deleted and will be re-synced with the new account.'),
                    'type': 'warning',
                    'sticky': True,
                }
            }
        return res

    @api.constrains('monei_api_key')
    def _check_api_key(self):
        """Validate API key format"""
        for record in self:
            if not record.monei_api_key:
                continue
            
            # Check API key format
            is_valid_format = re.match(r'^pk_(test|live)_([a-z0-9]{32})$', record.monei_api_key)
            if not is_valid_format:
                raise ValidationError(_("API Key format is not valid. It must start with pk_test_ or pk_live_ followed by 32 characters"))
