from odoo import _, modules
from odoo.exceptions import UserError
import requests
import json

class MoneiAPIService:
    def __init__(self, env):
        self.env = env
        # Get the mixin model to use its logging methods
        self.mixin = self.env['monei.mixin']
        # Get module version from manifest, removing Odoo version prefix if present
        manifest = modules.get_manifest('monei')
        version = manifest.get('version', '0.0.0')
        # Remove Odoo version prefix if present (e.g., "18.0.1.0.0" -> "1.0.0")
        self.version = version.split('.')[-3:] if len(version.split('.')) > 3 else version
        self.version = '.'.join(str(x) for x in self.version)

    def _get_api_url(self, subdomain='graphql'):
        """Get API URL with specified subdomain"""
        return self.env['res.config.settings']._get_api_url(subdomain)

    def _get_payment_url(self, payment_id):
        """Get payment dashboard URL"""
        base_url = self._get_api_url('dashboard')
        return f"{base_url}/payments/{payment_id}"

    def _get_api_key(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('monei.api_key')
        if not api_key:
            raise UserError(_('Please configure MONEI API Key first'))
        return api_key

    def _make_request(self, data):
        """Make a request to the MONEI API"""
        try:
            self.mixin._log_debug(f"Making API request:\n{json.dumps(data, indent=2)}")

            response = requests.post(
                self._get_api_url(),
                headers={
                    'Authorization': f'Bearer {self._get_api_key()}',
                    'Content-Type': 'application/json',
                    'User-Agent': f'MONEI/Odoo/{self.version}'
                },
                json=data,
                timeout=30
            )
            
            response_data = response.json()
            
            if 'errors' in response_data:
                raise UserError(response_data['errors'][0].get('message', 'Unknown error'))
                
            return response_data
            
        except requests.exceptions.ConnectionError:
            raise UserError(_('Could not connect to the server. Contact support if the issue persists.'))
        except requests.exceptions.Timeout:
            raise UserError(_('The request timed out. Please try again. If the issue persists, contact support.'))
        except Exception as e:
            self.mixin._log_error(f'API request failed: {e}')
            raise UserError(_('API request failed: %s') % str(e))

    def execute_query(self, query, variables=None):
        """Execute a GraphQL query"""
        data = {
            'query': query,
            'variables': variables or {}
        }
        return self._make_request(data)

    def execute_mutation(self, mutation, variables=None):
        """Execute a GraphQL mutation"""
        data = {
            'query': mutation,
            'variables': variables or {}
        }
        return self._make_request(data)

    def test_connection(self, api_key=None):
        """Test connection to MONEI API
        
        Args:
            api_key (str): Optional API key to test. If not provided, uses the configured one.
            
        Raises:
            UserError: If connection fails, API key is invalid, or response format is incorrect
        """
        if api_key is None:
            api_key = self._get_api_key()
        
        try:
            response = self.execute_query("""
                query Account {
                    account {
                    apiKey
                }
            }
            """)
        
            self.mixin._log_debug(f"Test connection response:\n{json.dumps(response, indent=2)}")
            
            if 'data' in response and 'account' in response['data']:
                returned_api_key = response['data']['account'].get('apiKey')
                if returned_api_key != api_key:
                    raise UserError(_('API Key mismatch'))
            else:
                raise UserError(_('Invalid response format from server')) 
        except Exception as e:
            raise UserError(_('Connection test failed'))
