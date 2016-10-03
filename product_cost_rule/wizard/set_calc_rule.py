# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


import os
import sys
import logging
import openerp
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class ProductMethodForceCalcWizard(orm.TransientModel):
    ''' Wizard for
    '''
    _name = 'product.method.force.calc.wizard'
    _description = 'Force calc or assign method to product'

    # Utility
    def get_product_filter_selection(self, cr, uid, wiz_proxy, context=None):
        ''' Update domain:
        '''
        product_pool = self.pool.get('product.product')

        domain = []
        # Supplier filter:
        if wiz_proxy.first_supplier_id:
            domain.append(
                ('first_supplier_id', '=', wiz_proxy.first_supplier_id.id))
                
        # Duty:
        if wiz_proxy.duty_id:
            domain.append(
                ('duty_id', '=', wiz_proxy.duty_id.id))

        # Status:
        if wiz_proxy.status:
            domain.append(
                ('status', '=', wiz_proxy.status))
        
        # Product code filter:
        if wiz_proxy.code_start:
            domain.append(('default_code', '=ilike', '%s%s' % (
                wiz_proxy.code_start, '%')))
        if wiz_proxy.code_partial:
            if wiz_proxy.code_from and wiz_proxy.code_from > 1:
                pattern = '_' * (wiz_proxy.code_from - 1)                
                domain.append(('default_code', '=ilike', '%s%s%s' % (
                    pattern,
                    wiz_proxy.code_partial,
                    '%',
                    )))
            else:
                domain.append(
                    ('default_code', 'ilike', wiz_proxy.code_partial))

        product_ids = product_pool.search(cr, uid, domain, context=context)
        return product_ids

    def return_view(self, cr, uid, ids, target='current', context=None):
        ''' Generate view for return product list result
        '''
        model_pool = self.pool.get('ir.model.data')
        tree_view_id = model_pool.get_object_reference(
            cr, uid, 'product_cost_rule', 'view_product_product_cost_tree')[1]
        form_view_id = model_pool.get_object_reference(
            cr, uid, 'product_cost_rule', 'view_product_product_cost_form')[1]
        search_view_id = model_pool.get_object_reference(
            cr, uid, 'product_cost_rule', 
            'view_product_product_cost_search')[1]
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Calc set product esit:'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'res_id': 1,
            'res_model': 'product.product',
            'view_id': tree_view_id,
            'search_view_id': search_view_id,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': [('id', 'in', ids)],
            'context': context,
            'target': target,
            'nodestroy': False,
            }
        
    # --------------------
    # Wizard button event:
    # --------------------
    def action_show_selection(self, cr, uid, ids, context=None):
        ''' Return record selected
        '''
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        product_ids = self.get_product_filter_selection(
            cr, uid, wiz_proxy, context=context)
        return self.return_view(cr, uid, product_ids, context=context)
            
    
    def action_execute(self, cr, uid, ids, context=None):
        ''' Event for button execute
        '''
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        product_pool = self.pool.get('product.product')
        transport_pool = self.pool.get('product.product.transport')
        
        # ---------------------------------------------------------------------
        # 1. generate filter and search product (common part)
        # ---------------------------------------------------------------------
        product_ids = self.get_product_filter_selection(cr, uid, wiz_proxy, 
            context=context)
        _logger.info('Found %s product for update!' % len(product_ids))    
        
        if wiz_proxy.mode == 'cost':
            # -----------------------------------------------------------------
            # 2. force calc method (depend on check button)
            # -----------------------------------------------------------------
            if wiz_proxy.company_set:
                product_pool.write(cr, uid, product_ids, {
                    'company_method_id': wiz_proxy.company_method_id.id,
                    }, context=context)
            if wiz_proxy.customer_set:
                product_pool.write(cr, uid, product_ids, {
                    'customer_method_id': wiz_proxy.customer_method_id.id,
                    }, context=context)
            if wiz_proxy.pricelist_set:
                product_pool.write(cr, uid, product_ids, {
                    'pricelist_method_id': wiz_proxy.pricelist_method_id.id,
                    }, context=context)
            
            # -----------------------------------------------------------------
            # 3. force calc operation
            # -----------------------------------------------------------------
            if wiz_proxy.company_calc:
                product_pool.get_product_cost_value(cr, uid, product_ids, 
                block='company', context=context)
            if wiz_proxy.customer_calc:
                product_pool.get_product_cost_value(cr, uid, product_ids, 
                    block='customer', context=context)
            if wiz_proxy.pricelist_calc:
                product_pool.get_product_cost_value(cr, uid, product_ids, 
                    block='pricelist', context=context)
        else: # 'transport'   
            update_transport_ids = [
                item.id for item in wiz_proxy.transport_ids]
            
            create_list = []
            for product in product_pool.browse(cr, uid, product_ids, 
                    context=context):
                current_ids = []    
                for item in product.transport_ids:
                    current_ids = [
                        item.transport_id.id for item in product.transport_ids]

                print current_ids, update_transport_ids                        

                volume = False
                for transport in wiz_proxy.transport_ids:
                    transport_id = transport.id
                    if transport_id not in current_ids:
                        if volume == False: # calculate only once                                                                
                            # get volume1
                            volume = product_pool.get_volume_single_product(
                                cr, uid, product, context=context)                        
                                    
                        if not volume:  
                            _logger.error(
                                'Product without volume: %s' % \
                                    product.default_code)                                            
                            break # no more transport for this product
                        quantity = int(transport.volume / volume)
                        create_list.append({
                            'transport_id': transport_id,
                            'product_id': product.id,
                            'quantity': quantity,
                            'calc_note': 'INT (%s / %s) = %s' % (
                                transport.volume, volume, quantity),
                            })

            for data in create_list:
                transport_pool.create(cr, uid, data, context=context)
        
        # Return touched product:        
        return self.return_view(cr, uid, product_ids, context=context)

    _columns = {
        # Filter field:
        'first_supplier_id': fields.many2one(
            'res.partner', 'First supplier'),
        'duty_id': fields.many2one(
            'product.custom.duty', 'Duty category'),
        'status': fields.selection([
            ('catalog', 'Catalog'),
            ('out', 'Out catalog'),
            ('stock', 'Stock'),
            ('obsolete', 'Obsolete'),
            ('sample', 'Sample'),
            ('todo', 'Todo'),
            ], 'Gamma'),
            
        # Code filter:
        'code_start': fields.char('Code start', size=25), 
        'code_partial': fields.char('Code partial', size=25), 
        'code_from': fields.integer('Code from char'),         
        #'family_id': fields.many2one('product.template', 'Family', 
        #    domain=[('is_family', '=', True)]),
        
        # Mode selection:
        'mode': fields.selection([
            ('transport', 'Product transport force'),
            ('cost', 'Set or calc product cost'),
            ], 'Wizard mode', required=True),
            
        # ---------------------------------------------------------------------
        # Transport management:
        # ---------------------------------------------------------------------
        'transport_ids': fields.many2many(
            'product.cost.transport', 'product_force_wizard_transport_rel', 
            'wizard_id', 'transport_id', 
            'Transport'),
    
        # ---------------------------------------------------------------------
        # Cost management:
        # ---------------------------------------------------------------------
        # Calculation field:
        'company_calc': fields.boolean('Company calc'),
        'customer_calc': fields.boolean('Customer calc'),
        'pricelist_calc': fields.boolean('Pricelist calc'),
        
        # Set field:
        'company_set': fields.boolean('Company set method'),
        'customer_set': fields.boolean('Customer set method'),
        'pricelist_set': fields.boolean('Pricelist set method'),
        
        'company_method_id': fields.many2one(
            'product.cost.method', 'Company Method'),
        'customer_method_id': fields.many2one(
            'product.cost.method', 'Customer Method'),
        'pricelist_method_id': fields.many2one(
            'product.cost.method', 'Pricelist Method'),        
        }
        
    _defaults = {        
        # Default value:
        'mode': lambda *x: 'cost',
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


