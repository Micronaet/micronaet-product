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
from openerp import SUPERUSER_ID #, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)

class SaleOrderLine(orm.Model):
    """ Model name: SaleOrderLine
    """
    
    _inherit = 'sale.order.line'

    def get_movements_oc(self, cr, uid, ids, context=None):
        product_pool = self.pool.get('product.product')
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        return product_pool.get_movements_type(cr, uid, [
            line_proxy.product_id.id], 'oc', context=context)
        
    def get_movements_of(self, cr, uid, ids, context=None):
        product_pool = self.pool.get('product.product')
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        return product_pool.get_movements_type(cr, uid, [
            line_proxy.product_id.id], 'of', context=context)
        
    def get_movements_in(self, cr, uid, ids, context=None):
        product_pool = self.pool.get('product.product')
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        return product_pool.get_movements_type(cr, uid, [
            line_proxy.product_id.id], 'in', context=context)
        
    def get_movements_out(self, cr, uid, ids, context=None):
        product_pool = self.pool.get('product.product')
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        return product_pool.get_movements_type(cr, uid, [
            line_proxy.product_id.id], 'out', context=context)

    def get_movements_inv(self, cr, uid, ids, context=None):
        product_pool = self.pool.get('product.product')
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        return product_pool.get_movements_type(cr, uid, [
            line_proxy.product_id.id], 'inv', context=context)

    _columns = {
        'mx_of_in': fields.related('product_id', 'mx_of_in', 
            type='float', string='OF in', store=False), 
        'mx_oc_out': fields.related('product_id', 'mx_oc_out', 
            type='float', string='OC out', store=False), 
        'mx_net_qty': fields.related('product_id', 'mx_net_qty', 
            type='float', string='Stock net', store=False), 
        'mx_lord_qty': fields.related('product_id', 'mx_lord_qty', 
            type='float', string='Stock lord', store=False),
        'mx_of_date': fields.related('product_id', 'mx_of_date', 
            type='char', size=100, string='OF date', store=False),
        #'mx_inv_qty': fields.function(
        #'mx_mm_qty': fields.function(
        #'mx_bf_in': fields.function(
        #'mx_bc_out': fields.function(
        
        #'mx_net_qty': fields.function(
        #'mx_lord_qty': fields.function(
        #'mx_bc_ids': fields.function(
        #'mx_oc_ids': fields.function(
        #'mx_of_ids': fields.function(
        #'mx_bf_ids': fields.function(
        #'mx_inv_ids': fields.function(
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
