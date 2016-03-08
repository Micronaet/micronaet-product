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
import qrcode
import base64
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

# TODO Parameters:
root_path = '~/photo/qrcode'
mask = 'http://qr.fiam.it/?code=%s'
extension = 'png'

class ProductProductImage(osv.osv):
    ''' Add extra function and fields for manage picture for product
    '''
    _inherit = 'product.product'        
    
    # -------------------------------------------------------------------------
    #                                   Utility:
    # -------------------------------------------------------------------------
    def qrcode_code(self, code):
        code = code.upper()
        code = code.replace(' ', '_')
        return code

    def qrcode_filename(self, code):
        code = self.qrcode_code(code)
        folder_path = os.path.expanduser(root_path)
        filename = os.path.join(folder_path, code)
        return '%s.%s' % (filename, extension)

    def prepare_qr_code(self, cr, uid, ids, context=None):
        ''' Create QR code for list of product passed
        '''        
        # Parameters:        
        version = 1
        box_size = 10
        border = 4
        
        if type(ids) not in (list, tuple):
            ids = [ids]

        qr = qrcode.QRCode(
            version=version,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=box_size,
            border=border,
            )
            
        for product in self.browse(cr, uid, ids, context=context):
            default_code = product.default_code
            code = self.qrcode_code(default_code)
            filename = self.qrcode_filename(default_code)
                        
            qr.add_data(mask % code)
            qr.make(fit=True)
            img = qr.make_image()
            img.save(filename)
        
    def get_image_qrcode(self, cr, uid, ids, context=None):
        ''' Get (or create before QR code image)
        '''
        if type(ids) not in (list, tuple):
            ids = [ids]

        img = ''
                
        for product in self.browse(cr, uid, ids, context=context):
            filename = self.qrcode_filename(product.default_code)
            if not os.path.isfile(filename):
                self.prepare_qr_code(cr, uid, product.id, context=context)
                 
            try:
                (qrcode, header) = urllib.urlretrieve(filename)
                f = open(qrcode , 'rb')
                img = base64.encodestring(f.read())
                f.close()
            except:
                img = ''
            # TODO manage error on open recreate?    
            #if not img:
            #    #create QR Code:    
            #    pass

        return img

    def _get_image_qrcode_field(self, cr, uid, ids, field_name, arg, 
            context=None):
        res = {}
        for item_id in ids:
            res[item_id] = self.get_image_qrcode(
                cr, uid, item_id, context=context)
        return res

    _columns = {
        'weblink_qrcode': fields.function(_get_image_qrcode_field, 
            type='binary', method=True),
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
