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
    """ Model name: Product
    """
    
    _inherit = 'product.product'

    def _field_latest_supplier_data(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Update latest supplier field
        '''
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = {
                'latest_supplier_id': False,
                'latest_price': False,
                'latest_price_date': False,
                }            
            for supplier in product.supplier_ids:
                for price in supplier.pricelist_ids:
                    if not price.active:
                        continue
                    max_date = res[product.id]['latest_price_date'] # readability
                    if not max_date or (
                            price.date_quotation and \
                            price.date_quotation > max_date):

                        # This is the latest record:                        
                        res[product.id]['latest_supplier_id'] = \
                            price.suppinfo_id.name.id
                        res[product.id]['latest_price'] = price
                        res[product.id]['latest_price_date'] = \
                            price.date_quotation
        return res
        
    # -------------------------------------------------------------------------
    # Store function:
    # -------------------------------------------------------------------------
    #def _get_default_code_from_product(self, cr, uid, ids, context=None):
    #    ''' Change defauld code in product
    #    '''
    #    _logger.warning('Change default_code in product.product')
    #    sol_pool = self.pool.get('sale.order.line')
    #    return sol_pool.search(cr, uid, [
    #        ('product_id', 'in', ids),
    #        ], context=context)
    _columns = {
        'latest_supplier_id': fields.function(
            _field_latest_supplier_data, method=True, 
            type='many2one', relation='res.partner', 
            string='Ultima fornitura di', store=False, 
            multi=True),
        'latest_price': fields.function(
            _field_latest_supplier_data, method=True, 
            type='many2one', string='Ultimo prezzo',
            store=False, multi=True),
        'latest_price_date': fields.function(
            _field_latest_supplier_data, method=True, 
            type='date', string='Ultima data prezzo',
            store=False, multi=True),
                        
        #'order_date': fields.related(
        #    'order_id', 'date_order', type='date',
        #    store={
        #        'sale.order.line': (
        #            _get_date_order_from_sol, ['order_id'], 10),
        #        'sale.order': (
        #            _get_date_order_from_order, ['date_order'], 10),
        #        }, string='Order date'),
        }
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
