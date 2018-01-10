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

class ProductTemplate(orm.Model):
    """ Model name: Product template
    """
    
    _inherit = 'product.template'

    def _field_last_supplier_data(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Update last supplier field
        '''
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = False
            max_date = False
            for seller in product.seller_ids:
                for price in seller.pricelist_ids:
                    if not price.is_active:
                        continue
                    if not max_date or (
                            price.date_quotation and \
                            price.date_quotation > max_date):

                        # This is the last record:
                        res[product.id] = seller.name.id
                        max_date = price.date_quotation
        return res
        
    # -------------------------------------------------------------------------
    # Store function:
    # -------------------------------------------------------------------------
    def _store_last_supplier_data(self, cr, uid, ids, context=None):
        ''' Change supplierinfo data
        '''
        _logger.warning('Change name, product_tmpl_id product.supplierinfo')
        template_ids = []
        for supp in self.browse(cr, uid, ids, context=context):
            template_ids.append(supp.product_tmpl_id.id)            
        return template_ids

    def _store_last_pricelist_data(self, cr, uid, ids, context=None):
        ''' Change supplierinfo data
        '''
        _logger.warning('Change date_quotation pricelist.priceinfo')
        template_pool = self.pool.get('product.template')

        # Change date get suppinfo list:
        template_ids = []        
        for pl in self.browse(cr, uid, ids, context=context):
            template_ids.append(pl.suppinfo_id.product_tmpl_id.id)
        return template_ids
            
            
    _last_supplier_store = {
        'product.supplierinfo': (
            _store_last_supplier_data, ['name', 'product_tmpl_id'], 10),
        'pricelist.partnerinfo': (
            _store_last_pricelist_data, ['date_quotation'], 10),
        }
        
    _columns = {
        'recent_supplier_id': fields.function(
            _field_last_supplier_data, method=True, 
            type='many2one', relation='res.partner', 
            string='Recente fornitura di', 
            store=_last_supplier_store, 
            ),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
