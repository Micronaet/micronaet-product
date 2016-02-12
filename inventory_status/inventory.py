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
from openerp import SUPERUSER_ID #, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class ProductProduct(orm.Model):
    ''' Model name: ProductProduct
    '''   
    _inherit = 'product.product'
    
    # --------
    # Utility:
    # --------
    def get_stock_movement_from_in_to_out(self, cr, uid, product_id, loc_in, 
            loc_out, context=None):
        ''' Return movement for product and move type passed
        '''
        # TODO
        #move_pool = self.pool.get('stock.move')
        #move_ids = move_pool.search(cr, uid, [
        #    ('location_id', '=', loc_in),
        #    ('location_desc_id', '=', loc_out),
        #    ('product_id', '=', product_id),
        #    ], context=context)
        return []#move_ids
        
    def get_stock_movement_from_type(self, cr, uid, product_id, type_id, 
            context=None):
        ''' Return movement for product and move type passed
        '''
        type_pool = self.pool.get('stock.picking.type')
        type_proxy = type_pool.browse(cr, uid, type_id, context=context)
        
        return [] # TODO
        #return self.get_stock_movement_from_in_to_out(
        #    cr, uid, product_id,
        #    type_proxy.default_location_src_id.id, 
        #    type_proxy.default_location_dest_id.id, 
        #    context=context)
        
    def get_movements_type(self, cr, uid, ids, move, context=None):
        ''' Open movements with type passed as:
            context field: 'type_of_movement':  
                'in', 'out', 'of', 'oc',
        '''  
        context = context or {}
        
        # Get parameter from company:
        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(cr, uid, company_ids, 
            context=context)[0]
            
        if move == 'in':
            # TODO loop
            item_ids = set()
            for element in company_proxy.stock_report_load_ids:
                item_ids.update(set(
                    self.get_stock_movement_from_type(
                        cr, uid, ids[0], element, 
                        context=context)))
            item_ids = list(item_ids)     
            return {
            'type': 'ir.actions.act_window',
            'name': 'Order line status',
            'res_model': 'stock.move',
            #'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'view_id': view_id,
            #'target': 'new',
            #'nodestroy': True,
            'domain': [('id', 'in', item_ids)],
            }   
                   
        elif move == 'out':
            pass
        elif move == 'of':
            pass       
        elif move == 'oc':
            sol_pool = self.pool.get('sale.order.line')
            # TODO filter for open order
            sol_ids = sol_pool.search(cr, uid, [
                ('product_id', '=', ids[0])], context=context)
            item_ids = []
            import pdb; pdb.set_trace()
            for sol in sol_pool.browse(cr, uid, sol_ids, context=context):
                if sol.product_uom_qty - sol.delivered_qty > 0.0:
                    import pdb; pdb.set_trace()
                    item_ids.append(sol.id)
            
            return {
            'type': 'ir.actions.act_window',
            'name': 'Order line status',
            'res_model': 'sale.order.line',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', item_ids)],
            }   
                   
        
        if not item_ids:
            return True

    def get_movements_oc(self, cr, uid, ids, context=None):
        self.get_movements_type(cr, uid, ids, 'oc', context=context)
    def get_movements_of(self, cr, uid, ids, context=None):
        self.get_movements_type(cr, uid, ids, 'of', context=context)
    def get_movements_in(self, cr, uid, ids, context=None):
        self.get_movements_type(cr, uid, ids, 'in', context=context)
    def get_movements_out(self, cr, uid, ids, context=None):
        self.get_movements_type(cr, uid, ids, 'out', context=context)
        
        
    def dummy_temp(self, cr, uid, ids, context=None):
        ''' Temp button for associate event till no correct association
        '''
        return True
        
    def button_export_inventory(self, cr, uid, ids, context=None):
        ''' Export on file:
        '''
        def clean_ascii(value):
            res = ''
            for c in value:
                if ord(c) < 127:
                    res += c
                else:
                    res += '#'    
            return res    
            
        filename = '/home/administrator/photo/xls/esistenze.csv'
        f_out = open(filename, 'w')
        
        _logger.info('Start export inventory: %s' % filename)
        product_ids = self.search(cr, uid, [
            ('web_published', '=', True)], context=context)
        for product in self.browse(cr, uid, product_ids, context=context):
            value = clean_ascii('%s|%s|%s|%s|%s|%s|%s|%s|%s\n' % ( #|%s
                product.default_code,
                #product.statistic_category, # TODO remove
                product.name,
                product.mx_net_qty,
                product.mx_oc_out,
                product.mx_of_in,
                product.mx_lord_qty,
                0,
                '/',
                'GPB',
                ))
            f_out.write(value)
        f_out.close()    
        _logger.info('End export inventory')
        return
    
    # -------------
    # Button event:
    # -------------
    def get_sale_order_line_status(self, cr, uid, ids, context=None):
        ''' Open sol list
        '''        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order line status',
            'res_model': 'sale.order.line',
            #'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'view_id': view_id,
            #'target': 'new',
            #'nodestroy': True,
            'domain': [('product_id', 'in', ids)],
            }
    
    def _get_status_ordered(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        sol_pool = self.pool.get('sale.order.line')
        sol_ids = sol_pool.search(cr, uid, [
            ('product_id', 'in', ids)], context=context)
        
        res = {}.fromkeys(ids, 0.0)
        for line in sol_pool.browse(cr, uid, sol_ids, context=context):
            item_id = line.product_id.id # product_id
            remain = line.product_uom_qty - line.delivered_qty            
            if line.order_id.state in ('draft', 'sent', 'cancel'):
                continue            
            res[item_id] -= remain
        return res
        
    # ----------------
    # Fields function:    
    # ----------------
    def _get_inventory_values(self, cr, uid, product_ids, fields, args, context=None):
        ''' Get information
        '''
        res = {}

        # pool used:
        product_pool = self.pool.get('product.product')
        pick_pool = self.pool.get('stock.picking')
        sale_pool = self.pool.get('sale.order') # XXX maybe not used 
        sol_pool = self.pool.get('sale.order.line') # XXX maybe not used 
        move_pool = self.pool.get('stock.move')

        # ---------------------------------------------------------------------
        # Parameter for filters:
        # ---------------------------------------------------------------------
        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Exclude partner list:
        exclude_partner_ids = [] # Used?
        for item in company_proxy.stock_explude_partner_ids:
            exclude_partner_ids.append(item.id)            
        # Append also this company partner (for inventory)    
        exclude_partner_ids.append(company_proxy.partner_id.id)
        stock_location_id = company_proxy.stock_location_id.id
        
        # Year filter:
        from_date = datetime.now().strftime('%Y-01-01 00:00:00')    
        to_date = datetime.now().strftime('%Y-12-31 23:59:59')    

        # ------------------
        # Create empty dict:
        # ------------------
        for item_id in product_ids:
            res[item_id] = {
                'mx_inv_qty': 0.0,
                'mx_mm_qty': 0.0,
                'mx_of_in': 0.0,
                'mx_oc_out': 0.0,
                'mx_bf_in': 0.0,
                'mx_bc_out': 0.0,
                'mx_net_qty': 0.0,
                'mx_lord_qty': 0.0,
                }

        # ---------------------------------------------------------------------
        # Inventory adjustement
        # ---------------------------------------------------------------------
        if stock_location_id:
            line_ids = move_pool.search(cr, uid, [
                ('inventory_id', '!=', False),
                ('date', '>=', from_date), 
                ('date', '<=', to_date), 
                ])
            
            for line in move_pool.browse(cr, uid, line_ids, context=context):
                if line.location_id.id == stock_location_id:
                    res[line.product_id.id][
                        'mx_inv_qty'] -= line.product_uom_qty
                elif line.location_dest_id.id == stock_location_id:                        
                    res[line.product_id.id][
                        'mx_inv_qty'] += line.product_uom_qty
        else:    
            _logger.error('No stock location set up in Company!!!')

        # ---------------------------------------------------------------------
        # BC. Get unload picking
        # ---------------------------------------------------------------------
        out_picking_type_ids = []
        
        # Delivery out:
        for item in company_proxy.stock_report_unload_ids:
            out_picking_type_ids.append(item.id)
            
        # MRP out
        for item in company_proxy.stock_report_mrp_out_ids:
            if item.id not in out_picking_type_ids:
                out_picking_type_ids.append(item.id)

        pick_ids = pick_pool.search(cr, uid, [
            # type pick filter   
            ('picking_type_id', 'in', out_picking_type_ids),
            # Partner exclusion
            #('partner_id', 'not in', exclude_partner_ids), 
            # TODO check data date
            # TODO date_done, min_date, date
            ('date', '>=', from_date), 
            ('date', '<=', to_date), 
            # TODO state filter
            ])

        line_ids = move_pool.search(cr, uid, [
            ('product_id', 'in', product_ids),
            ('picking_id', 'in', pick_ids),
            ], context=context)
        
        for line in move_pool.browse(cr, uid, line_ids, context=context):
            res[line.product_id.id][
                'mx_bc_out'] += line.product_uom_qty

        # ---------------------------------------------------------------------
        # OF. Get load picking
        # ---------------------------------------------------------------------
        in_picking_type_ids = []
        
        # Purchase delivery in:
        for item in company_proxy.stock_report_load_ids:
            in_picking_type_ids.append(item.id)

        # MRP delivery in:
        for item in company_proxy.stock_report_mrp_in_ids:
            if item.id not in in_picking_type_ids:
                in_picking_type_ids.append(item.id)
            
        pick_ids = pick_pool.search(cr, uid, [     
            # type pick filter   
            ('picking_type_id', 'in', in_picking_type_ids),            
            # Partner exclusion
            # TODO ('partner_id', 'not in', exclude_partner_ids),            
            # check data date
            # TODO Restore date (for start up period not)
            #('date', '>=', from_date), # XXX correct for virtual?
            #('date', '<=', to_date),            
            # TODO state filter
            ])

        line_ids = move_pool.search(cr, uid, [
            ('product_id', 'in', product_ids),
            ('picking_id', 'in', pick_ids),
            ], context=context)

        for line in move_pool.browse(cr, uid, line_ids, context=context):
            if line.state == 'assigned': # OF
                res[line.product_id.id][
                    'mx_of_in'] += line.product_uom_qty
            else: #done
                res[line.product_id.id][
                    'mx_bf_in'] += line.product_uom_qty
        
        # ---------------------------------------------------------------------
        # Get order to delivery
        # ---------------------------------------------------------------------
        sol_ids = sol_pool.search(cr, uid, [
            ('product_id', 'in', product_ids)])
            
        for line in sol_pool.browse(cr, uid, sol_ids):
            # Header state
            if line.order_id.state in ('cancel', 'draft', 'sent'): #done?
                continue # TODO better!!            
            # Check delivered:
            remain = line.product_uom_qty - line.delivered_qty
            if remain <= 0.0:
                continue
            
            res[line.product_id.id][
                'mx_oc_out'] += remain
        
        # Update with calculated fields        
        for key in res:
            res[key]['mx_net_qty'] = \
                res[key]['mx_bf_in'] - res[key]['mx_bc_out'] + \
                res[key]['mx_inv_qty'] 
            res[key]['mx_lord_qty'] = \
                res[key]['mx_net_qty'] - res[key]['mx_oc_out'] + \
                res[key]['mx_of_in']                    
        return res

    _columns = {
        #'status_ordered': fields.function(
        #     _get_status_ordered, method=True, type='float', string='Ordered', 
        #     store=False),
        'web_published': fields.boolean('Web published'),
        
        'mx_inv_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Inventory', 
            store=False, multi=True),
        'mx_mm_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Movement', 
            store=False, multi=True),

        'mx_bf_in': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='BF in (MRP in)', 
            store=False, multi=True),
        'mx_bc_out': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='BC out (MRP out)', 
            store=False, multi=True),    

        'mx_of_in': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='OF in', 
            store=False, multi=True),
        'mx_oc_out': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='OC out', 
            store=False, multi=True),
        
        'mx_net_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Total Net', 
            store=False, multi=True),
        'mx_lord_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Total Lord', 
            store=False, multi=True),        
        }
        
    _defaults = {
        'web_published': lambda *x: True,
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
