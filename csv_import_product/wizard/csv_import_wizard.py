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

class ProductProductCsvImportWizard(orm.TransientModel):
    ''' Wizard to import CSV product updating price
    '''    
    _name = 'product.product.csv.import.wizard'

    # ---------------
    # Utility funtion
    # ---------------
    def preserve_window(self, cr, uid, ids, context=None):
        ''' Create action for return the same open wizard window
        '''
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[
            ('model', '=', 'mrp.production.create.wizard'),
            ('name', '=', 'Create production order') # TODO needed?
            ], context=context)
        
        return {
            'type': 'ir.actions.act_window',
            'name': "Wizard create production order",
            'res_model': 'mrp.production.create.wizard',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'nodestroy': True,
            }

    # --------------
    # Wizard button:
    # --------------
    def action_import_csv(self, cr, uid, ids, context=None):
        ''' Import pricelist and product description
        '''
        # TODO:
        filename = '/home/thebrush/Scrivania/GPB/Importazioni/file'
        
        if context is None:
           context = {}

        # Pool used:
        product_pool = self.pool.get('product.product')
        log_pool = self.pool.get('product.product.importation')

        # Wizard proxy:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        from_line = wiz_proxy.from_line # 14
        to_line = wiz_proxy.to_line #24
        filename = os.path.join(filename, wiz_proxy.name)
        
        # Load trace:
        column_trace = {}
        for item in wiz_proxy.trace_id.column_ids:
            column_trace[item.column] = item.field
        
        # ---------------------------------------------------------------------
        #                Open XLS document (first WS):
        # ---------------------------------------------------------------------
        # from xlrd.sheet import ctype_text   
        wb = xlrd.open_workbook(filename)
        ws = wb.sheet_by_index(0)
        # row = ws.row(0)  # 1st row
        
        # Create import log for this import:
        import pdb; pdb.set_trace()
        log_id = log_pool.create(cr, uid, {
            'name': wiz_proxy.comment,
            #'datetime',
            #'user_id': 
            'trace_id': wiz_proxy.trace_id.id,
            'note': 'File: %s\n%s' % (wiz_proxy.name, wiz_proxy.note or ''),
            }, context=context)

        for i in range(from_line, to_line + 1): # Note +1!
            row = ws.row(i)
            data = { # product record
                'csv_import_id': log_id, # Link to log record
                }
            
            # Loop on colums (trace)
            for col, field in column_trace.iteritems():
                # TODO check presence:
                #for idx, cell_obj in enumerate(row):
                data[field] = row[col - 1] # Note: start from 0

            # Search product with code:
            default_code = data.get('default_code', False)
            if not default_code:
                _logger.error('Error no code present in line: %s' % i)

            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code)], context=context)

            if not product_ids:
                #raise osv.except_osv(
                #    _('Error'),
                #    _('Error reading parameter in BOM (for lavoration)'))
                _logger.error('%s. Error code not found, code: %s' % (
                    i, default_code))
                continue    
            elif len(product_ids) > 1:
                _logger.error('%s. Error more code (take first), code: %s' % (
                    i, default_code))
            
            product_product.write(
                cr, uid, product_id, data, context=context)[0]

        return return_view(
            self, cr, uid, log_id, 
            'csv_import_product.product_product_importation_form_view', 
            'product.product.importation', context=context)

    _columns = {
        'name': fields.char('File name', size=80, required=True),
        'comment': fields.char('Log comment', size=80, required=True),
        'from_line': fields.integer('From line', required=True), 
        'to_line': fields.integer('To line', required=True), 
        'trace_id': fields.many2one('product.product.importation.trace',
            'Trace', required=True),
        'price_force': fields.selection([
            ('product', 'Price in product form'),
            ('pricelist', 'Pricelist'),            
            ], 'Force price'),            
        'note': fields.text('Note'),
        }
        
    _defaults = {
        'from_line': lambda *x: 1,
        'price_format': lambda *x: 'product',
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
