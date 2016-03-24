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
    """ Model name: SaleOrder
    """    
    _inherit = 'sale.order'

    # Button:
    def with_inventory_status(self, cr, uid, ids, context=None):
        ''' Start inventory
        '''
        context = context or {}
        user_id = context.get('uid', False)
        return self.pool.get('res.users').write(cr, uid, user_id, {
            'no_inventory_status': False,
            }, context=context)
        
    def without_inventory_status(self, cr, uid, ids, context=None):
        ''' Stop inventory
        '''
        context = context or {}
        user_id = context.get('uid', False)
        return self.pool.get('res.users').write(cr, uid, user_id, {
            'no_inventory_status': True,
            }, context=context)
    
    # ----------------
    # Fields function:                
    # ----------------
    def _get_user_no_inventory_status(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Fields function for calculate status for inventory for logget user
        '''
        context = context or {}
        res = {}
        if len(ids) > 1:
            return
        user_id = context.get('uid', False)
        res[ids[0]] = False
        if user_id: 
            res[ids[0]] = self.pool.get('res.users').browse(
                cr, uid, user_id, context=context).no_inventory_status
        return res
    
    _columns = {
        'no_inventory_status': fields.function(
            _get_user_no_inventory_status, method=True, 
            type='boolean', string='No inventory',
            store=False), 
       }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
