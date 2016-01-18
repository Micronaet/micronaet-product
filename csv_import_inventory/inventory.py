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
        for item in inventory_proxy.line_ids:
            inventory_product[item.product_id.id] = item.id
        
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
        'csv_import_id': fields.many2one('log.importation',
            'Log import', ondelete='set null'),
        }

class LogImportation(orm.Model):
    ''' Importation log element
    ''' 
    _inherit = 'log.importation'

    _columns = {
        'inventory_id': fields.many2one('stock.inventory', 'Inventory'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
