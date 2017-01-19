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
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class ProductCostTransport(orm.Model):
    """ Product Cost Transport method
    """    
    _name = 'product.cost.transport'
    _description = 'Transport method'
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'cost': fields.float('Transport cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Transport cost in company currency', required=True),
        'volume': fields.float('Total volume (M3)', 
            digits=(16, 2), required=True), 
        'note': fields.text('Note'),
        }
    
class ProductCostMethod(orm.Model):
    """ Product cost method
    """    
    _name = 'product.cost.method'
    _description = 'Cost method'
    
    _columns = {
        'name': fields.char('Rule', size=64, required=False),        
        'category': fields.selection([
            ('company', 'F / Company (base: supplier cost)'),
            ('customer', 'F / Customer (base: company cost)'),
            ('pricelist', 'Pricelist (base: customer cost)'),
            ], 'Category', required=True, 
            help='Used for get the cost to update, cost f/company, f/customer'
                'pricelist'),
        'transport_id': fields.many2one(
            'product.cost.transport', 'Transport'),
        'force_exchange': fields.float('Force exchange', digits=(16, 2)),    
        'round': fields.integer('Decimal subtotal', required=True,
            help='Round number of decimal, 2 means 15.216 > 15.22'),    
        # TODO add selection for round only final result    
        'note': fields.text('Note'),
        }

    _defaults = {
        'category': lambda *x: 'company',            
        'round': lambda *x: 2,
        }

class ProductCostRule(orm.Model):
    """ Product cost rule
    """    
    _name = 'product.cost.rule'
    _description = 'Cost rule'
    _order = 'sequence,id'
    
    _columns = {
        'sequence': fields.integer('Sequence'),
        'name': fields.char('Description', size=64, required=True),        
        'method_id': fields.many2one(
            'product.cost.method', 'Method', ondelete='cascade'),
        'operation': fields.selection([
            ('discount', 'Discount % (-)'),
            ('duty', 'Duty % (+)'),
            ('exchange', 'Exchange (x)'),
            ('transport', 'Tranport (Vol. x transport)'),
            ('recharge', 'Recharge % (+)'),
            ('approx', 'Approx'), # Ex.: 0.01 or 1 
            ], 'Operation', required=True,
            help='Operation type set the base for operation and type of '
                'operator and also the sign'),
        'mode': fields.selection([
            ('fixed', 'Fixed'),
            ('percentual', 'Percentual'),
            ], 'Cost mode', required=True),
        'value': fields.float(
            'Value', digits_compute=dp.get_precision('Product Price')),
        'note': fields.char('Note', size=80),
        }
        
    _defaults = {
        'operation': lambda *x: 'recharge',
        'mode': lambda *x: 'percentual',
        }    

class ProductCostMethod(orm.Model):
    """ Product cost method
    """    
    _inherit = 'product.cost.method'
    
    _columns = {
        'rule_ids': fields.one2many('product.cost.rule', 'method_id', 'Rule'), 
        }

class ProductProduct(orm.Model):
    """ Model name: Product Product
    """    
    _inherit = 'product.product'

    # Utility: 
    def get_duty_product_rate(self, cr, uid, duty, country_id, context=None):
        ''' Utility for return duty range from duty browse category and
            country ID of first supplier
        '''
        for tax in duty.tax_ids:
            if tax.country_id.id == country_id:
                return tax.tax
        return 0.0
        
    def get_volume_single_product(self, cr, uid, product, context=None):
        ''' Calculate volume with default pack or multipackage if present
        '''
        volume = 0        
        if product.has_multipackage:
            for pack in product.multi_pack_ids:
                for loop in range(0, pack.number or 1):
                    #res.append('%s x %s x %s' % (
                    #    pack.height, pack.width, pack.length,
                    #    ))
                    volume += pack.height * pack.width * pack.length \
                        / 1000000.0                    
        else:
            #res.append('%s x %s x %s' % (
            #    product.pack_l, product.pack_h, product.pack_p
            #    ))
            
            q_x_pack = product.q_x_pack or 1 # min 1
            volume = \
                product.pack_l * product.pack_h * product.pack_p \
                / 1000000.0 / q_x_pack
        return volume        

        
    # -------------------------------------------------------------------------
    #                           Compute method:
    # -------------------------------------------------------------------------
    def get_product_cost_value(self, cr, uid, ids, 
            block='company', context=None):
        ''' Utility for generate cost for product template passed
            ids: list of product ID
            block: name of field that idendify cost method 
                (company, customer, pricelist)
        '''
        for product in self.browse(cr, uid, ids, context=context):
            # Reset variable used:
            calc = ''
            error = ''
            warning = ''
            supplier_id = product.first_supplier_id.id
            country_id = product.first_supplier_id.country_id.id
            
            # -----------------------------------------------------------------
            #         Get parameter depend on block selected:
            # -----------------------------------------------------------------
            if block == 'company':
                total = product.standard_price
                result_field = 'company_cost'
                base_description = _('Supplier cost')
            elif block == 'customer':            
                total = product.company_cost
                result_field = 'customer_cost'
                base_description = _('Company cost')
            elif block == 'pricelist':
                total = product.customer_cost
                result_field = 'lst_price'
                base_description = _('Customer cost')
            else:
                self.write(cr, uid, product.id, {
                    error_field: _('''
                        <p><font color="red">Block selection error: %s
                        </font></p>''') % block,
                        
                    }, context=context)
                continue
            
            # Field name depend on block name:
            calc_field = '%s_calc' % block
            error_field = '%s_calc_error'% block
            warning_field = '%s_calc_warning' % block
    
            # Bloced error:
            if not total:
                self.write(cr, uid, product.id, {
                    calc_field: False,
                    error_field: _('''
                        <p><font color="red">Base price is empty (%s)
                        </font></p>''') % block,
                    warning_field: False,    
                    }, context=context)
                continue
                
            # -----------------------------------------------------------------
            #                  Process all the rules:    
            # -----------------------------------------------------------------
            method = product.__getattribute__('%s_method_id' % block)
            transport = method.transport_id
            round_decimal = method.round
            float_mask = '%s10.%sf' % ('%', round_decimal)
            
            calc += '''
                <tr> 
                    <td>0</td>
                    <td>Base: %s</td>
                    <td>&nbsp;</td>
                    <td style="text-align:right"><b>%s</b></td>
                </tr>''' % (
                    base_description,
                    float_mask % total,
                    )
            
            for rule in method.rule_ids:                
                # Rule parameter (for readability):
                value = rule.value
                                    
                # Read rule field used:                    
                mode = rule.mode
                operation = rule.operation
                
                # -------------------------------------------------------------
                #                       DISCOUNT RULE:
                # -------------------------------------------------------------
                if operation == 'discount':
                    base = total

                    if not value:
                        error += _('''
                            <p><font color="red">
                                Discount rate not found!!!
                            </font></p>''')
                        continue

                    # value depend on mode:
                    if mode == 'percentual':
                        discount_value = total * value / 100.0
                    elif mode == 'fixed':
                        discount_value = value
                        
                    total -= discount_value
                    total = round(total, round_decimal)
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td style="text-align:right">%s</td>
                        </tr>''' % (
                            rule.sequence,
                            _('- Discount %s%s') % (
                                value,
                                '' if mode == 'fixed' else '%',
                                ),
                            value if mode == 'fixed' else \
                                '%s x %s = %s' % (
                                    base, 
                                    value, 
                                    discount_value,
                                    ),
                            float_mask % total,
                            )    

                # -------------------------------------------------------------
                #                          DUTY RULE:
                # -------------------------------------------------------------
                elif operation == 'duty':
                    # -------------------------------------
                    # Check mandatory fields for duty calc:
                    # -------------------------------------
                    if not supplier_id: 
                        error += _('''
                        <p><font color="red">
                            First supplier not found!</font>
                        </p>''')
                        continue # next rule
                        
                    if not country_id: 
                        error += _('''
                        <p><font color="red">
                            Country for first supplier not found!</font>
                        </p>''''<p>')
                        continue # next rule

                    duty = product.duty_id                    
                    # Check duty category presence:
                    if not duty and not product.is_duty_set: 
                        error += _('''
                        <p><font color="red">
                            Duty category not setted on product
                            And product is not a duty set!
                            </font>
                        </p>''')
                        continue
                    
                    # Get duty rate depend on supplier country
                    base = total
                    duty_value = 0.0
                    if product.is_duty_set:
                        for duty_set in product.duty_set_ids:
                            duty_rate = self.get_duty_product_rate(
                                cr, uid, duty_set.duty_id, 
                                country_id, context=context)
                            duty_value += (base * duty_set.partial / 100.0) * (
                                duty_rate / 100.0)
                    else: # no set
                        duty_rate = self.get_duty_product_rate(
                             cr, uid, duty, country_id, 
                             context=context)
                        duty_value = base * duty_rate / 100.0
    
                    # Check duty rate value (:
                    if not duty_value: 
                        warning += _('''
                        <p><font color="orange">
                            Duty value is zero!</font>
                        </p>''')
                    
                    total += duty_value
                    total = round(total, round_decimal)
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td style="text-align:right"><b>%s</b></td>
                        </tr>''' % (
                            rule.sequence,
                            _('''+ Duty %s%s<br/>
                                <i><font color="grey">[%s-%s]</font></i>
                            ''') % (
                                '(set)' if product.is_duty_set else duty_rate,
                                '%',
                                _('Different duty categ.') if \
                                    product.is_duty_set \
                                    else product.duty_id.name,
                                product.first_supplier_id.country_id.name,
                                ),
                            '%s x %s = %s' % (base, duty_rate, duty_value) if \
                                not product.is_duty_set else duty_value,
                            float_mask % total,
                            )    

                # -------------------------------------------------------------
                #                         EXCHANGE RULE:
                # -------------------------------------------------------------
                elif operation == 'exchange':
                    base = total
                    comment = ''
                    # Read exchange:
                    if method.force_exchange: # method
                        comment = _('(Met.)')    
                        exchange_rate = method.force_exchange
                    else:
                        supplier = product.first_supplier_id
                        if supplier:
                            comment = _('(Suppl.)')    
                            if supplier.cost_currency_id:
                                exchange_rate = \
                                    supplier.cost_currency_id.rate_silent_cost
                            else:
                                exchange_rate = 1.0 # EUR
                                warning += _('''
                                    <p><font color="orange">
                                        No currency in supplier use 1
                                    </font></p>''')
                        else:
                            exchange_rate = 0.0
                        
                    if not exchange_rate: # no exchange (value 0):
                        error += _('''
                            <p><font color="red">
                                Exchange value not found (currency and method)!                                
                            </font></p>''')
                        continue
                               
                    total /= exchange_rate
                    total = round(total, round_decimal)
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s %s</td>
                            <td>%s</td>
                            <td style="text-align:right">%s</td>
                        </tr>''' % (
                            rule.sequence,
                            _(': Exchange %s') % exchange_rate,
                            comment,
                            '%s : %s' % (
                                base, exchange_rate),
                            float_mask % total,
                            )    

                # -------------------------------------------------------------
                #                         TRANSPORT RULE:
                # -------------------------------------------------------------
                elif operation == 'transport':
                    comment = ''
                    # Check mandatory element for transport:
                    if transport:
                        comment = _('(Metod)')
                    elif product.first_supplier_id and \
                            product.first_supplier_id.transport_id:
                        comment = _('(Suppl.)')
                        transport = product.first_supplier_id.transport_id
                    else:    
                        error += _('''
                            <p><font color="red">
                                Setup transport in cost method %s or 
                                partner!
                            </font></p>''') % block
                        continue
                    # Calculate date depend on tranport choosed    
                    transport_cost = transport.cost
                    transport_volume = transport.volume
                    transport_id = transport.id
                        
                    # Search in tranport-product relation
                    q_x_tran = 0
                    for prod_tran in product.transport_ids:
                        if prod_tran.transport_id.id == transport.id:
                            q_x_tran = prod_tran.quantity
                            break
                    
                    if q_x_tran: # Calculate with q x tran                                
                        cost1 = transport_cost / q_x_tran
                        total += cost1
                        total = round(total, round_decimal)

                        calc += '''
                            <tr>
                                <td>%s</td>
                                <td>%s %s</td>
                                <td>%s</td>
                                <td style="text-align:right">%s</td>
                            </tr>''' % (
                                rule.sequence,
                                _('+ Transport (sett.)'),
                                comment,
                                '%s / %s = %s' % (
                                    transport_cost, 
                                    q_x_tran,
                                    cost1,
                                    ),
                                float_mask % total,
                                )                        
                    else:
                        # Calculated fields:
                        volume1 = self.get_volume_single_product(
                            cr, uid, product, context=context)
                        
                        # Check mandatory volume
                        if not volume1:
                            error += _('''
                                <p><font color="red">
                                    Volume x piece not present!!!
                                </font></p>''')
                            continue

                        if not transport_volume:
                            error += _('''
                                <p><font color="red">
                                    No transport total volume present!!!
                                </font></p>''')
                            continue
                                                
                        pc_x_trans = transport_volume / volume1
                        cost1 =  transport_cost / int(pc_x_trans) # cut down
                        total += cost1
                        total = round(total, round_decimal)
                        warning += _('''
                        <p><font color="orange">
                            Transport is optimistic because based on volume
                            not on pcs x tranport in product form!
                            </font>
                        </p>''')

                        calc += '''
                            <tr>
                                <td>%s</td>
                                <td>%s %s</td>
                                <td>%s</td>
                                <td style="text-align:right">%s</td>
                            </tr>''' % (
                                rule.sequence,
                                _('+ Transport (calc.)<br/>'
                                    '<i><font color="orange">'
                                    '[pcs/tr. %s > %s]'
                                    '</font></i>') % (
                                        pc_x_trans, int(pc_x_trans)),
                                comment,        
                                '%s / %s = %s' % (
                                    transport_cost, 
                                    int(pc_x_trans), 
                                    cost1,
                                    ),
                                float_mask % total,
                                )    

                # -------------------------------------------------------------
                #                          RECHARGE RULE:
                # -------------------------------------------------------------
                elif operation == 'recharge':
                    base = total

                    if not value:
                        error += _('''
                            <p><font color="red">
                                Recharge rate not found!!!
                            </font></p>''')
                        continue
                        
                    # value depend on mode:
                    if mode == 'percentual':
                        recharge_value = total * value / 100.0
                    elif mode == 'fixed':
                        recharge_value = value
                    
                    total += recharge_value
                    total = round(total, round_decimal)
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td style="text-align:right">%s</td>
                        </tr>''' % (
                            rule.sequence,
                            _('+ Rechange %s%s') % (
                                value,
                                '' if mode == 'fixed' else '%',
                                ),
                            value if mode == 'fixed' else \
                                '%s x %s = %s' % (
                                    base, 
                                    value, 
                                    recharge_value,
                                    ),
                            float_mask % total,
                            )    

                # -------------------------------------------------------------
                #                          APPROX RULE:
                # -------------------------------------------------------------
                elif operation == 'approx':
                    if not value:
                        error += _('''
                            <p><font color="red">
                                Approx need to be setup (es. 0,01)!
                            </font></p>''')
                        continue
                    
                    total = (total / value)
                    total = round(total, 0) * value # int round
                    
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td></td>
                            <td style="text-align:right">%s</td>
                        </tr>''' % (
                            rule.sequence,
                            _('= Round %s') % value,
                            float_mask % total,
                            )    

            # -----------------------------------------------------------------
            #                     Write data in product:
            # -----------------------------------------------------------------
            self.write(cr, uid, product.id, {
                result_field: total,
                calc_field: _('''
                    <table>
                        <tr>
                            <th>Seq.</th>
                            <th>Description</th>
                            <th>Calculation</th>
                            <th>Subtotal</th>
                        </tr>%s
                    </table>''') % calc, # embed in table
                error_field: error,
                warning_field: warning,
                }, context=context)                
        return True
    
    # 3 Button:
    def calculate_cost_method_company(self, cr, uid, ids, context=None):
        ''' Button calculate
        '''
        return self.get_product_cost_value(cr, uid, ids, 
            block='company', context=context)

    def calculate_cost_method_customer(self, cr, uid, ids, context=None):
        ''' Button calculate
        '''
        return self.get_product_cost_value(cr, uid, ids, 
            block='customer', context=context)

    def calculate_cost_method_pricelist(self, cr, uid, ids, context=None):
        ''' Button calculate
        '''
        return self.get_product_cost_value(cr, uid, ids, 
            block='pricelist', context=context)

class ProductProductTransport(orm.Model):
    """ Model name: ProductProduct
    """
    
    _name = 'product.product.transport'
    _description = 'Product transport'
    _rec_name = 'product_id'
    
    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product'),
        'transport_id': fields.many2one(
            'product.cost.transport', 'Transport', required=True),
        'calc_note': fields.text('Calc. note', readonly=True) ,    
        'quantity': fields.integer('Quantity', required=True),
        }
    
class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'
    
    # Button
    def open_normal_form_view(self, cr, uid, ids, context=None):
        '''
        '''
        model_pool = self.pool.get('ir.model.data')
        form_id = model_pool.get_object_reference(
            cr, uid, 'product', 'product_normal_form_view')[1]
    
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cost manage'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_id': ids[0],
            'res_model': 'product.product',
            'view_id': form_id, # False
            'views': [(form_id, 'form'), (False, 'tree')],
            'domain': [],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }
    def open_cost_form_view(self, cr, uid, ids, context=None):
        '''
        '''
        model_pool = self.pool.get('ir.model.data')
        form_id = model_pool.get_object_reference(
            cr, uid, 'product_cost_rule', 'view_product_product_cost_form')[1]
    
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cost manage'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_id': ids[0],
            'res_model': 'product.product',
            'view_id': form_id, # False
            'views': [(form_id, 'form'), (False, 'tree')],
            'domain': [],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }
    
    _columns = {
        # 3 Method:
        'company_method_id': fields.many2one(
            'product.cost.method', 'Company Method'),
        'customer_method_id': fields.many2one(
            'product.cost.method', 'Customer Method'),
        'pricelist_method_id': fields.many2one(
            'product.cost.method', 'Pricelist Method'),
            
        # 3 Text result:    
        'company_calc': fields.text(
            'Company calc', readonly=True),
        'customer_calc': fields.text(
            'Customer calc', readonly=True),    
        'pricelist_calc': fields.text(
            'Pricelist calc', readonly=True),    
            
        # 3 Text calc error:
        'company_calc_error': fields.text(
            'Company calc error', readonly=True),
        'customer_calc_error': fields.text(
            'Customer calc error', readonly=True),
        'pricelist_calc_error': fields.text(
            'Pricelist calc error', readonly=True),

        # 3 Text calc warning:
        'company_calc_warning': fields.text(
            'Company calc warning', readonly=True),
        'customer_calc_warning': fields.text(
            'Customer calc warning', readonly=True),
        'pricelist_calc_warning': fields.text(
            'Pricelist calc warning', readonly=True),
        
        # XXX supplier_cost >> standard_price
        #'supplier_cost': fields.float('Cost FOB',
        #    digits_compute=dp.get_precision('price_accuracy'), 
        #    help='Supplier cost (pricelist cost, f/company)'),
        'company_cost': fields.float('Cost FCO/Company', 
            digits_compute=dp.get_precision('price_accuracy'), 
            help='Supplier cost (pricelist cost, f/company)'),
        'customer_cost': fields.float('Cost FCO/Customer', 
            digits_compute=dp.get_precision('price_accuracy'), 
            help='Customer cost (base for calculate goods f/customer)'),
        
        'cost_currency_id': fields.related(
            'first_supplier_id', 'cost_currency_id', 
            type='many2one', relation='res.currency', 
            string='Partner cost currency', readonly=True),
        
        'transport_ids': fields.one2many(
            'product.product.transport', 'product_id', 
            'Transport'),
        }

class ResCurrency(orm.Model):
    """ Model name: Res Currency
    """    
    _inherit = 'res.currency'

    _columns = {
        'rate_silent_cost': fields.float('Rate for cost', digits=(16, 4), 
            help='Used for convert supplier cost in pricelist generation'),        
        }

class ResPartner(orm.Model):
    """ Model name: ResPartner
    """    
    _inherit = 'res.partner'
    
    _columns = {
        'transport_id': fields.many2one(
            'product.cost.transport', 'Default transport'),
        'cost_currency_id': fields.many2one(
            'res.currency', 'Currency for cost',
            help='currency for supplier cost value, used also to get exchange'
                'value for conversiono'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
