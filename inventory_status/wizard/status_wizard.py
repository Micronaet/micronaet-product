# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Abstract (http://www.abstract.it)
#    Copyright (C) 2014 Agile Business Group (http://www.agilebg.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class ProductProductStatusStockWizard(orm.TransientModel):
    ''' Wizard report
    '''
    _name = 'product.product.status.stock.wizard'
    _description = 'Status wizard'

    def _get_status(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        context = context or {}
        product_id = context.get('active_id', 0)
        return self.pool.get('product.product').get_inventory_values(
            cr, uid, [product_id], context=context)[product_id]
   
    _columns = {
        'status_inventory': fields.function(
            _get_status, method=True, type='float', string='Inventory', 
            store=False, multi=True),
        'status_movement': fields.function(
            _get_status, method=True, type='float', string='Movement', 
            store=False, multi=True),
        'status_order_in': fields.function(
            _get_status, method=True, type='float', string='OF in', 
            store=False, multi=True),
        'status_order_out': fields.function(
            _get_status, method=True, type='float', string='OC out', 
            store=False, multi=True),
        'status_load_in': fields.function(
            _get_status, method=True, type='float', string='BF in ', 
            store=False, multi=True),
        'status_load_out': fields.function(
            _get_status, method=True, type='float', string='BC out', 
            store=False, multi=True),    
        }
