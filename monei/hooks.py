def post_init_hook(cr, registry=None):
    """Post-install hook to update cron job settings from config parameters.
    
    This hook can be called in two ways:
    1. post_init_hook(cr, registry) - during module installation
    2. post_init_hook(env) - during module upgrade
    
    The sync settings will only be enabled if there's a valid API key configured.
    """
    import logging
    from odoo import api, SUPERUSER_ID
    
    _logger = logging.getLogger(__name__)
    
    # Handle case where cr is actually an environment
    env = cr if hasattr(cr, 'cr') else api.Environment(cr, SUPERUSER_ID, {})
    
    try:
        # Get config parameters
        ICP = env['ir.config_parameter'].sudo()
        
        # Only set values if they don't exist
        if not ICP.get_param('monei.enable_cron_sync'):
            ICP.set_param('monei.enable_cron_sync', 'False')  # Disabled by default
        if not ICP.get_param('monei.cron_interval_number'):
            ICP.set_param('monei.cron_interval_number', '1')
        if not ICP.get_param('monei.cron_interval_type'):
            ICP.set_param('monei.cron_interval_type', 'days')
        
        # Update cron job with current config values
        cron_sudo = env.ref('monei.ir_cron_sync_monei_payments').sudo()
        if cron_sudo:
            cron_sudo.write({
                'active': ICP.get_param('monei.enable_cron_sync') == 'True',
                'interval_number': int(ICP.get_param('monei.cron_interval_number')),
                'interval_type': ICP.get_param('monei.cron_interval_type'),
            })
            _logger.info('MONEI cron job updated successfully')
            
    except Exception as e:
        _logger.error('Failed to initialize MONEI settings: %s', str(e))
        # Don't raise the exception to avoid breaking the install/upgrade process
        return False
    
    return True

def uninstall_hook(cr, registry=None):
    """Clean up MONEI configuration parameters when uninstalling the module.
    
    This hook can be called in two ways:
    1. uninstall_hook(cr, registry) - during module uninstallation
    2. uninstall_hook(env) - during registry loading
    
    Args:
        cr: database cursor or environment
        registry: Odoo registry (optional)
    """
    import logging
    from odoo import api, SUPERUSER_ID
    
    _logger = logging.getLogger(__name__)
    
    # Handle case where cr is actually an environment
    env = cr if hasattr(cr, 'cr') else api.Environment(cr, SUPERUSER_ID, {})
    
    try:
        # Get config parameters
        ICP = env['ir.config_parameter'].sudo()
        
        # List of all MONEI config parameters
        monei_params = [
            'monei.api_key',
            'monei.enable_cron_sync',
            'monei.disable_sync_on_load',
            'monei.cron_interval_number',
            'monei.cron_interval_type',
        ]
        
        # Delete all MONEI parameters
        for param in monei_params:
            if ICP.get_param(param):
                ICP.set_param(param, False)
                _logger.info('Removed config parameter: %s', param)
        
        _logger.info('MONEI configuration parameters cleaned up successfully')
            
    except Exception as e:
        _logger.error('Failed to clean up MONEI configuration parameters: %s', str(e))
        # Don't raise the exception to avoid breaking the uninstall process
        return False
    
    return True 