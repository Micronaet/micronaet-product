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
            help='Transport cost in company currency', required=False),
        'cube_meter': fields.float('M3 total', digits=(16, 2), required=False), 
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
            ('multi', 'Multi percentual'),
            ], 'Cost mode', required=True),
        'value': fields.float(
            'Value', digits_compute=dp.get_precision('Product Price')),
        'text_value': fields.char('Text value', size=30, 
            help='Used for multi discount element'),
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


class ProductTemplate(orm.Model):
    """ Model name: ProductTemplate
    """    
    _inherit = 'product.template'
    
    # -------------------------------------------------------------------------
    #                           Compute method:
    # -------------------------------------------------------------------------
    def get_product_cost_value(self, cr, uid, product, 
            field='company_method_id', context=context):
        ''' Utility for generate cost for product template passed
            product: browse obj for product
            field: name of field that idendity cost method
        '''
        
        return True
    
    """def get_campaign_price(self, cost, price, campaign, product, cost_type):
        # ---------------------------------------------------------------------
        # Product cost generation:
        # ---------------------------------------------------------------------
        total = 0.0
        for rule in cost_type.rule_ids:
            # Read rule parameters
            sign = rule.sign
            base = rule.base
            mode = rule.mode
            value = rule.value
            text_value = rule.text_value
            
            # -----------
            # Sign coeff:
            # -----------
            if sign == 'minus':
                sign_coeff = -1.0  
            else:
                sign_coeff = 1.0
                
            # ----------------
            # Base evaluation:
            # ----------------
            if base == 'previous':
                base_value = total
            elif base == 'cost':
                base_value = cost
                if not total: # Initial setup depend on first rule
                    total = cost 
            elif base == 'price':
                base_value = price
                if not total: # Initial setup depend on first rule
                    total = price
            #elif base == 'volume':
            #    base_value = (
            #        product.volume / campaign.volume_total)                    
            else:
                _logger.error('No base value found!!!')                
                # TODO raise error?        

            # -----------
            # Value type:
            # -----------
            if mode == 'fixed':
                total += sign_coeff * value
                continue # Fixed case only increment total no other operations                
            elif mode == 'multi':
                # TODO check sign for multi discount value (different from revenue)
                # Convert multi discount with value
                value = sign_coeff * partner_pool.format_multi_discount(
                    text_value).get('value', 0.0)
            elif mode == 'percentual':
                value *= sign_coeff
            else:    
                _logger.error('No mode value found!!!')
                # TODO raise error?        
                    
            if not value:
                _logger.error('Percentual value is mandatory!')
                pass
            total += base_value * value / 100.0

        # --------------------------------
        # General cost depend on campaign:    
        # --------------------------------
        volume_cost = campaign.volume_cost
        discount_scale = campaign.discount_scale
        revenue_scale = campaign.revenue_scale
        
        # TODO correct!!!!:
        if volume_cost:        
            total += total * product.qty * (
                product.volume / campaign.volume_total)
            # TODO use heigh, width, length 
            # TODO use pack_l, pack_h, pack_p
            # TODO use packaging dimension?
            
        if discount_scale:
            discount_value = partner_pool.format_multi_discount(
                discount_scale).get('value', 0.0)
            total -= total * discount_value / 100.0

        if revenue_scale:
            revenue_value = partner_pool.format_multi_discount(
                revenue_scale).get('value', 0.0)
            total += total * revenue_value / 100.0
            
        # TODO extra recharge:
        return total"""
    
    _columns = {
        'company_method_id': fields.many2one(
            'product.cost.method', 'Company Method'),
        'customer_method_id': fields.many2one(
            'product.cost.method', 'Customer Method'),
        'pricelist_method_id': fields.many2one(
            'product.cost.method', 'Pricelist Method'),
        
        'supplier_cost': fields.float('Supplier cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Supplier cost (pricelist cost, f/company)'),
        'customer_cost': fields.float('Customer cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Customer cost (base for calculate goods f/customer)'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
