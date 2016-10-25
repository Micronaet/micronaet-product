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
import base64
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
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'

    # Parameters:
    _component_path = 'component'
    _component_extension = 'png'
    
    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def get_config_parameter_list(self, cr, uid, context=None):
        ''' Read parameter: 
        '''    
        key = 'product.default.product.parent'
        config_pool = self.pool.get('ir.config_parameter')
        config_ids = config_pool.search(cr, uid, [
            ('key', '=', key)], context=context)
        if not config_ids:
            _logger.warning('Parameter not found: %s' % key)
            return []
        config_proxy = config_pool.browse(
            cr, uid, config_ids, context=context)[0]
        return eval(config_proxy.value)    
        
    # -------------------------------------------------------------------------
    # Functional field:
    # -------------------------------------------------------------------------
    def _set_component_image(self, cr, uid, item_id, name, value, 
            fnct_inv_arg=None, context=None):
        ''' Write image as stored file when insert
        '''
        company_pool = self.pool.get('res.company')
        
        product_folder = os.path.expanduser(company_pool.get_base_local_folder(
            cr, uid, subfolder=self._component_path, context=context))

        product_proxy = self.browse(cr, uid, item_id, context=context)
        
        filename = os.path.join(product_folder, '%s.%s' % (
            product_proxy.id, self._component_extension))

        product_file = open(filename, 'wb')
        if value:
            product_file.write(base64.decodestring(value))
        product_file.close()
        _logger.info('Saved image: %s' % filename)
        return True
    
    def _get_component_image(self, cr, uid, ids, field, args, context=None):
        ''' Use base folder for get ID.png filename from filesystem
        '''
        company_pool = self.pool.get('res.company')        
        product_folder = os.path.expanduser(company_pool.get_base_local_folder(
            cr, uid, subfolder=self._component_path, context=context))

        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            filename = os.path.join(product_folder, '%s.%s' % (
                product.id, self._component_extension))
            try:
                f = open(filename , 'rb')
                res[product.id] = base64.encodestring(f.read())
                f.close()
            except:
                res[product.id] = ''            
        return res

    _columns = {
        'component_image': fields.function(_get_component_image, 
            fnct_inv=_set_component_image, string='Image',
            type='binary', method=True),
        }       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
