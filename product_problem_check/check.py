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

class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'
    
    # --------
    # Utility:
    # --------
    def check_product_default_code_presence(self, cr, uid, context=None):
        ''' Check product code presence
        '''
        return self.search(cr, uid, [
            ('default_code', '=', False),
            ('is_family', '=', False),
            ('active', '=', True),
            #('type', '!=', 'service'),
            ], context=context)
        
    def check_product_bom_presence(self, cr, uid, context=None):
        ''' Check BOM presence
        '''
        
        product_ids = []
        return product_ids

    def check_product_double_code_presence(self, cr, uid, context=None):
        ''' Check product double code
        '''
        query = """
            SELECT 
                default_code
            FROM 
                product_product
            GROUP BY
                default_code
            HAVING 
                count(*) > 1;    
            """
        default_codes = [
            item for cr.execute(query)]
        import pdb; pdb.set_trace()    
        product_ids = self.search(cr, uid, [
            ('default_code', 'in', default_codes)], context=context)    
        return product_ids
        
    def show_product_detail_check_product(self, cr, uid, ids, context=None):
        ''' Open view form
        '''
        model_pool = self.pool.get('ir.model.data')
        tree_view_id = model_pool.get_object_reference(
            cr, uid,
            'product_problem_check', 
            'view_product_product_check_tree')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Product detail'),
            'view_type': 'form',
            'view_mode': 'form', # tree
            'res_id': ids[0],
            'res_model': 'product.product',
            'view_id': False,#tree_view_id,
            'views': [(False, 'form')], #(tree_view_id, 'tree'), 
            #'domain': [('id', 'in', ids)],
            #'context': {},
            'target': 'current',
            'nodestroy': False,
            }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
