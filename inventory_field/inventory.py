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

class ProductProductInventoryCategory(orm.Model):
    """ Model name: ProductProductInventoryCategory
    """
    
    _name = 'product.product.inventory.category'
    _description = 'Inventory category'
    
    def force_no_code_category(self, cr, uid, ids, context=None):
        ''' Force all no code to this category
        '''
        product_pool = self.pool.get('product.product')
        
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        product_ids = product_pool.search(cr, uid, [
            ('default_code', '=', False)], context=context)
        product_pool.write(cr, uid, product_ids, {
            'inventory_category_id': current_proxy.id,
            }, context=context)    
        return True    
        
    def force_code_category(self, cr, uid, ids, context=None):
        ''' Force product category with code in text field
        '''
        product_pool = self.pool.get('product.product')
        
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        code = current_proxy.code
        code_list = code.split('\n')
        product_ids = product_pool.search(cr, uid, [
            ('default_code', 'in', code_list)], context=context)
        product_pool.write(cr, uid, product_ids, {
            'inventory_category_id': current_proxy.id,
            }, context=context)    
        return True    
        
    _columns = {
        'name': fields.char(
            'Name', size=64, required=True),
        'note': fields.text('Note'),    
        'code': fields.text('Force code'),         
        }

class ProductProduct(orm.Model):
    ''' Link product to inventory purchase order
    '''
    _inherit = 'product.product'
    
    _columns = {
        # TODO No more use:
        'inventory_start': fields.float(
            'Inventory start', digits=(16, 3)),
        'inventory_delta': fields.float(
            'Inventory delta', digits=(16, 3), 
            help='Delta inventory for post correction retroactive'),
        'inventory_date': fields.date('Inventory date'),    
        
        # XXX Inventory report (keep in isolated module?)
        'inventory_category_id': fields.many2one(
            'product.product.inventory.category', 'Inventory category'),
        'inventory_excluded': fields.boolean('Inventory excluded'),    
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
