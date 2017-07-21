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
    _wireframe_path = 'linedrawing'
    _wireframe_extension = 'jpg'
    
    # -------------------------------------------------------------------------
    # Utility:
    # -------------------------------------------------------------------------
    def prepare_filename(self, default_code):
        ''' Upper the default code and replace spaces with _ char
        '''
        return (default_code or '').upper().replace(' ', '_')
    
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
    def _set_wireframe_image(self, cr, uid, item_id, name, value, 
            fnct_inv_arg=None, context=None):
        ''' Write image as stored file when insert
        '''
        company_pool = self.pool.get('res.company')
        
        product_folder = os.path.expanduser(company_pool.get_base_local_folder(
            cr, uid, subfolder=self._wireframe_path, context=context))

        product_proxy = self.browse(cr, uid, item_id, context=context)
        default_code = self.prepare_filename(product_proxy.default_code)
        if not default_code:
            raise osv.except_osv(
                _('Error'), 
                _('Set default code before save image (name = CODE.png)'),
                )
        
        filename = os.path.join(
            product_folder, '%s.%s' % (
                default_code, self._wireframe_extension))

        product_file = open(filename, 'wb')
        if value:
            product_file.write(base64.decodestring(value))
        product_file.close()        
        return True
    
    def _get_wireframe_image(self, cr, uid, ids, field, args, context=None):
        ''' Use base folder for get ID.png filename from filesystem
        '''
        company_pool = self.pool.get('res.company')        
        product_folder = os.path.expanduser(company_pool.get_base_local_folder(
            cr, uid, subfolder=self._wireframe_path, context=context))

        parent_block = self.get_config_parameter_list(
            cr, uid, context=context)
        res = {}

        for product in self.browse(cr, uid, ids, context=context):
            default_code = self.prepare_filename(product.default_code)
            
            # Jump if no default code:
            if not default_code:
                res[product.id] = ''
                continue
            
            parent_code = [default_code]    
            for parent in parent_block:
                parent_code.append(default_code[0:parent].strip('_'))

            for img_name in parent_code:
                # TODO manage parent wireframe
                filename = os.path.join(
                    product_folder, '%s.%s' % (
                        img_name, 
                        self._wireframe_extension,
                        ))
                try:
                    f = open(filename , 'rb')
                    res[product.id] = base64.encodestring(f.read())
                    f.close()
                    _logger.info('Linedrawing: %s' % filename)        
                except:
                    _logger.warning('No Linedrawing: %s' % filename)        
                    res[product.id] = ''            
                if res[product.id]:
                    break                
        return res

    _columns = {
        'wireframe_parent_id': fields.many2one(
            'product.product', 'Linedrawing parent'),
        'wireframe': fields.function(_get_wireframe_image, 
            fnct_inv=_set_wireframe_image, string='Image',
            type='binary', method=True),
        }       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
