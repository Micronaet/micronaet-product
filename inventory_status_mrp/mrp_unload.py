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
import xlsxwriter # XLSX export
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

class MrpProduction(orm.Model):
    """ Model name: MRP PRoduction
    """
    
    _inherit = 'mrp.production'
    
    def schedule_unload_mrp_material(self, cr, uid, context=None):
        ''' Update product field with unloaded elements
        '''
        # ---------------------------------------------------------------------
        # Utility function:
        # ---------------------------------------------------------------------
        def write_xls_log(log):
            ''' Write log in WS updating counter
            '''
            col = 0
            for item in log:
                self.WS.write(self.counter, col, item)
                col += 1
            self.counter += 1
            return
            
        # ---------------------------------------------------------------------
        # XLS log export:        
        # ---------------------------------------------------------------------
        filename = '/home/administrator/photo/log/mrp_unload.xlsx'
        WB = xlsxwriter.Workbook(filename)

        self.WS = WB.add_worksheet('Unload') # Work Sheet:        
        self.counter = 0 # Row counters:
        # Write header
        write_xls_log([
            'MRP', 
            'Date',
            'Order',
            'Product',
            'Maked',
            'ID',
            'Component',
            'Maked',
            'State',
            ])        
        
        #from_date = '2016-08-30'
        # After inventory date:
        from_date = '2017-01-01 00:00:00'
        
        mrp_ids = self.search(cr, uid, [        
            # State filter:
            #('state', 'not in', ('done', 'cancel')),
            
            # Period filter (only up not down limit)
            ('date_planned', '>=', from_date),
            ], context=context)
            
        product_pool = self.pool.get('product.product')   
        cr.execute('''
            UPDATE product_product set mx_mrp_out=0;
            ''')                        

        # Generate MRP total componet report with totals:
        unload_db = {}
        for mrp in self.browse(cr, uid, mrp_ids, context=context):
            for sol in mrp.order_line_ids:
                # Total elements:
                maked = sol.product_uom_maked_sync_qty                                
                if not maked: 
                    continue
                for component in sol.product_id.dynamic_bom_line_ids:                    
                    product = component.product_id
                                            
                    cmpt_maked = maked * component.product_qty
                    if product.id in unload_db: 
                        unload_db[product.id] += cmpt_maked
                    else:    
                        unload_db[product.id] = cmpt_maked
                    
                    write_xls_log([
                        mrp.name, mrp.date_planned, sol.order_id.name,
                        # Product
                        sol.product_id.default_code, maked,
                        # Component
                        product.id, product.default_code, cmpt_maked,
                        mrp.state,
                        ])
                        
        WB.close()  
        for product_id, unload in unload_db.iteritems():
            product_pool.write(cr, uid, product_id, {
                'mx_mrp_out': unload,
                }, context=context)                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
