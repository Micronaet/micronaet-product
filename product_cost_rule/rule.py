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
            ], 'Category', 
            help='Used for get the cost to update, cost f/company, f/customer'
                'pricelist'),
        'transport_id': fields.many2one(
            'product.cost.transport', 'Transport'),
        'force_exchange': fields.float('Force exchange', digits=(16, 2)),    
        'note': fields.text('Note'),
        }

    _defaults = {
        'category': lambda *x: 'company',            
        }

class ProductCostRule(orm.Model):
    """ Product cost rule
    """    
    _name = 'product.cost.rule'
    _description = 'Cost rule'
    _order = 'sequence,id'
    
    _columns = {
        'sequence': fields.integer('Sequence'),
        'name': fields.char('Description', size=64, required=False),        
        'method_id': fields.many2one(
            'product.cost.method', 'Method', ondelete='cascade'),
        'operation': fields.selection([
            ('discount', 'Discount % (-)'),
            ('duty', 'Duty % (+)'),
            ('exchange', 'Exchange (x)'),
            ('transport', 'Tranport (Vol. x transport)'),
            ('recharge', 'Recharge % (+)'),], 'Operation', required=True,
            help='Operation type set the base for operation and type of '
                'operator and also the sign'),
        'mode': fields.selection([
            ('fixed', 'Fixed'),
            ('percentual', 'Percentual'),
            ], 'Cost mode', required=True),
        'value': fields.float(
            'Value', digits_compute=dp.get_precision('Product Price')),
        'round': fields.integer('Round', required=True,
            help='Round number of decimal, 2 means 15.216 > 15.22'),    
        'note': fields.char('Note', size=80),
        }
        
    _defaults = {
        'operation': lambda *x: 'recharge',
        'mode': lambda *x: 'percentual',
        'round': lambda *x: 2,
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
            product: browse obj for product
            field: name of field that idendify cost method
        '''
        # Database for speed up search:
        duty_db = {} # database of first supplier duty

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
                total = product.supplier_cost                
                result_field = 'standard_price'
                base_description = _('Supplier cost')
            elif block == 'customer':            
                total = product.standard_price
                result_field = 'customer_price'
                base_description = _('Company cost')
            elif block == 'pricelist':
                total = product.customer_cost
                result_field = 'price_lst'
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
    
            if not total:
                self.write(cr, uid, product.id, {
                    error_field: _('''
                        <p><font color="red">Base price is empty (%s)
                        </font></p>''') % block,
                    }, context=context)
                continue
                
            # -----------------------------------------------------------------
            #                  Process all the rules:    
            # -----------------------------------------------------------------
            method = product.__getattribute__('%s_method_id' % block)
            transport = method.transport_id
            calc += '''
                <tr> 
                    <td>0</td>
                    <td>Base: %s</td>
                    <td>&nbsp;</td>
                    <td style="text-align:right"><b>%s</b></td>
                </tr>''' % (
                    base_description,
                    total,
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
                    # value depend on mode:
                    if mode == 'percentual':
                        discount_value = total * value / 100.0
                    elif mode == 'fixed':
                        discount_value = value
                        
                    total -= discount_value
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
                            total,
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
                    if not duty: 
                        error += _('''
                        <p><font color="red">
                            Duty category not setted on product!</font>
                        </p>''')
                        continue
                    
                    # Get duty rate depend on supplier country     
                    if supplier_id not in duty_db:
                        duty_db[supplier_id] = self.get_duty_product_rate(
                            cr, uid, duty, country_id, 
                            context=context)
                    duty_rate = duty_db[supplier_id]
    
                    # Check duty rate value (:
                    if not duty_rate: 
                        warning += _('''
                        <p><font color="orange">
                            Duty rate is 0!</font>
                        </p>''')
                    
                    base = total
                    duty_value = total * duty_rate / 100.0
                    total += duty_value
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
                                duty_rate,
                                '%',
                                product.duty_id.name,
                                product.first_supplier_id.country_id.name,
                                ),
                            '%s x %s = %s' % (base, duty_rate, duty_value),
                            total,
                            )    

                # -------------------------------------------------------------
                #                         EXCHANGE RULE:
                # -------------------------------------------------------------
                elif operation == 'exchange':
                    base = total
                    exchange_rate = method.force_exchange
                    # TODO read it from currency                    
                    exchange_value = total * exchange_rate                        
                    total += exchange_value
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td style="text-align:right">%s</td>
                        </tr>''' % (
                            rule.sequence,
                            _('x Exchange %s') % exchange_rate,
                            '%s x %s = %s' % (
                                base, exchange_rate, exchange_value),
                            total,
                            )    

                # -------------------------------------------------------------
                #                         TRANSPORT RULE:
                # -------------------------------------------------------------
                elif operation == 'transport':
                    # Check mandatory element:
                    if not transport:
                        self.write(cr, uid, product.id, {
                            error_field: _('''
                                <p><font color="red">
                                    No %s transport set up cost method!
                                </font></p>''') % block,
                            }, context=context)
                        continue
                        
                    # Mandatory fields (from view):   
                    transport_cost = transport.cost
                    transport_volume = transport.volume
                    
                    # Calculated fields:
                    volume1 = self.get_volume_single_product(
                        cr, uid, product, context=context)
                    
                    # Check mandatory volume
                    if not volume1:
                        self.write(cr, uid, product.id, {
                            error_field: _('''
                                <p><font color="red">
                                    Volume x piece not present!!!
                                </font></p>'''),
                            }, context=context)
                        continue
                    
                    cost1 = volume1 * transport_cost / transport_volume     
                    total +=  cost1
                    calc += '''
                        <tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td style="text-align:right">%s</td>
                        </tr>''' % (
                            rule.sequence,
                            _('+ Transport (volume)'),
                            '%s x %s / %s = %s' % (
                                volume1, 
                                transport_cost, 
                                transport_volume,
                                cost1,
                                ),
                            total,
                            )    

                # -------------------------------------------------------------
                #                          RECHARGE RULE:
                # -------------------------------------------------------------
                elif operation == 'recharge':
                    base = total
                    # value depend on mode:
                    if mode == 'percentual':
                        recharge_value = total * value / 100.0
                    elif mode == 'fixed':
                        recharge_value = value
                        
                    total += recharge_value
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
                            total,
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

class ProductTemplate(orm.Model):
    """ Model name: ProductTemplate
    """    
    _inherit = 'product.template'
    
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
        
        'supplier_cost': fields.float('Supplier cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Supplier cost (pricelist cost, f/company)'),
        'customer_cost': fields.float('Customer cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Customer cost (base for calculate goods f/customer)'),
        }

class ResPartner(orm.Model):
    """ Model name: ResPartner
    """    
    _inherit = 'res.partner'
    
    _columns = {
        'cost_currency_id': fields.many2one(
            'res.currency', 'Cost currency', 
            help='currency for supplier cost value, used also to get exchange'
                'value for conversiono'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
