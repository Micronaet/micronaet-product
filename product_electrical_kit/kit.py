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

class ProductProductKit(orm.Model):
    """ Model name: ProductProductKit
    """    
    _name = 'product.product.kit'
    _description = 'Product Kit'
    _rec_name = 'product_id'
    _order = 'product_id'
    
    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'component_id': fields.many2one(
            'product.product', 'Component', required=True),
        'qty': fields.integer('Q.ty', required=True),    
        'categ_id': fields.many2one(
            'product.category', 'Category brand', 
            help='Category managed as productor brand'),
        }
    
    _defaults = {
        'qty': lambda *x: 1,
        }    

class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """
    
    _inherit = 'product.product'
    
    def extract_check_report_xlsx(self, cr, uid, ids, context=None):
        ''' Report for check kit definition
        '''
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        
        # ---------------------------------------------------------------------
        # Collect data:
        # ---------------------------------------------------------------------
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        brand_db = {} # NOTE: False >> common part
        title = []        
        for line in current_proxy.component_ids: 
            brand = line.categ_id:
            if brand in brand_db:
                brand_db[brand].append(line)
            else:    
                brand_db[brand] = [line]
                title.extend([
                    5, # qty
                    15, # code
                    40, # name
                    10, # price
                    1 # space
                    ])

        # ---------------------------------------------------------------------
        # Generate XLS file:
        # ---------------------------------------------------------------------
        ws_name = _('KIT Check')        
        excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, title)
        
        #write_xls_line(ws_name, row, line, default_format=False)
        return excel_pool.return_attachment(
            cr, uid, name='KIT Check', name_of_file='kit_check.xlsx') 
        
    def _check_kit_variant(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = ''
            check_tot = item.kit_variant
            if not check_tot:
                continue
            groups = {}
            for cmpt in item.component_ids:
                categ_id = cmpt.categ_id
                if not categ_id:
                    continue
                if categ_id in groups:
                    groups[categ_id] += 1
                else:    
                    groups[categ_id] = 1
                
            for group, tot in groups.iteritems():
                if tot != check_tot:
                    res[item.id] += '%s [%s]\n' % (group.name, tot)
        return res
        
    _columns = {
        'kit': fields.boolean('Kit'),
        'kit_variant': fields.integer('Kit variant', 
            help='Kit number of supplier variant'),
        'kit_variant_check': fields.function(
            _check_kit_variant, method=True, 
            type='text', string='Check variant', store=False), 
        'component_ids': fields.one2many(
            'product.product.kit', 'product_id', 'Component'),  
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
