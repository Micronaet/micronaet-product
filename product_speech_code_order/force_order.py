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

class SaleOrder(orm.Model):
    """ Model name: Sale Order
    """    
    _inherit = 'sale.order'
    
    def force_product_speech_code_from_order(self, cr, uid, ids, context=None):
        ''' Force calculation for details product
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        product_pool = self.pool.get('product.product')
        done_ids = []
        for line in current_proxy.order_line:
            product_id = line.product_id.id
            if product_id in done_ids:
                continue
            product_pool.generate_name_from_code(
                cr, uid, [product_id], context=context)
            done_ids.append(product_id)    
        return True

class SaleOrderLine(orm.Model):
    """ Model name: Sale Order Line
    """    
    _inherit = 'sale.order.line'
    
    def force_product_speech_code_from_order_line(
            self, cr, uid, ids, context=None):
        ''' Force calculation for details product
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        
        line = self.browse(cr, uid, ids, context=context)[0]
        product_pool = self.pool.get('product.product')
        product_id = line.product_id.id
        product_pool.generate_name_from_code(
            cr, uid, [product_id], context=context)
        return True
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
