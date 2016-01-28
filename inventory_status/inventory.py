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
    
    # button event:
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
        
    def get_inventory_values(self, cr, uid, product_ids, context=None):
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
        
        # Year filter:
        from_date = datetime.now().strftime('%Y-01-01 00:00:00')    
        to_date = datetime.now().strftime('%Y-12-31 23:59:59')    

        # ------------------
        # Create empty dict:
        # ------------------
        for item_id in product_ids:
            res[item_id] = {
                'status_inventory': 0.0,
                'status_movement': 0.0,
                'status_order_in': 0.0,
                'status_order_out': 0.0,
                'status_load_in': 0.0,
                'status_load_out': 0.0,
                }

        # ---------------------------------------------------------------------
        # BC. Get unload picking
        # ---------------------------------------------------------------------
        out_picking_type_ids = []
        for item in company_proxy.stock_report_unload_ids:
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
                'status_order_out'] += line.product_uom_qty

        # ---------------------------------------------------------------------
        # OF. Get load picking
        # ---------------------------------------------------------------------
        in_picking_type_ids = []
        for item in company_proxy.stock_report_load_ids:
            in_picking_type_ids.append(item.id)
            
        pick_ids = pick_pool.search(cr, uid, [     
            # type pick filter   
            ('picking_type_id', 'in', in_picking_type_ids),            
            # Partner exclusion
            # TODO ('partner_id', 'not in', exclude_partner_ids),            
            # check data date
            ('date', '>=', from_date), # XXX correct for virtual?
            ('date', '<=', to_date),            
            # TODO state filter
            ])

        line_ids = move_pool.search(cr, uid, [
            ('product_id', 'in', product_ids),
            ('picking_id', 'in', pick_ids),
            ], context=context)

        for line in move_pool.browse(cr, uid, line_ids, context=context):
            if line.state == 'assigned': # OF
                res[line.product_id.id][
                    'status_order_in'] += line.product_uom_qty
            else: #done
                res[line.product_id.id][
                    'status_load_in'] += line.product_uom_qty
        
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
                'status_order_out'] += line.product_uom_qty
        return res        

    _columns = {
        'status_ordered': fields.function(
             _get_status_ordered, method=True, type='float', string='Ordered', 
             store=False),
        #'status_virtual': fields.function(
        #     _get_status_ordered, method=True, type='float', 
        #     string='Virtual available', store=False, multi=True),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
