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

class StockMove(orm.Model):
    ''' Model name: Stock move ref.
    '''   
    _inherit = 'stock.move'
    
    def open_picking_from_stock_move(self, cr, uid, ids, context=None):
        ''' Open button
        '''
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        return {
            'type': 'ir.actions.act_window',
            'name': _('Picking'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_id': current_proxy.picking_id.id,
            'res_model': 'stock.picking',
            'views': [(False, 'form')],
            'context': context,
            'target': 'new', 
            }
        
    _columns = {
        'ddt_id': fields.related(
            'picking_id', 'ddt_id', 
            type='many2one', relation='stock.ddt', 
            string='DDT', store=False), 
        'partner_id': fields.related(
            'picking_id', 'partner_id', 
            type='many2one', relation='res.partner', 
            string='Partner', store=False), 
        }
    
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
        model_pool = self.pool.get('ir.model.data')
        
        if move == 'in': # BF
            product_proxy = self.browse(cr, uid, ids, context=context)[0]
            item_ids = [item.id for item in product_proxy.mx_bf_ids]
            
            try:
                tree_view = model_pool.get_object_reference(
                    cr, uid, 'inventory_status', 
                    'view_stock_move_ref_form')[1]
            except:
                tree_view = False        
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Stock move status',
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [
                    (tree_view or False, 'tree'), 
                    ],
                'domain': [('id', 'in', item_ids)],
                }   

        elif move == 'inv': # INV
            product_proxy = self.browse(cr, uid, ids, context=context)[0]
            item_ids = [item.id for item in product_proxy.mx_inv_ids]
            
            try:
                tree_view = model_pool.get_object_reference(
                    cr, uid, 'inventory_status', 
                    'view_stock_move_ref_form')[1]
            except:
                tree_view = False        
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Stock move status',
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [
                    (tree_view or False, 'tree'), 
                    ],
                'domain': [('id', 'in', item_ids)],
                }   
                   
        elif move == 'out': # BC
            product_proxy = self.browse(cr, uid, ids, context=context)[0]
            item_ids = [item.id for item in product_proxy.mx_bc_ids]
            
            try:
                tree_view = model_pool.get_object_reference(
                    cr, uid, 'inventory_status', 
                    'view_stock_move_ref_form')[1]
            except:
                tree_view = False        
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Stock move status',
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [
                    (tree_view or False, 'tree'), 
                    ],
                'domain': [('id', 'in', item_ids)],
                }   
        elif move == 'of':
            product_proxy = self.browse(cr, uid, ids, context=context)[0]
            item_ids = [item.id for item in product_proxy.mx_of_ids]
            
            try:
                tree_view = model_pool.get_object_reference(
                    cr, uid, 'inventory_status', 
                    'view_stock_move_ref_form')[1]
            except:
                tree_view = False        
            
            return {
                'type': 'ir.actions.act_window',
                'name': 'Stock move status',
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [
                    (tree_view or False, 'tree'), 
                    ],
                'domain': [('id', 'in', item_ids)],
                }   
            
        elif move == 'oc':
            product_proxy = self.browse(cr, uid, ids, context=context)[0]
            item_ids = [item.id for item in product_proxy.mx_oc_ids]

            try:        
                tree_view = model_pool.get_object_reference(
                    cr, uid, 'inventory_status', 
                    'view_sale_order_line_tree')[1]
            except:
                tree_view = False        
                
            return {
                'type': 'ir.actions.act_window',
                'name': 'Order line status',
                'res_model': 'sale.order.line',
                'view_type': 'form',
                'views': [
                    #(form_view or False, 'form'),
                    (tree_view or False, 'tree'), 
                    #(False, 'kanban'),
                    #(False, 'calendar'), 
                    #(False, 'graph'),
                    ],
                'view_mode': 'tree,form',
                'domain': [('id', 'in', item_ids)],
                }
        return True # XXX do nothing (error)

    def get_movements_oc(self, cr, uid, ids, context=None):
        return self.get_movements_type(cr, uid, ids, 'oc', context=context)
        
    def get_movements_of(self, cr, uid, ids, context=None):
        return self.get_movements_type(cr, uid, ids, 'of', context=context)
        
    def get_movements_in(self, cr, uid, ids, context=None):
        return self.get_movements_type(cr, uid, ids, 'in', context=context)
        
    def get_movements_out(self, cr, uid, ids, context=None):
        return self.get_movements_type(cr, uid, ids, 'out', context=context)

    def get_movements_inv(self, cr, uid, ids, context=None):
        return self.get_movements_type(cr, uid, ids, 'inv', context=context)
        
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
        publish = '/home/administrator/ftp_pm.sh' 
        f_out = open(filename, 'w')
        
        _logger.info('Start export inventory: %s' % filename)
        product_ids = self.search(cr, uid, [
            ('web_published', '=', True)], context=context)
        for product in self.browse(cr, uid, product_ids, context=context):
            of_status = '/' # TODO check date and publish
            #for of in product.mx_of_ids:
            #    of_status += '%s %s\n' % (
            #        int(of.product_uom_qty),
            #        (of.picking_id.min_date or '?')[:10],
            #        )
            value = clean_ascii('%s|%s|%s|%s|%s|%s|%s|%s|%s\n' % ( #|%s
                product.default_code,
                #product.statistic_category, # TODO remove
                product.name,
                product.mx_net_qty,
                product.mx_oc_out,
                product.mx_of_in,
                product.mx_lord_qty,
                0,
                of_status,
                'GPB',
                ))
            f_out.write(value)
        f_out.close()    
        _logger.info('Publish inventory')
        try:
            os.system(publish)  
        except:
            _logger.error('Error publishing...')
            return False
                
        _logger.info('End export inventory')
        return True
    
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
            'view_type': 'form',
            'view_mode': 'tree,form',
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
    def _get_inventory_values(self, cr, uid, product_ids, fields, args, 
            context=None):
        ''' Get information
        '''
        _logger.warning('>>> START INVENTORY <<<')
        res = {}
        res_extra = {}
        
        if context is None:
            context = {}

        # ---------------------------------------------------------------------
        # Parameter for evaluation:
        # ---------------------------------------------------------------------                
        limit_up_date = context.get('limit_up_date', False) # limit for invent.

        # Year filter:
        from_date = datetime.now().strftime('%Y-01-01 00:00:00') # XXX ex 2016
        if limit_up_date:
            to_date = limit_up_date
            _logger.warning('Limite date: %s' % limit_up_date)
        else:    
            to_date = datetime.now().strftime('%Y-12-31 23:59:59')# XXX ex 2017

        # ---------------------------------------------------------------------
        # Read parameter for inventory:
        # ---------------------------------------------------------------------
        user_id = context.get('uid', uid)
        user = self.pool.get('res.users').browse(
            cr, uid, user_id, context=context)
        no_inventory_status = user.no_inventory_status
        _logger.warning('USER: %s' % user_id)

        # pool used:
        product_pool = self.pool.get('product.product')
        pick_pool = self.pool.get('stock.picking')
        sale_pool = self.pool.get('sale.order') # XXX maybe not used 
        sol_pool = self.pool.get('sale.order.line') # XXX maybe not used 
        move_pool = self.pool.get('stock.move')
        company_pool = self.pool.get('res.company')

        # ---------------------------------------------------------------------
        # Parameter for filters:
        # ---------------------------------------------------------------------
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        
        # Exclude partner list:
        exclude_partner_ids = [] # NOT USED TO REMOVE!!!!!!
        for item in company_proxy.stock_explude_partner_ids:
            exclude_partner_ids.append(item.id)            
        # Append also this company partner (for inventory)    
        exclude_partner_ids.append(company_proxy.partner_id.id)
        stock_location_id = company_proxy.stock_location_id.id
        
        # ------------------
        # Create empty dict:
        # ------------------
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
           # Extra data used     
            res_extra[product.id] = {
                'mx_mrp_out': product.mx_mrp_out, # TODO remove when stock move
                'mx_start_qty': product.mx_start_qty,
                #'mx_start_date': product.mx_start_date,
                }
                
            # Field data:    
            res[product.id] = {
                # Qty:
                'mx_inv_qty': 0.0,
                'mx_mm_qty': 0.0,
                'mx_of_in': 0.0,
                'mx_oc_out': 0.0,
                'mx_bf_in': 0.0,
                'mx_bc_out': 0.0,
                # Total:
                'mx_net_qty': 0.0,
                'mx_lord_qty': 0.0,
                'mx_net_mrp_qty': 0.0,
                'mx_lord_mrp_qty': 0.0,
                
                # one2many fields: 
                'mx_bc_ids': [],
                'mx_oc_ids': [],
                'mx_of_ids': [],
                'mx_bf_ids': [],
                'mx_inv_ids': [],
                
                # text info:
                'mx_of_date': '',           
                }
                
        if no_inventory_status:
            _logger.warning('>>> STOP NO INVENTORY <<<')
            return res
            
        # ---------------------------------------------------------------------
        # Inventory adjustement
        # ---------------------------------------------------------------------
        if stock_location_id:
            line_ids = move_pool.search(cr, uid, [
                ('inventory_id', '!=', False),
                ('product_id', 'in', product_ids),
                ('date', '>=', from_date), 
                ('date', '<=', to_date), 
                ])
            for line in move_pool.browse(cr, uid, line_ids, context=context):
                if 'mx_inv_ids' not in res[line.product_id.id]:
                    res[line.product_id.id]['mx_inv_ids'] = []
                res[line.product_id.id]['mx_inv_ids'].append(line.id)
                
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

        line_ids = move_pool.search(cr, uid, [
            # Line:
            ('product_id', 'in', product_ids),
            #('state', '!=', 'cancel'), # TODO active?

            # Header:
            # XXX date_done, min_date, date?
            ('picking_id.date', '>=', from_date), 
            ('picking_id.date', '<=', to_date),
            ('picking_id.picking_type_id', 'in', out_picking_type_ids),
            # ('partner_id', 'not in', exclude_partner_ids), 
            # TODO add state filter?
            ], context=context)
        
        for line in move_pool.browse(cr, uid, line_ids, context=context):
            res[line.product_id.id]['mx_bc_out'] += line.product_uom_qty            
            res[line.product_id.id]['mx_bc_ids'].append(line.id) # one2many:  

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
            
        line_ids = move_pool.search(cr, uid, [
            # Line:
            ('product_id', 'in', product_ids),
            
            # Header:
            # TODO ('partner_id', 'not in', exclude_partner_ids),            
            ('picking_id.picking_type_id', 'in', in_picking_type_ids),            
            # XXX Note: Only up period filter:
            #('picking_id.date', '>=', from_date), 
            ('picking_id.date', '<=', to_date),
            ], context=context)

        for line in move_pool.browse(cr, uid, line_ids, context=context):
            if line.state == 'assigned': # OF (still open, so keep also prev.)
                res[line.product_id.id][
                    'mx_of_in'] += line.product_uom_qty
                res[line.product_id.id]['mx_of_ids'].append(line.id)
                res[line.product_id.id]['mx_of_date'] += '%s ' % ((
                    line.date_expected or '')[:10])    
                                    
            # XXX Note: Added 02/01/2017 elif clause instead of else
            elif line.picking_id.date >= from_date: # done BF
                res[line.product_id.id]['mx_bf_in'] += line.product_uom_qty
                res[line.product_id.id]['mx_bf_ids'].append(line.id) # one2many
        
        # ---------------------------------------------------------------------
        # Get order to delivery
        # ---------------------------------------------------------------------
        sol_ids = sol_pool.search(cr, uid, [
            ('product_id', 'in', product_ids),
            ('mx_closed', '=', False), # Forced as closed
            ('order_id.state', 'not in', ('cancel', 'draft', 'sent')),
            # XXX Note: no date filter
            ])
            
        for line in sol_pool.browse(cr, uid, sol_ids): # Check delivered:
            remain = line.product_uom_qty - line.delivered_qty
            if remain <= 0.0:
                continue
            
            res[line.product_id.id]['mx_oc_out'] += remain
            res[line.product_id.id]['mx_oc_ids'].append(line.id) # one2many
        
        # Update with calculated fields        
        for key in res:
            # Without MRP:
            res[key]['mx_net_qty'] = \
                res_extra[key]['mx_start_qty'] + \
                res[key]['mx_inv_qty'] + \
                res[key]['mx_bf_in'] - \
                res[key]['mx_bc_out']
            res[key]['mx_lord_qty'] = \
                res[key]['mx_net_qty'] - \
                res[key]['mx_oc_out'] + \
                res[key]['mx_of_in']
            # TODO - campaign
                
            # WIth MRP (unload MP):
            res[key]['mx_net_mrp_qty'] = res[key]['mx_net_qty'] - \
                res_extra[key]['mx_mrp_out']
            res[key]['mx_lord_mrp_qty'] = res[key]['mx_lord_qty'] - \
                res_extra[key]['mx_mrp_out']
                
        _logger.warning('>>> STOP INVENTORY <<<')
        return res

    _columns = {
        #'status_ordered': fields.function(
        #     _get_status_ordered, method=True, type='float', string='Ordered', 
        #     store=False),
        'web_published': fields.boolean('Web published'),
                
        # Quantity
        'mx_start_date': fields.date('Start date'),
        'mx_start_qty': fields.float('Inventory start qty', 
            digits=(16, 2), # TODO parametrize
            help='Inventory at 1/1 for current year'),
        #'mx_delta_qty': fields.float('Inventory start qty', 
        #    digits=(16, 3), # TODO parametrize
        #    help='Inventory at 1/1 for current year'),

        'mx_inv_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Inventory adjust', store=False, multi=True),
        'mx_mm_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Movement', store=False, multi=True),

        'mx_bf_in': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='BF in (MRP in)', store=False, multi=True),
        'mx_bc_out': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='BC out (MRP out)', store=False, multi=True),    

        'mx_of_in': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='OF in', store=False, multi=True),
        'mx_oc_out': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='OC out', store=False, multi=True),
        
        'mx_net_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Total Net', store=False, multi=True),
        'mx_lord_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Total Lord', store=False, multi=True),     
        'mx_net_mrp_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Total Net with MRP', store=False, multi=True),
        'mx_lord_mrp_qty': fields.function(
            _get_inventory_values, method=True, type='float', 
            string='Total Lord with MRP', store=False, multi=True),     
        
        # TODO temporary field for unload in production this season.
        'mx_mrp_out': fields.float('(MRP out)', digits=(16, 2),
            help='Not included in net or lord qty, just a data placeholder'),       
        
        # Many2one
        'mx_bc_ids': fields.function(
            _get_inventory_values, method=True, type='one2many', 
            string='BC movement', relation='stock.move',
            store=False, multi=True),

        'mx_oc_ids': fields.function(
            _get_inventory_values, method=True, type='one2many', 
            string='OC movement', relation='sale.order.line',
            store=False, multi=True),

        'mx_of_ids': fields.function(
            _get_inventory_values, method=True, type='one2many', 
            string='OF movement', relation='stock.move',
            store=False, multi=True),

        'mx_bf_ids': fields.function(
            _get_inventory_values, method=True, type='one2many', 
            string='BF movement', relation='stock.move',
            store=False, multi=True),

        'mx_inv_ids': fields.function(
            _get_inventory_values, method=True, type='one2many', 
            string='Inv. movement', relation='stock.move',
            store=False, multi=True),
        
        # Text information:
        'mx_of_date': fields.function(
            _get_inventory_values, method=True, type='char', size=100, 
            string='OF date', store=False, multi=True),
        
        # History information:
        #'mx_net_qty_h': fields.float('Net (h)', digits=(16, 2)),
        #'mx_lord_qty_h': fields.float('Lord (h)', digits=(16, 2)),            
        }
        
    _defaults = {
        'web_published': lambda *x: True,
        }    

class ResUsers(orm.Model):
    """ Model name: SaleOrder
    """    
    _inherit = 'res.users'
   
    def set_no_inventory_status(self, cr, uid, value=False, context=None):
        ''' Set inventory status uid
            return previous value
            default is True
        '''
        user_proxy = self.browse(cr, uid, uid, context=context)
        
        previous = user_proxy.no_inventory_status
        self.write(cr, uid, uid, {
            'no_inventory_status': value
            }, context=context)
        _logger.warning('>>> Set user [%s] No inventory status: %s > %s' % (
            user_proxy.login, previous, value))
        return previous
            
    _columns = {
        'no_inventory_status': fields.boolean('No inventory status'),
        }

# TODO move away:
class SaleOrder(orm.Model):
    """ Model name: SaleOrder
    """    
    _inherit = 'sale.order'
   
    def set_context_no_inventory(self, cr, uid, ids, context=None):
        ''' Set no inventory in res.users parameter
        '''
        _logger.info('Stop inventory for user: %s' % uid)
        self.pool.get('res.users').write(cr, uid, [uid], {
            'no_inventory_status': True,
            }, context=context)
        return     

    def set_context_yes_inventory(self, cr, uid, ids, context=None):
        ''' Set no inventory in res.users parameter
        '''    
        _logger.info('Start inventory for user: %s' % uid)
        self.pool.get('res.users').write(cr, uid, [uid], {
            'no_inventory_status': False,
            }, context=context)
        return     
       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
