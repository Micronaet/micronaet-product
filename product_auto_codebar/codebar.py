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


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """
    _name = 'product.codebar.exclude'
    _description = 'Code excluded'
        
    # Onchange function:
    def onchange_exclude_name(self, cr, uid, ids, name, context=None):
        res = {}
        if len(name) != 5:
            res['warning'] = {
                'title': 'Wrong format',
                'message': 'Exclude format must be: 00001 (only code part)',
                }

        try:
            if int(name) <= 0:
                res['warning'] = {
                    'title': 'Wrong format',
                    'message': 'Exclude format must be int number',
                    }
        except:
            res['warning'] = {
                'title': 'Wrong format',
                'message': 'Error checking format',
                }            
            
        return res
        
    _columns = {
        'name': fields.char('Exclude', size=5, required=True,
            help='Only code part, ex: 67890 for 8012345678901'), 
        # calculated part for EAN    
        }

class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """
    _inherit = 'product.product'

    def create(self, cr, uid, vals, context=None):
        """ Create a new record for a model ClassName
            @param cr: cursor to database
            @param uid: id of current user
            @param vals: provides a data for new record
            @param context: context arguments, like lang, time zone
            
            @return: returns a id of new record
        """
        if vals.get('ean13_auto', False) and not vals.get('ean13', False):
            # Generate if not present and checked auto boolean:
            vals['ean13'] = self._get_ean13_auto(cr, uid, context=context)
        vals['ean13_auto'] = False
            
        return super(ProductProduct, self).create(
            cr, uid, vals, context=context)
    
    # Utility button:
    def _get_ean13_auto(self, cr, uid, context=None):
        ''' Get an EAN 13 code 
        '''
        def generate_code(value):
            ''' Add extra char
            '''
            import barcode
            EAN = barcode.get_barcode_class('ean13')
            if len(value) != 12:
                raise osv.except_osv(
                    _('Error'),
                    _('EAN before control must be 12 char!'))
            ean13 = EAN(value)
            return ean13.get_fullcode()

        # Pool used:
        exclude_pool = self.pool.get('product.codebar.exclude')

        company_pool = self.pool.get('res.company')
        company_ids = company_pool.search(cr, uid, [], context=context)
        company_proxy = company_pool.browse(
            cr, uid, company_ids, context=context)[0]
        fixed = company_proxy.codebar_fixed
        if not fixed or len(fixed) != 7:
            raise osv.except_osv(
                _('Error'), 
                _('Setup fixed part in company form (must be 7 char)'))
                
        # Load list of ean code yet present and black list
        product_ids = self.search(
            cr, uid, [('ean13_product', '!=', False)], context=context)
        black_list = [item.ean13_product for item in self.browse(
            cr, uid, product_ids, context=context)]
            
        exclude_ids = exclude_pool.search(cr, uid, [], context=context)
        exclude_proxy = exclude_pool.browse(
            cr, uid, exclude_ids, context=context)
        black_list.extend([item.name for item in exclude_proxy])
        for i in range(1, 10000):
            code = '%05d' % i
            if code not in black_list:
                return generate_code('%s%s' % (fixed, code))
        return ''
    
    # Button events:    
    def generate_barcode_ean13(self, cr, uid, ids, context=None):
        ''' Create EAN code, not duplicated and not in exclude list
        '''            
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        if current_proxy.ean13:
            raise osv.except_osv(
                _('Error'), 
                _('EAN yet present, delete and press button again'))
        
        ean13 = self._get_ean13_auto(cr, uid, context=context)
        if ean13:
            return self.write(cr, uid, ids, {
                'ean13': ean13, }, context=context)        
        return True

    # -------------------------------------------------------------------------
    #                        Fields function:
    # -------------------------------------------------------------------------
    # Field function:
    def _get_part_ean_code(self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            if item.ean13:
                res[item.id] = item.ean13[7:12]
            else:
                res[item.id] = ''                
        return res

    # Store function:
    def _get_product_ean_changed(self, cr, uid, ids, context=None):
        ''' Return changed product (store function
        '''
        return ids

    _columns = {
        'ean13_auto': fields.boolean('Auto EAN'),
        'ean13_product': fields.function(
            _get_part_ean_code, method=True, 
            type='char', string='EAN13 product part', 
            store={
                'product.product': (_get_product_ean_changed, ['ean13'], 10),
                }),                        
        }
        
    _defaults = {
        'ean13_auto': lambda *x: True,
        }    
        
class ResCompany(orm.Model):
    """ Model name: Company
    """
    _inherit = 'res.company'

    _columns = {
        'codebar_fixed': fields.char('Codebar fixed', size=7, 
            help='Fixed part, ex: 8012345 for 8012345678901'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
