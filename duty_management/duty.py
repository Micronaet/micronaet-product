# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
from openerp.osv import fields, osv, expression, orm
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class ProductProductDutyExtraData(orm.Model):
    """ Duty extra data
    """
    _name = 'product.product.duty.extra.data'
    _description = 'Product Extra data'
    _order = 'mask'

    def linked_all(self, cr, uid, ids, context=None):
        """ Current record linked
        """
        product_pool = self.pool.get('product.product')

        rule_ids = self.search(cr, uid, [
            ('unused', '=', False),
        ], context=context)

        for rule in self.browse(cr, uid, rule_ids, context=context):
            rule_id = role.id
            mask = rule.mask
            cr.execute('''
                SELECT id FROM product_product 
                WHERE default_code ilike '%s';
                ''' % mask)
            product_ids = [p[0] for p in cr.fetchall()]
            total = len(product_ids)
            if product_ids:
                _logger.info('Updating %s product with rule: %s' % (
                    total,
                    mask,
                ))
                product_pool.write(cr, uid, product_ids, {
                    'extra_data_id': rule_id,
                }, context=context)
            else:
                _logger.info('Not found product with mask: %s' % mask)
            # Update totals:
            self.write(cr, uid, [rule_id], {
                'total': total,
            }, context)
        return True

    def current_linked(self, cr, uid, ids, context=None):
        """ Current record linked
        """
        product_pool = self.pool.get('product.product')
        product_ids = product_pool.search(cr, uid, [
            ('extra_data_id', '=', ids[0]),
            ], context=context)

        if not product_ids:
            raise osv.except_osv(
                _('Attenzione'),
                _('Non trovati prodotti abbinati a questa regola'),
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotti abbinati'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'res_id': 1,
            'res_model': 'product.product',
            'view_id': False,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', product_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }

    def current_masked(self, cr, uid, ids, context=None):
        """ Current record masked with this selection
        """
        extra_data = self.browse(cr, uid, ids, context=context)[0]
        mask = extra_data.mask

        cr.execute('''
            SELECT id FROM product_product 
            WHERE default_code ilike '%s';
            ''' % mask)
        product_ids = [p[0] for p in cr.fetchall()]

        if not product_ids:
            raise osv.except_osv(
                _('Attenzione'),
                _('Non trovati prodotti con questa maschera'),
            )
        # model_pool = self.pool.get('ir.model.data')
        # view_id = model_pool.get_object_reference(
        # 'module_name', 'view_name')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotti con maschera'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'res_id': 1,
            'res_model': 'product.product',
            'view_id': False,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', product_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }

    _columns = {
        'mask': fields.char(
            'Maschera codice', size=20, required=True,
            help='Maschera per abbinare il dato ai prodotti'),
        'name': fields.char('Name', size=50, required=True),
        'price': fields.float('Prezzo', digits=(10, 2), required=True),
        'unused': fields.boolean('Non usare'),
        'total': fields.integer('Totale', help='Totale di prodotti trovati'),

        'width': fields.float('W', digits=(10, 2)),
        'length_from': fields.float('L (da)', digits=(10, 2)),
        'length_to': fields.float('L (a)', digits=(10, 2)),
        'height_from': fields.float('H (da)', digits=(10, 2)),
        'height_to': fields.float('H (a)', digits=(10, 2)),

        'seat': fields.float('Seduta', digits=(10, 2)),
        'harm': fields.float('Bracciolo', digits=(10, 2)),
        'pipe_diameter': fields.char('Diam. tubo', size=30),

        'box_length': fields.float('L (scatola)', digits=(10, 2)),
        'box_width': fields.float('W (scatola)', digits=(10, 2)),
        'box_height': fields.float('H (scatola)', digits=(10, 2)),

        'weight_net': fields.float('Peso netto', digits=(10, 2)),
        'weight': fields.float('Peso lordo', digits=(10, 2)),

        'pallet_piece': fields.integer('Pz (pallet)'),
        'track_piece': fields.integer('Pz (camion)'),

        'pallet_length': fields.float('L (pallet)', digits=(10, 2)),
        'pallet_width': fields.float('W (pallet)', digits=(10, 2)),
        'pallet_height': fields.float('H (pallet)', digits=(10, 2)),
    }


class ProductProduct(orm.Model):
    """ Duty extra data
    """
    _inherit = 'product.product'

    _columns = {
        'extra_data_id': fields.many2one(
            'product.product.duty.extra.data', 'Extra data')
        }


class AccountFiscalPosition(orm.Model):
    """ Cost for country to import in Italy
    """
    _inherit = 'account.fiscal.position'

    _columns = {
        'duty_print': fields.boolean('Stampa codice doganale'),
        }


class AccountInvoice(orm.Model):
    """ Custom duty block
    """
    _inherit = 'account.invoice'

    # Override default Workflow action:
    def invoice_validate(self, cr, uid, ids, context=None):
        """ Override default action for write custom duty box:
        """
        res = super(AccountInvoice, self).invoice_validate(
            cr, uid, ids, context=context)

        # If Extra CEE generate Duty box:
        invoice = self.browse(cr, uid, ids, context=context)[0]
        if invoice.fiscal_position.duty_print and not invoice.duty_block:
            try:
                self.generate_duty_block(cr, uid, ids, context=context)
            except:
                _logger.error('Errore generating duty box')

        return res

    def generate_duty_block(self, cr, uid, ids, context=None):
        """ Button event for generate duty block
        """
        assert len(ids) == 1, 'Funziona per una fattura alla volta!'

        invoice = self.browse(cr, uid, ids, context=context)[0]
        if not invoice.fiscal_position.duty_print:
            return False

        table = {}
        error = ''
        for line in invoice.invoice_line:
            product = line.product_id
            duty_code = product.duty_code
            quantity = line.quantity
            net = product.weight_net
            gross = product.weight

            if not duty_code:
                continue
            if duty_code not in table:
                table[duty_code] = [0.0, 0.0, 0.0]  # Amount, net, gross
            table[duty_code][0] += line.price_subtotal  # Subtotal amount
            table[duty_code][1] += net * quantity  # W. net
            table[duty_code][2] += gross * quantity  # W. gross

            if not net:
                error += '%s >> Peso netto mancante\n' % product.default_code
            if not gross:
                error += '%s >> Peso lordo mancante\n' % product.default_code

        res = 'Custom table:\n'
        for duty_code in sorted(table):
            res += u'Code %s: %.2f € [Net: %s Kg - Gross %s Kg]\n' % (
                duty_code, table[duty_code][0],
                table[duty_code][1], table[duty_code][2]
                )

        if error:
            error = 'ERRORI:\n%s' % error
        return self.write(cr, uid, ids, {
            'duty_block': res,
            'duty_error': error,
            }, context=context)

    _columns = {
        'duty_block': fields.text('Tabella doganale'),
        'duty_error': fields.text('Errori calcolo doganale'),
        }


class ProductCustomDutyTax(orm.Model):
    """ Cost for country to import in Italy
    """
    _name = 'product.custom.duty.tax'
    _description = 'Product custom duty tax'
    _rec_name = 'tax'

    _columns = {
        'tax': fields.float('% Tax', digits=(8, 3)),
        'country_id': fields.many2one('res.country', 'Country', required=True),
        'duty_id': fields.many2one('product.custom.duty', 'Duty code'),
        }


class ProductCustomDuty(orm.Model):
    """ Anagrafic to calculate product custom duty depending of his category
        (using % of tax per supplier cost)
    """
    _name = 'product.custom.duty'
    _description = 'Product custom duty'

    def load_product_duty_category(self, cr, uid, connector_id, context=None):
        """ Assign category to product selected
        """
        res = {}
        category_ids = self.search(cr, uid, [
            ('start', '!=', False),
            ], context=context)
        for category in self.browse(cr, uid, category_ids, context=context):
            for start in category.start.split('|'):
                res[start] = category.id
        return res

    _columns = {
        'name': fields.char('Custom duty', size=100, required=True),
        'code': fields.char('Code', size=24),
        # TODO remove:
        'start': fields.text(
            'Start code',
            help='Write start code as: 127|027|029'),
        'tax_ids': fields.one2many(
            'product.custom.duty.tax', 'duty_id', '% Tax'),
        }


class ProductProductExtra(orm.Model):
    _inherit = 'product.product'

    # todo override write or create element for generate duty code!!!!!!!!!!!!
    _columns = {
        'duty_id': fields.many2one('product.custom.duty', 'Custom duty'),
        'duty_code': fields.related(
            'duty_id', 'code', type='char', string='Duty code', readonly=True),
        # 'dazi': fields.float('Dazi (USD)', digits=(16, 2)),
        # 'dazi_eur': fields.function(_get_full_calculation, method=True,
        #    type='float', string='Dazi (EUR)', digits=(16, 2), store=False,
        #    multi="total_cost"),
        }
