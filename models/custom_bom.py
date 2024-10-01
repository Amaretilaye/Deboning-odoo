from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CustomBom(models.Model):
    _name = 'custom.bom'
    _description = 'Custom Bill of Materials for Deboning'

    name = fields.Char(string='BoM Reference', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True, domain=[('type', '=', 'product')])
    quantity = fields.Float(string='Quantity (Kg)', required=True, default=1.0)
    line_ids = fields.One2many('custom.bom.line', 'bom_id', string='BoM Lines')

    @api.constrains('product_id')
    def _check_unique_product(self):
        for record in self:
            # Search for other CustomBom records with the same product_id
            existing_boms = self.search([
                ('product_id', '=', record.product_id.id),
                ('id', '!=', record.id)
            ])
            if existing_boms:
                raise ValidationError("The product '%s' is already assigned to another BoM." % (record.product_id.name,))

class CustomBomLine(models.Model):
    _name = 'custom.bom.line'
    _description = 'Custom BoM Line'

    bom_id = fields.Many2one('custom.bom', string='Custom BoM', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True)
