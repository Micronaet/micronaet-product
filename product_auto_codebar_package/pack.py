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


class ProductPackaging(orm.Model):
    """ Model name: ProductPackaging
    """
    _inherit = 'product.packaging'
    
    # --------------
    # Button events:    
    # --------------
    def generate_barcode_ean13(self, cr, uid, ids, context=None):
        ''' Create EAN code, not duplicated and not in exclude list
        '''
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        if current_proxy.ean:
            raise osv.except_osv(
                _('Error'), 
                _('EAN yet present, delete and press button again'))

        ean13 = self.pool.get('product.codebar.unused').get_ean13(
            cr, uid, context=context)                              
        if ean13:
            return self.write(cr, uid, ids, {
                'ean': ean13,
                }, context=context)        
        return False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
