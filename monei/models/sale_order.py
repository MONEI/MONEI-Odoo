from odoo import models, fields, api, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    monei_payment_count = fields.Integer(
        string='Payment Count',
        compute='_compute_monei_payment_count'
    )
    monei_payment_ids = fields.One2many(
        'monei.payment',
        'sale_order_id',
        string='MONEI Payments'
    )

    def _compute_monei_payment_count(self):
        for order in self:
            order.monei_payment_count = len(order.monei_payment_ids)

    def action_view_monei_payments(self):
        self.ensure_one()
        return {
            'name': _('MONEI Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'monei.payment',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'create': False},
        } 