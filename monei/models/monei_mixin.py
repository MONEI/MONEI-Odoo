from odoo import models, api, _
from datetime import datetime
import logging
import re
from odoo.exceptions import UserError
import inspect

_logger = logging.getLogger(__name__)

class MoneiMixin(models.AbstractModel):
    _name = 'monei.mixin'
    _description = 'MONEI Mixin'

    def _parse_datetime(self, timestamp):
        """Convert Unix timestamp to Odoo datetime"""
        try:
            if isinstance(timestamp, (int, float)) and timestamp > 0:
                return datetime.fromtimestamp(timestamp)
            return False
        except Exception as e:
            self._log_warning(f'Error parsing timestamp {timestamp}: {e}')
            return False

    def _safe_get(self, data, *keys, default=False):
        """Safely get nested dictionary values"""
        current = data
        for key in keys:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current if current is not None else default 
    
    def _get_caller(self):
        """Get the name of the calling function"""
        # Get the caller's frame (2 levels up: _get_caller -> _log_x -> actual caller)
        caller_frame = inspect.currentframe().f_back.f_back
        # Get function name
        func_name = caller_frame.f_code.co_name
        # Get class name if it exists
        if 'self' in caller_frame.f_locals:
            class_name = caller_frame.f_locals['self'].__class__.__name__
            return f"[{class_name}.{func_name}]"
        return f"[{func_name}]"

    def _log_info(self, message):
        """Log info message with caller information"""
        caller = self._get_caller()
        _logger.info(f"{caller} - {message}")

    def _log_warning(self, message):
        """Log warning message with caller information"""
        caller = self._get_caller()
        _logger.warning(f"{caller} - {message}")

    def _log_error(self, message):
        """Log error message with caller information"""
        caller = self._get_caller()
        _logger.error(f"{caller} - {message}")

    def _log_debug(self, message):
        """Log debug message with caller information"""
        caller = self._get_caller()
        _logger.debug(f"{caller} - {message}")

    def _validate_phone(self, phone, field_name='phone'):
        """
        Validate and clean phone number to E.164 format
        Args:
            phone: Phone number to validate
            field_name: Name of the field for error message
        Returns:
            str: Cleaned phone number in E.164 format
        Raises:
            UserError: If phone number format is invalid
        """
        if not phone:
            return False

        # Clean phone number (remove spaces and any other characters)
        clean_phone = ''.join(char for char in phone if char.isdigit() or char == '+')
        if not clean_phone.startswith('+'):
            clean_phone = '+' + clean_phone

        # Validate E.164 format
        phone_pattern = r'^\+[1-9]\d{1,14}$'
        if not re.match(phone_pattern, clean_phone):
            raise UserError(_(
                '%s must be in E.164 format: "+" followed by country code and number.\n'
                'Example: +34612345678'
            ) % field_name.replace('_', ' ').title())

        return clean_phone

    def _validate_email(self, email, field_name='email'):
        """
        Validate email format
        Args:
            email: Email to validate
            field_name: Name of the field for error message
        Returns:
            str: Cleaned email address
        Raises:
            UserError: If email format is invalid
        """
        if not email:
            return False

        # Clean email (remove extra spaces)
        clean_email = email.strip()

        # RFC 5322 compliant email regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, clean_email):
            raise UserError(_(
                '%s must be a valid email address.\n'
                'Example: john.doe@example.com'
            ) % field_name.replace('_', ' ').title())

        return clean_email
