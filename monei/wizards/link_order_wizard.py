from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MoneiPaymentLinkOrderWizard(models.TransientModel):
    _name = 'monei.payment.link.order.wizard'
    _description = 'Link MONEI Payment to Sale Order'

    payment_id = fields.Many2one('monei.payment', string='Payment', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)

    def action_link(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('Please select a Sale Order.'))
        self.payment_id.write({
            'order_id': self.sale_order_id.name,
            'sale_order_id': self.sale_order_id.id,
        })
        self.payment_id._sync_order_information(self.sale_order_id)
        return {'type': 'ir.actions.act_window_close'} 