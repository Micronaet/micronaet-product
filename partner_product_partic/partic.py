# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID#, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)

_logger = logging.getLogger(__name__)


class ResPartnerProductPartic(osv.osv):
    ''' Add product partic obj
    '''    
    _inherit = 'res.partner.product.partic'

    # -------------------------------------------------------------------------
    #                                 Columns
    # -------------------------------------------------------------------------
    _columns = {
        'partner_code': fields.char('Partner code', size=40), 
        'partner_description': fields.char('Partner description', size=60,
            help='Description in partner\'s language'
            ),
        'partner_price': fields.float('Price', 
            digits_compute=dp.get_precision('Product Price')),     
        'price_from_date': fields.date('From date'),
        'price_to_date': fields.date('To date'),    
        }

class SaleOrderLine(orm.Model):
    """ Model name: SaleOrderLine
    """
    _inherit = 'sale.order.line'
    
    # override onchange product for check before in partner partic
    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product, 
            qty=0, uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, 
            fiscal_position=False, flag=False, warehouse_id=False, 
            context=None):
            
        # Change original function:    
        res = super(SaleOrderLine, self).product_id_change_with_wh(
            cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, 
            partner_id=partner_id, lang=lang, update_tax=update_tax, 
            date_order=date_order, packaging=packaging, 
            fiscal_position=fiscal_position, flag=flag, 
            warehouse_id=warehouse_id, context=context)
        # TODO check parent also in pricelist (not for now!!)    
            
        # Check if there's partner-product partic
        if product and partner_id:
            # -----------------------------------------------------------------    
            # Search in customer-product partic:
            # -----------------------------------------------------------------    
            partic_pool = self.pool.get('res.partner.product.partic')
            partic_ids = partic_pool.search(cr, uid, [
                ('partner_id', '=', partner_id),
                ('product_id', '=', product),
                ('partner_price', '>', 0),
                ], context=context)
                
            # -----------------------------------------------------------------    
            # Try to check with parent code if present for this company:    
            # -----------------------------------------------------------------    
            if not partic_ids:
                # Try parent code:
                product_pool = self.pool.get('product.product')
                product_proxy = product_pool.browse(
                    cr, uid, product, context=context)
                parent_code =  product_proxy.company_id.partic_parent_len or 0
                if parent_code and product_proxy.default_code:
                    default_code = product_proxy.default_code[0:parent_code]                
                    product_ids = product_pool.search(cr, uid, [
                        ('default_code', '=', default_code)], context=context)
                    if product_ids:
                        if len(product_ids) > 1:
                            _logger.warning('More than one: %s' % default_code)
                        partic_ids = partic_pool.search(cr, uid, [
                            ('partner_id', '=', partner_id),
                            ('product_id', '=', product_ids[0]),
                            ('partner_price', '>', 0),
                            ], context=context)
                            
            # -----------------------------------------------------------------
            # Get price (product or parent):
            # -----------------------------------------------------------------
            if partic_ids:
                partic_proxy = partic_pool.browse(
                    cr, uid, partic_ids, context=context)[0]   
                if 'value' not in res:
                    res['value'] = {}
                res['value']['price_unit'] = partic_proxy.partner_price
        return res
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
