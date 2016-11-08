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


class ProductPackage(orm.Model):
    """ Model name: ProductPackage
    """    
    _inherit = 'product.packaging'
    
    # On change event:
    def onchange_ul_dimension(self, cr, uid, ids, ul, context=None):
        ''' Load dimension from ul
        '''
        ul_pool = self.pool.get('product.ul')
        res = {}
        if not ul:
           return 
        ul_proxy = ul_pool.browse(cr, uid, ul, context=context)
        res['value'] = {
            'pack_p': ul_proxy.length,
            'pack_h': ul_proxy.height,
            'pack_l': ul_proxy.width,            
            }
        return res           
           
    # Button event:
    def load_from_pack(self, cr, uid, ids, context=None):
        ''' Load pack measure from box
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        return self.write(cr, uid, ids, {
            'pack_p': current_proxy.ul.length,
            'pack_h': current_proxy.ul.height,
            'pack_l': current_proxy.ul.width,
            }, context=context)
            
    # TODO use as related?
    _columns = {
        'pack_l': fields.float('L. Imb.', digits=(16, 2)),
        'pack_h': fields.float('H. Imb.', digits=(16, 2)),
        'pack_p': fields.float('P. Imb.', digits=(16, 2)),
        'pack_volume': fields.float('Volume', digits=(16, 2)), # TODO related?
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
