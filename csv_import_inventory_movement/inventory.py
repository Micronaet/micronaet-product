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
import xlrd
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

class StockMove(orm.Model):
    """ Model name: Quants updated from inventory
    """    
    _inherit = 'stock.move'

    _columns = {
        'inventory_quants_id': fields.many2one(
            'stock.quant', 'Inventory quant', ondelete='set null',
            help='Quants linked to this stock movement'),
        }

class ProductProductImportInventory(orm.Model):
    ''' Importation log element
    ''' 
    _name = 'product.product.import.inventory'
    _description = 'Inventory partial import'
    _rec_name = 'fullname'
    _order = 'date desc'
    
    filename = '/home/administrator/photo/xls/inventory' # TODO parametrize

    # -------------
    # Button event:
    # -------------
    def set_inventory_start(self, cr, uid, ids, context=None):
        ''' Set start inventory in product from XLS file 
        '''
        product_pool = self.pool.get('product.product')
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
         

        # ----------------
        # Read parameters:
        # ----------------
        # From import procedure:
        fullname = current_proxy.fullname
        max_line = current_proxy.max_line or 15000

        log_file = open(
            os.path.join(
                self.filename,
                'inventory_update_%s_%s.csv' % (
                    fullname,
                    datetime.now(),
                    ),
                ), 'w')

        try:
            filename = os.path.join(self.filename, fullname)
            wb = xlrd.open_workbook(filename)
            ws = wb.sheet_by_index(0)
        except:
            error = 'Error opening XLS file: %s' % (sys.exc_info(), )
            raise osv.except_osv(
                _('Open file error'), 
                _('Cannot found file: %s' % filename),
                )  

        if not fullname:
            raise osv.except_osv(
                _('Import error'), 
                _('Need a file name to import in path %s' % fullname),
                )
                
        _logger.info('Start import from path: %s' % self.filename)        
        for i in range(0, max_line):
            try:
                row = ws.row(i) # generate error at end
            except:
                log_file.write('%s | Row error|\n' % i)
                break
            # Loop on colums (trace)
            try:
                default_code = str(row[0].value).replace('.0', '')
            except:
                log_file.write('%s | Code error|%s\n' % (i, row))
                break
                
            # Search product with code:
            if not default_code:
                log_file.write('%s | No code|%s\n' % (i, row))
                continue # jump

            try:
                product_qty = float(row[1].value)
            except:
                log_file.write('%s | Qty error|%s\n' % (i, row))
                product_qty = 0

            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code)], context=context)
            
            if not product_ids:
                log_file.write('%s | Product not found|%s\n' % (i, row))
                continue # jump
            
            product_proxy = product_pool.browse(
                cr, uid, product_ids, context=context)[0]
             
            # Write log before:
            log_file.write('%s | %s | %s\n' % (
                default_code,
                #product_proxy.inventory_start,
                product_proxy.mx_start_qty,
                product_qty,
                ))

            product_pool.write(cr, uid, product_ids[0], {
                # XXX old procedure for update inventory data
                #'inventory_start': product_qty,
                #'inventory_delta': 0.0,# XXX reset delta adjust!!!
                
                # XXX now new inventory start 2017:
                'inventory_start': 0.0,
                'inventory_delta': 0.0,
                'mx_start_qty': product_qty,
                'mx_start_date': '2016-12-31 00:00:00', # TODO
                }, context=context)

            _logger.info('Update %s' % default_code)    
                
        log_file.close()        
        return True       

    def action_import_product_from_csv(self, cr, uid, ids, context=None):
        ''' Import detail button
        '''
        if context is None:
            context = {}
            
        # Pool used:
        picking_pool = self.pool.get('stock.picking')
        move_pool = self.pool.get('stock.move')
        product_pool = self.pool.get('product.product')
        seq_pool = self.pool.get('ir.sequence')
        quant_pool = self.pool.get('stock.quant')
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        user_pool = self.pool.get('res.users')
        
        # Browse obj:
        user_proxy = user_pool.browse(
            cr, uid, uid, context=context)

        # Set inventory ON
        user_pool.write(cr, uid, uid, {
            'no_inventory_status': False,
            }, context=context)

        # ----------------
        # Read parameters:
        # ----------------
        # From import procedure:
        fullname = current_proxy.fullname
        create_product = current_proxy.create_product
        partner_id = current_proxy.partner_id.id or user_proxy.partner_id.id
        uom_id = current_proxy.uom_id.id or False
        max_line = current_proxy.max_line or 15000
        type_cl = current_proxy.cl_picking_type_id
        type_sl = current_proxy.sl_picking_type_id
        seq_cl_id = current_proxy.cl_picking_type_id.sequence_id.id
        seq_sl_id = current_proxy.sl_picking_type_id.sequence_id.id

        # Calculated:
        date = current_proxy.date or datetime.now().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        context['limit_up_date'] = date # set up limit   

        # Log activity:
        if not fullname:
            raise osv.except_osv(
                _('Import error'), 
                _('Need a file name to import in path %s' % fullname),
                )
        _logger.info('Start import from path: %s' % self.filename)

        # ----------------
        # Header creation:        
        # ----------------
        header_data = {
            'name': seq_pool.get_id(cr, uid, seq_cl_id, 'id', context=context),
            'partner_id': partner_id,
            'picking_type_id': type_cl.id,            
            'date': date,
            'min_date': date,
            'date_done': date,
            'origin': _('CL from: %s') % fullname,
            'state': 'done', # forced
            }   
            
        # Create object:
        cl_proxy = picking_pool.create(cr, uid, header_data, context=context)
        
        # Update SL data:
        header_data.update({
            'picking_type_id': type_sl.id,
            'name': seq_pool.get_id(
                cr, uid, seq_sl_id, 'id', context=context),
            'origin': _('SL from: %s') % fullname,
            })
            
        sl_proxy = picking_pool.create(cr, uid, header_data, context=context)

        # ---------------------------------------------------------------------
        #                Open XLS document (first WS):
        # ---------------------------------------------------------------------
        error = note = ''

        # Read excel filename:
        try:
            filename = os.path.join(self.filename, fullname)
            wb = xlrd.open_workbook(filename)
            ws = wb.sheet_by_index(0)
        except:
            error = 'Error opening XLS file: %s' % (sys.exc_info(), )
            raise osv.except_osv(
                _('Open file error'), 
                _('Cannot found file: %s' % filename),
                )  

        # Loop on line:
        for i in range(0, max_line):
            try:
                row = ws.row(i) # generate error at end
            except:
                # Out of range error ends import:
                note += _('Import end at line: %s\n') % i
                break

            try:
                # Loop on colums (trace)
                try:
                    default_code = str(row[0].value).replace('.0', '')
                except:
                    default = ''
                    
                # Search product with code:
                if not default_code:
                    error += _('%s. No default code on file found\n') % i
                    continue # jump

                try:
                    product_qty = float(row[1].value)
                except:
                    product_qty = 0

                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                
                created = False
                if not product_ids:
                    if create_product:
                        created = True
                        product_id = product_pool.create(cr, uid, {
                            'default_code': default_code,
                            'name': 'Product %s' % default_code,
                            'uom_id': uom_id,
                            'uos_id': uom_id,
                            'uom_po_id': uom_id,
                            }, context=context)
                        product_ids = [product_id]    
                    else:
                        error += _(
                            '%s. Error code not found, code: %s\n') % (
                                i, default_code)
                        continue # jump                
                elif len(product_ids) > 1:
                    error += _(
                        '%s. Warning more code (take first), code: %s\n') % (
                                i, default_code)
                                              
                product_proxy = product_pool.browse(
                    cr, uid, product_ids, context=context)[0]
                    
                # Update with stock:
                mx_net_qty = product_proxy.mx_net_qty # for speed
                gap_qty = mx_net_qty - product_qty
                
                if gap_qty > 0:
                    document = 'SL'
                    picking_id = sl_proxy
                    type_picking = type_sl
                    # quant:
                    sign = -1 # negative quant
                    quant_location_id = type_picking.default_location_src_id.id
                elif gap_qty < 0:
                    document = 'CL'
                    picking_id = cl_proxy
                    type_picking = type_cl
                    gap_qty = -gap_qty # positive quantity        
                    # quant:
                    sign = +1 # positive quant
                    quant_location_id = \
                        type_picking.default_location_dest_id.id
                else:
                    document = 'NO DOC'

                if gap_qty:
                    # Create quant:
                    quant_id = quant_pool.create(cr, uid, {
                        'in_date': date,
                        'cost': 0.0, # TODO
                        'location_id': quant_location_id,
                        'product_id': product_ids[0],
                        'qty': gap_qty * sign, 
                        #'product_uom': bom.product_id.uom_id.id,
                        }, context=context)   

                    move_pool.create(cr, uid, {
                        'name': default_code,
                        'product_id': product_ids[0],
                        'picking_id': picking_id,
                        'product_uom_qty': gap_qty,
                        'date': date,
                        'date_expected': date,
                        #'date_planned': date,
                        'inventory_quants_id': quant_id,
                        'location_id': 
                            type_picking.default_location_src_id.id,
                        'location_dest_id': 
                            type_picking.default_location_dest_id.id,
                            
                        'price_unit': 1.0, # TODO for stock evaluation
                        'product_uom': product_proxy.uom_id.id,
                        'state': 'done',
                        }, context=context)

                note += '%s|. |\'%s| from |\'%s| to |\'%s| [|%s|%s|%s]\n' % (
                    i, 
                    default_code, 
                    mx_net_qty,
                    product_qty,
                    document,
                    gap_qty if gap_qty else 'No move!!',
                    'product creation!' if created else '',
                    )
            except:
                error += _('%s. Import error code: %s [%s]\n') % (
                    i, default_code, sys.exc_info())
                    
        self.write(cr, uid, ids, {
            'error': error,
            'note': 'File: %s\n%s' % (
                filename, note),
            'inventory_cl_id': cl_proxy,
            'inventory_sl_id': sl_proxy,    
            }, context=context)

        # Set inventory OFF
        user_pool.write(cr, uid, uid, {
            'no_inventory_status': True,
            }, context=context)
        
        context['limit_up_date'] # reset context limit
        _logger.info('End import XLS purchase file: %s' % fullname)
        
        return True

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'date': fields.datetime('Date'),
        'fullname': fields.char(
            'File name', size=80, required=True), 
        'max_line': fields.integer('Max line'),
        'create_product': fields.boolean('Create product'),
        'uom_id': fields.many2one(
            'product.uom', 'UOM', help='For new product'), 
        'cl_picking_type_id': fields.many2one(
            'stock.picking.type', 'Type CL', required=True),
        'sl_picking_type_id': fields.many2one(
            'stock.picking.type', 'Type SL', required=True),
        'inventory_cl_id': fields.many2one(
            'stock.picking', 'Inventory CL', ondelete='set null'),
        'inventory_sl_id': fields.many2one(
            'stock.picking', 'Inventory SL', ondelete='set null'),
        'error': fields.text('Error'),
        'note': fields.text('Note'),
        }
        
    _defaults = {
        'date': lambda *x: datetime.now().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT),
        'max_line': lambda *x: 15000,
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
