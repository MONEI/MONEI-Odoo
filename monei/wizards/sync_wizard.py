from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ..utils.date_utils import (
    get_today_date_range,
    get_yesterday_date_range,
    get_week_date_range,
    get_month_date_range
)

class MoneiSyncWizard(models.TransientModel):
    _name = 'monei.sync.wizard'
    _description = 'MONEI Sync Wizard'

    date_from = fields.Datetime(
        string='From Date',
        required=True,
        default=lambda self: fields.Datetime.now() - timedelta(days=1)
    )
    date_to = fields.Datetime(
        string='To Date',
        required=True,
        default=fields.Datetime.now
    )

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for wizard in self:
            if wizard.date_from and wizard.date_to:
                now = fields.Datetime.now()
                if wizard.date_to > now:
                    raise ValidationError(_('The end date cannot be in the future.'))
                if wizard.date_from > wizard.date_to:
                    raise ValidationError(_('The start date must be before the end date.'))

    def action_sync(self):
        self.ensure_one()
        return self.env['monei.payment'].action_sync_payments(
            date_from=self.date_from,
            date_to=self.date_to
        )

    def action_set_today(self):
        self.ensure_one()
        date_from, date_to = get_today_date_range()
        
        self.write({
            'date_from': date_from,
            'date_to': date_to,
        })
        return self._return_wizard_action()

    def action_set_yesterday(self):
        self.ensure_one()
        date_from, date_to = get_yesterday_date_range()
        
        self.write({
            'date_from': date_from,
            'date_to': date_to,
        })
        return self._return_wizard_action()

    def action_set_week(self):
        self.ensure_one()
        date_from, date_to = get_week_date_range()
        
        self.write({
            'date_from': date_from,
            'date_to': date_to,
        })
        return self._return_wizard_action()

    def action_set_month(self):
        self.ensure_one()
        date_from, date_to = get_month_date_range()
        
        self.write({
            'date_from': date_from,
            'date_to': date_to,
        })
        return self._return_wizard_action()

    def _return_wizard_action(self):
        """Helper method to return the wizard form view"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        } 