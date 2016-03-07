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
import urllib
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
    
    
    _columns = {
        
    }
class ProductProductImage(osv.osv):
    ''' Add extra function and fields for manage picture for product
    '''
    _inherit = 'product.product'

    def get_image_qrcode(self, cr, uid, ids, context=None):
        ''' Get (or create before QR code image)
        '''
        if type(ids) not in (list, tuple):
            ids = [ids]
        img = ''
        folder_path = '~/photo/qrcode' #self.pool.get('product.quotation.folder')
        folder_path = os.path.expanduser(folder_path)
        
        for product in self.browse(cr, uid, ids, context=context):
            default_code = '%s.png' % product.default_code
            filename = os.path.join(folder_path, product.default_code)            
            try:
                (qrcode, header) = urllib.urlretrieve(filename)
                f = open(qrcode , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            if not img:
                #create QR Code:    
                pass

            # codice padre (5 cifre):
            #if (not img) and code and len(code) >= 5:
            #    try:
            #        padre = code[:5]
            #        (filename, header) = urllib.urlretrieve(
            #            image_path + padre.replace(" ", "_") + extension)
            #        f = open(filename , 'rb')
            #        if with_log:
            #            _logger.info('>> Load image: %s' % filename) # TODO debug
            #        img = base64.encodestring(f.read())
            #        f.close()
            #    except:
            #         img = ''
        return img

    def _get_image_qrcode_field(self, cr, uid, ids, field_name, arg, 
            context=None):
        res = {}
        for item_id in ids:
            res[item] = self.get_image_qrcode(
                cr, uid, item_id, context=context)
        return res

    _columns = {
        'weblink_qrcode': fields.function(_get_image_qrcode_field, 
            type="binary", method=True),
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
