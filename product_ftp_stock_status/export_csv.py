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
import xlsxwriter
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
    ''' Model name: Product 
    '''    
    _inherit = 'product.product'
    
    # -------------------------------------------------------------------------
    # Scheduled action:
    # -------------------------------------------------------------------------
    def export_csv_stock_status_via_ftp_file(self, cr, uid, context=None):
        ''' Export and launch FTP publish
        '''        
        # ---------------------------------------------------------------------
        # CSV file:
        # ---------------------------------------------------------------------
        csv_file = '/home/administrator/photo/xls/ftp/product.csv'
        sh_file = '/home/administrator/photo/xls/ftp/publish.sh'
        
        _logger.warning('Start generate CSV stock status: %s' % csv_file)

        ftp_file = open(csv_file, 'r')
                
        # ---------------------------------------------------------------------
        # Start export product:
        # ---------------------------------------------------------------------
        product_pool = self.pool.get('product.product')
        product_ids = product_pool.search(cr, uid, [
            #('statistic_category', 'in', (
            #    'I01', 'I02', 'I03', 'I04', 'I05', 'I06')),
            ], context=context)
            
        for product in product_pool.browse(
                cr, uid, product_ids, context=context):
            ftp_file.write('%s;%s;%s\n' % (
                product.default_code,
                product.mx_net_qty,
                product.mx_lord_qty,
                product.lst_price,
                )
        ftp_file.close()                
        
        # ---------------------------------------------------------------------
        # FTP publish
        # ---------------------------------------------------------------------
        _logger.warning('Publish file: %s [script: %s]' % (
            csv_file,
            sh_file,
            ))            
        os.system(sh_file)
        _logger.warning('End publish FTP stock status')
        return True
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
