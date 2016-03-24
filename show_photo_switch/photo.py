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

class ResUsers(orm.Model):
    """ Model name: SaleOrder
    """    
    _inherit = 'res.users'
   
    _columns = {
        'always_show_photo': fields.boolean(
            'Always show photo', help='In product form show product photo'),
        }

class ProductProduct(orm.Model):
    """ Model name: Product
    """    
    _inherit = 'product.product'
   
    def set_context_no_photo(self, cr, uid, ids, context=None):
        ''' Set no inventory in res.users parameter
        '''
        self.pool.get('res.users').write(cr, uid, [uid], {
            'always_show_photo': False,
            }, context=context)
        return     

    def set_context_yes_photo(self, cr, uid, ids, context=None):
        ''' Set no inventory in res.users parameter
        '''    
        self.pool.get('res.users').write(cr, uid, [uid], {
            'always_show_photo': True,
            }, context=context)
        return    

    # ----------------
    # Fields function:                
    # ----------------
    def _get_user_always_show_photo_status(self, cr, uid, ids, fields, args, 
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
                cr, uid, user_id, context=context).always_show_photo
        return res
    
    _columns = {
        'always_show_photo': fields.function(
            _get_user_always_show_photo_status, method=True, 
            type='boolean', string='Show photo',
            store=False), 
       }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
