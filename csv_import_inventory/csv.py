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
        product_pool = self.pool.get('product.product')
        log_pool = self.pool.get('product.product.importation')

        inventory_proxy = self.browse(cr, uid, ids, context=context)[0] 
        
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

        # ----------------------------------
        # Create import log for this import:
        # ----------------------------------
        log_id = log_pool.create(cr, uid, {
            'name': wiz_proxy.comment or 'No comment',
            'error': error,
            # Extra info write at the end
            }, context=context)
        log_view['res_id'] = log_id # Save record ID to open after import
        if error:
            return log_view
        
        # ------------------------
        # Create inventory header:
        # ------------------------

        error = annotation = ''
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
                data = {                
                    'csv_import_id': log_id # link to log event
                    
                        
                product_pool.write(cr, uid, product_ids[0], data, 
                    context=context)
                _logger.info('Update product code: %s' % default_code)            
            except:
                error += _('%s. Import error code: <b>%s</b> [%s]</br>') % (
                    i, default_code, sys.exc_info())
                    

        # End operations:    
        context['lang'] = current_lang
        # Update lof with extra information:            
        log_pool.write(cr, uid, log_id, {
            'inventory_id': inventory_id, # Link
            'error': error,
            'note': '''
                File: <b>%s</b></br>
                Import note: <i>%s</i></br>
                Operator note:</br><i>%s</i>
                ''' % (
                    wiz_proxy.name, 
                    annotation, 
                    wiz_proxy.note or ''),
            }, context=context)

        _logger.info('End import XLS product file: %s' % wiz_proxy.name)
        return log_view
        
            
    _columns = {
        'fielname': fields.char(
            'Inventory filename', size=80), 
        'csv_import_id': fields.many2one('product.product.importation',
            'Log import', ondelete='set null'),
        }

class ProductProductImportation(orm.Model):
    ''' Importation log element
    ''' 
    _inherit = 'product.product.importation'

    _columns = {
        'inventory_id': fields.many2one('stock.inventory', 'Inventory'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
