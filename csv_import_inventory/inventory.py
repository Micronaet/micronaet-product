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

class ProductProduct(orm.Model):
    ''' Link product to inventory purchase order
    '''
    _inherit = 'product.product'
    
    _columns = {
        'purchase_id': fields.many2one(
            'purchase.order', 'Purchase inventory'),
            
        # TODO remove (moved in inventory_field module    
        'inventory_start': fields.float(
            'Inventory start', digits=(16, 3)),
        'inventory_delta': fields.float(
            'Inventory delta', digits=(16, 3), 
            help='Delta inventory for post correction retroactive'),
        'inventory_date': fields.date('Inventory date'),    
        # TODO remove (moved in inventory_field module            
        }

class PurchaseOrder(orm.Model):
    ''' Product for link import log
    '''
    _inherit = 'purchase.order'

    # -------------
    # Button event:
    # -------------
    # TODO Migrate in a new module?
    def action_import_product_from_csv(self, cr, uid, ids, context=None):
        ''' Import detail button
        '''
        filename = '/home/administrator/photo/xls/inventory' # TODO parametrize
        max_line = 15000
        _logger.info('Start import from path: %s' % filename)

        # Pool used:
        line_pool = self.pool.get('purchase.order.line')
        product_pool = self.pool.get('product.product')
        log_pool = self.pool.get('log.importation')

        purchase_proxy = self.browse(cr, uid, ids, context=context)[0]
        error = annotation = ''
        
        if not purchase_proxy.filename:        
            raise osv.except_osv(
                _('Import error'), 
                _('Need a file name to import in path %s' % filename),
                )  

        purchase_product = {} # converter key=product ID, value=item ID
        for item in purchase_proxy.order_line:
            purchase_product[item.product_id.id] = item.id

        # ---------------------------------------------------------------------
        #                Open XLS document (first WS):
        # ---------------------------------------------------------------------
        # ----------------
        # Read excel file:
        # ----------------
        try:
            filename = os.path.join(filename, purchase_proxy.filename)
            # from xlrd.sheet import ctype_text   
            wb = xlrd.open_workbook(filename)
            ws = wb.sheet_by_index(0)
        except:
            error = 'Error opening XLS file: %s' % (sys.exc_info(), )
            raise osv.except_osv(
                _('Open file error'), 
                _('Cannot found file: %s' % filename),
                )  

        # ----------------------------------
        # Create import log for this import:
        # ----------------------------------
        log_id = log_pool.create(cr, uid, {
            'purchase_id': purchase_proxy.id,
            'name': '%s [%s]' % (
                purchase_proxy.name or 'No name',
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
            'error': error,
            # Note: Extra info write at the end
            }, context=context)

        if error:
            _logger.error('Error import product: %s' % (sys.exc_info(), ))
            return False

        for i in range(0, max_line):
            try:
                row = ws.row(i) # generate error at end
            except:
                # Out of range error ends import:
                annotation += _('Import end at line: %s\n') % i
                break

            try:
                # Loop on colums (trace)
                try:
                    default_code = str(row[0].value).replace('.0', '')
                except:
                    default = ''    
                # Search product with code:
                if not default_code:
                    _logger.error('Product %s not found' % row[0].value)
                    error += _(
                        'Error no code present in line: <b>%s</b></br>') % i
                    continue # jump

                try:
                    product_qty = float(row[1].value)
                except:
                    product_qty = 0

                try:
                    price_unit = float(row[2].value)
                except:
                    price_unit = 0
                    #_logger.warning('Keep 0 the value: %s' % product_qty)    
                #TODO lot = row[2].value 
                
                if not product_qty:
                    # XXX not warning log 
                    #_logger.warning('%s. Jumped line: %s [%s]' % (
                    #    i, default_code, row[1].value))
                    continue
                

                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)
                if not product_ids:
                    error += _(
                        '%s. Error code not found, code: <b>%s</b></br>') % (
                            i, default_code)
                    continue # jump
                elif len(product_ids) > 1:
                    error += _(
                        '''%s. Error more code (take first), 
                            code: <b>%s</b></br>''') % (
                                i, default_code)                
                product_id = product_ids[0]
                product_proxy = product_pool.browse(
                    cr, uid, product_id, context=context)

                state = 'create'
                if product_qty:
                    if product_id in purchase_product: # Update line
                        line_pool.write(cr, uid, purchase_product[product_id], {
                            'product_qty': product_qty,
                            'price_unit': price_unit, # TODO accept? 1.0,
                            'product_uom': product_proxy.uom_id.id
                            #'location_id': purchase_proxy.location_id.id,
                            }, context=context)                        
                        state = 'update'
                    else: # create line
                        line_pool.create(cr, uid, {
                            'name': default_code,
                            'date_planned': '2015-12-31',
                            'product_id': product_id,
                            'order_id': purchase_proxy.id,
                            'product_qty': product_qty,
                            #'location_id': purchase_proxy.location_id.id,
                            'price_unit': price_unit, # TODO accept0? 1.0,
                            'product_uom': product_proxy.uom_id.id
                            }, context=context)
                # for no product qty doesn't create purchase row, only update
                # date in product ref.            
         
                # Some fast info in product:
                product_pool.write(cr, uid, product_id, {
                    'purchase_id': ids[0],
                    'inventory_start': product_qty,
                    'inventory_date': datetime.now().strftime('%Y-01-01'),
                    }, context=context)

                _logger.info('%s. Product %s %s to: %s' % (
                    i, default_code, state, product_qty))
            except:
                error += _('%s. Import error code: <b>%s</b> [%s]</br>') % (
                    i, default_code, sys.exc_info())
                    
        log_pool.write(cr, uid, log_id, {
            'error': error,
            'note': '''
                File: <b>%s</b></br>
                Import note: <i>%s</i></br>
                ''' % (
                    filename, annotation,
                    ),
            }, context=context)

        _logger.info('End import XLS purchase file: %s' % (
            purchase_proxy.filename))
        return True
            
    _columns = {
        'filename': fields.char('Filename', size=80),
        'csv_import_id': fields.many2one('log.importation',
            'Log import', ondelete='set null'),
        }

class StockInventory(orm.Model):
    ''' Product for link import log
    '''
    _inherit = 'stock.inventory'

    # -------------
    # Button event:
    # -------------
    def action_import_product_from_csv(self, cr, uid, ids, context=None):
        ''' Import detail button
        '''
        filename = '/home/administrator/photo/xls' # TODO parametrize
        max_line = 10000
        _logger.info('Start import from path: %s' % filename)

        # Pool used:
        line_pool = self.pool.get('stock.inventory.line')
        product_pool = self.pool.get('product.product')
        log_pool = self.pool.get('log.importation')

        inventory_proxy = self.browse(cr, uid, ids, context=context)[0]
        error = annotation = ''
        
        if not inventory_proxy.filename:        
            raise osv.except_osv(
                _('Import error'), 
                _('Need a file name to import in path %s' % filename),
                )  

        inventory_product = {} # converter key=product ID, value=item ID
        #for item in inventory_proxy.order_line:
        #    inventory_product[item.product_id.id] = item.id
        
        # ---------------------------------------------------------------------
        #                Open XLS document (first WS):
        # ---------------------------------------------------------------------
        # ----------------
        # Read excel file:
        # ----------------
        try:
            filename = os.path.join(filename, inventory_proxy.filename)
            # from xlrd.sheet import ctype_text   
            wb = xlrd.open_workbook(filename)
            ws = wb.sheet_by_index(0)
        except:
            error = 'Error opening XLS file: %s' % (sys.exc_info(), )
            raise osv.except_osv(
                _('Open file error'), 
                _('Cannot found file: %s' % filename),
                )  

        # ----------------------------------
        # Create import log for this import:
        # ----------------------------------
        log_id = log_pool.create(cr, uid, {
            'inventory_id': inventory_proxy.id,
            'name': '%s [%s]' % (
                inventory_proxy.name or 'No name',
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)),
            'error': error,
            # Note: Extra info write at the end
            }, context=context)

        if error:
            _logger.error('Error import product: %s' % (sys.exc_info(), ))
            return False
        
        for i in range(0, max_line):
            try:
                row = ws.row(i) # generate error at end
            except:
                # Out of range error ends import:
                annotation += _('Import end at line: %s\n') % i
                break

            try:
                # Loop on colums (trace)
                default_code = row[0].value
                product_qty = row[1].value # TODO check if is float!
                #TODO lot = row[2].value 
                
                # Search product with code:
                if not default_code:
                    error += _(
                        'Error no code present in line: <b>%s</b></br>') % i
                    continue # jump

                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)

                if not product_ids:
                    error += _(
                        '%s. Error code not found, code: <b>%s</b></br>') % (
                            i, default_code)
                    continue # jump

                elif len(product_ids) > 1:
                    error += _(
                        '''%s. Error more code (take first), 
                            code: <b>%s</b></br>''') % (
                                i, default_code)
                
                product_id = product_ids[0]
                if product_id in inventory_product: # Update line
                    line_pool.write(cr, uid, inventory_product[product_id], {
                        'product_qty': product_qty,
                        'location_id': inventory_proxy.location_id.id,
                        }, context=context)                        
                else: # create line
                    line_pool.create(cr, uid, {
                        'product_id': product_id,
                        'inventory_id': inventory_proxy.id,
                        'product_qty': product_qty,
                        'location_id': inventory_proxy.location_id.id,
                        #'product_uom_id': TODO use default correct for product!
                        }, context=context)
                _logger.info('Product %s set to: %s' % (
                    default_code, product_qty))
            except:
                error += _('%s. Import error code: <b>%s</b> [%s]</br>') % (
                    i, default_code, sys.exc_info())
                    

        log_pool.write(cr, uid, log_id, {
            'error': error,
            'note': '''
                File: <b>%s</b></br>
                Import note: <i>%s</i></br>
                ''' % (
                    filename, 
                    annotation,
                    ),
            }, context=context)

        _logger.info('End import XLS inventory file: %s' % (
            inventory_proxy.filename))
        return True
        
            
    _columns = {
        'filename': fields.char('Filename', size=80),
        'csv_import_id': fields.many2one('log.importation',
            'Log import', ondelete='set null'),
        }

class LogImportation(orm.Model):
    ''' Importation log element
    ''' 
    _inherit = 'log.importation'

    _columns = {
        'inventory_id': fields.many2one('stock.inventory', 'Inventory'),
        'purchase_id': fields.many2one('purchase.order', 'Purchase'),
        #'picking_id': fields.many2one('stock.picking', 'Picking'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
