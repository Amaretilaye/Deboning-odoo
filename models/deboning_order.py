from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class DeboningOrder(models.Model):
    _name = 'deboning.order'
    _description = 'Deboning Order'
    _order = 'order_datetime desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_datetime = fields.Datetime(string='Order Date & Time', default=fields.Datetime.now, required=True)
    name = fields.Char(string='Order Reference', required=True, default='New')
    custom_bom_id = fields.Many2one('custom.bom', string='BoM Product', required=True, ondelete='cascade')
    quantity = fields.Float(string='Quantity (Kg)', required=True, default=1)
    line_ids = fields.One2many('deboning.order.line', 'order_id', string='Deboning Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True,
                                   default=lambda self: self._get_default_warehouse())

    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)


    @api.model
    def _get_default_warehouse(self):
        """Get the default warehouse based on the user's allowed warehouses."""
        user = self.env.user
        if user.allowed_warehouses_ids:
            return user.allowed_warehouses_ids[0]  # Return the first allowed warehouse
        return self.env['stock.warehouse'].search([], limit=1)


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('deboning.order') or 'New'
        return super(DeboningOrder, self).create(vals)

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    def action_back_to_draft(self):
        for record in self:
            record.state = 'draft'

    @api.onchange('custom_bom_id', 'quantity')
    def _onchange_custom_bom_or_quantity(self):
        """Update deboning order lines based on the selected BoM and quantity."""
        if self.custom_bom_id:
            self.line_ids = [(5, 0, 0)]  # Clear existing lines
            bom_total_quantity = self.custom_bom_id.quantity

            lines = []
            for bom_line in self.custom_bom_id.line_ids:
                lines.append((0, 0, {
                    'product_id': bom_line.product_id.id,
                    'quantity': (bom_line.quantity / bom_total_quantity) * self.quantity,
                }))
            self.line_ids = lines

    def action_done(self):
        self._update_product_quantities()
        self.state = 'done'

    def _update_product_quantities(self):
        """Update the quantity in stock.quant based on deboning lines."""
        for order in self:
            # Deduct the main product (whole chicken) from stock
            main_product = order.custom_bom_id.product_id
            main_warehouse = order.line_ids[0].warehouse_id  # Assuming all lines use the same warehouse
            main_location = main_warehouse.lot_stock_id

            # Find the stock.quant for the main product and location
            main_quant = self.env['stock.quant'].search([
                ('product_id', '=', main_product.id),
                ('location_id', '=', main_location.id)
            ], limit=1)

            if not main_quant or main_quant.quantity < order.quantity:
                raise ValidationError(
                    "Insufficient stock for the main product '%s' in location '%s'. Available quantity is %s, but %s is required." % (
                        main_product.name, main_location.name, main_quant.quantity if main_quant else 0, order.quantity)
                )

            # Deduct the main product quantity from stock
            main_quant.write({'quantity': main_quant.quantity - order.quantity})

            # Update the stock for each product in the deboning lines
            for line in order.line_ids:
                product = line.product_id
                warehouse = line.warehouse_id
                location = warehouse.lot_stock_id

                # Find or create a stock.quant for the product and location
                quant = self.env['stock.quant'].search([
                    ('product_id', '=', product.id),
                    ('location_id', '=', location.id)
                ], limit=1)

                if quant:
                    quant.write({'quantity': quant.quantity + line.quantity})
                else:
                    self.env['stock.quant'].create({
                        'product_id': product.id,
                        'location_id': location.id,
                        'quantity': line.quantity,
                    })





class DeboningOrderLine(models.Model):
    _name = 'deboning.order.line'
    _description = 'Deboning Order Line'

    order_id = fields.Many2one('deboning.order', string='Deboning Order', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Produced Quantity', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True,
                                   default=lambda self: self._get_default_warehouse())
    order_state = fields.Selection(related="order_id.state", string="State")

    @api.model
    def _get_default_warehouse(self):
        """Get the default warehouse based on the user's allowed warehouses."""
        user = self.env.user
        if user.allowed_warehouses_ids:
            return user.allowed_warehouses_ids[0]  # Return the first allowed warehouse
        return self.env['stock.warehouse'].search([], limit=1)
