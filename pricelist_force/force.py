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

class ProductPricelistVersion(orm.Model):
    """ Model name: ProductPricelistVersion
    """
    
    _inherit = 'product.pricelist.version'
    
    # Button event:
    def force_pricelist_price_from_version(self, cr, uid, ids, context=None):
        ''' Calculate price for all elements and force in pricelist
        '''
        # Pool used:
        product_pool = self.pool.get('product.product')
        
        version_proxy = self.browse(cr, uid, ids, context=context)[0]
        i = 0
        for item in version_proxy.items_id:
            i += 1
            product_ids = product_pool.search(cr, uid, [
                ('id', '=', item.product_id.id)], context=context)
            if not product_ids:
                _logger.error('%s. Code: %s not found!' % (
                    i,
                    item.product_id.default_code, 
                    ))
                continue

            if len(product_ids) > 1:
                _logger.warning('%s. Code: %s > found more than one' % (
                    i,
                    item.product_id.default_code, 
                    ))
            
            product_pool.write(cr, uid, product_ids, {
                'lst_price': item.price_surcharge, # TODO change !!!!!
                }, context=context)
            _logger.info('%s. Code: %s updated' % (
                i,
                item.product_id.default_code, 
                ))
        return True    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
