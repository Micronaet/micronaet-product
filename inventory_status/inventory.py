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
    
    # button event:
    def get_sale_order_line_status(self, cr, uid, ids, context=None):
        ''' Open sol list
        '''   
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order line status',
            'res_model': 'sale.order.line',
            #'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'view_id': view_id,
            #'target': 'new',
            #'nodestroy': True,
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
        
    _columns = {
        'status_ordered': fields.function(
             _get_status_ordered, method=True, type='float', string='Ordered', 
             store=False),
        #'status_virtual': fields.function(
        #     _get_status_ordered, method=True, type='float', 
        #     string='Virtual available', store=False, multi=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
