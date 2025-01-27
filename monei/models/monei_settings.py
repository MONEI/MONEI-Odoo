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
    
    mock_server = fields.Boolean(
        string="Mock Server",
        config_parameter='monei.mock_server',
        default=False,
        help="Use the mock server instead of the real MONEI API"
    )
    
    def set_values(self):
        """Override to handle payment deletion when API key or mock server changes"""
        old_api_key = self.env['ir.config_parameter'].sudo().get_param('monei.api_key')
        old_mock_server = self.env['ir.config_parameter'].sudo().get_param('monei.mock_server') == 'True'
        
        # Save new values
        res = super().set_values()
        
        # If API key or mock server changed, delete all payments
        if self.monei_api_key != old_api_key or self.mock_server != old_mock_server:
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
    
    def _get_api_url(self, subdomain='graphql'):
        """Get the API URL
        
        Args:
            subdomain (str): The subdomain to use (default: graphql)
                           Examples: graphql, dashboard
        
        Returns:
            str: The complete API URL
        """
        if self.env['ir.config_parameter'].sudo().get_param('monei.mock_server') == 'True':
            return 'http://host.docker.internal:5001'
        
        return f'https://{subdomain}.monei.com'

    @api.constrains('monei_api_key')
    def _check_api_key(self):
        """Validate API key format and trigger initial sync if needed"""
        for record in self:
            if not record.monei_api_key:
                continue
            
            # Check API key format
            is_valid_format = re.match(r'^pk_(test|live)_([a-z0-9]{32})$', record.monei_api_key)
            if not is_valid_format:
                raise ValidationError("API Key is not valid, it must be in the format pk_test_ or pk_live_ followed by 32 characters")
            
            # If format is valid and key changed, test connection and sync
            old_key = self.env['ir.config_parameter'].sudo().get_param('monei.api_key')
            if record.monei_api_key != old_key:
                try:
                    # Temporarily set the new API key
                    self.env['ir.config_parameter'].sudo().set_param('monei.api_key', record.monei_api_key)
                    
                    try:
                        api_service = MoneiAPIService(self.env)
                        api_service.test_connection(record.monei_api_key)
                        
                        # Get month date range
                        date_from, date_to = get_month_date_range()
                        
                        # Trigger the sync
                        self.env['monei.payment'].action_sync_payments(
                            date_from=date_from,
                            date_to=date_to
                        )
                        
                        # Show success message
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Success'),
                                'message': _('API Key validated and payments synced from %s to %s') % (
                                    fields.Datetime.to_string(date_from),
                                    fields.Datetime.to_string(date_to)
                                ),
                                'type': 'success',
                            }
                        }
                    except Exception as e:
                        # Restore old key if validation fails
                        if old_key:
                            self.env['ir.config_parameter'].sudo().set_param('monei.api_key', old_key)
                        raise ValidationError(f"{str(e)}")
                except Exception as e:
                    raise ValidationError(f"API Key validation failed: {str(e)}")

    def action_test_connection(self, api_key=None):
        """Test the connection to MONEI API"""
        if not api_key:
            api_key = self.monei_api_key
        if not api_key:
            raise UserError(_('Please set and save the API Key first'))

        try:
            api_service = MoneiAPIService(self.env)
            api_service.test_connection(api_key)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Connection to MONEI API successful'),
                    'type': 'success',
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    