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
        filename = '/home/thebrush/Scrivania/GPB/Importazioni/file/Bestluck -1.xls'
        from_line = 14
        to_line = 24
        
        if context is None:
           context = {}

        # Wizard proxy:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        
        # Pool used:
        production_pool = self.pool.get('product.product')
        
        # ---------------------------------------------------------------------
        #                Open XLS document (first WS):
        # ---------------------------------------------------------------------
        #from xlrd.sheet import ctype_text   
        wb = xlrd.open_workbook(filename)
        #sheet_names = wb.sheet_names()[0]
        #ws = wb.sheet_by_name(sheet_names)
        ws = xl_workbook.sheet_by_index(0)
        #row = ws.row(0)  # 1st row
        i = 0
        for row in ws.row:
            i += 1
            if i <= from_line:
                continue
            if i > to_line:    
                break

            print row
            #for idx, cell_obj in enumerate(row):


        # Context dict for pass parameter to create lavoration procedure:
              
        #raise osv.except_osv(
        #    _('Error'),
        #    _('Error reading parameter in BOM (for lavoration)'))

        return {}
        #return return_view(
        #    self, cr, uid, p_id, 'mrp.mrp_production_form_view', 
        #    'mrp.production', context=context) 


    _columns = {
        'name': fields.char('File name', size=80, readonly=True),
        'comment': fields.char('Log comment', size=80),
        'note': fields.text('Note', readonly=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
