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
    _name = 'product.codebar.unused'
    _description = 'Code unused'
    _order = 'name'
    
    def burn_ean13_code(self, cr, uid, ean13, partial=False, context=None):
        ''' Remove code fron unused list
            partial if is the article part
        '''
        if not ean13:
            _logger.error('No passed ean to burn!')
            return False
            
        if partial:
            domain = [('name', '=ilike', '_______%s_' % ean13)]
        else:
            domain = [('name', '=', ean13)]   
        item_ids = self.search(cr, uid, domain, context=context)
        if item_ids:
            try:
                return self.unlink(cr, uid, item_ids, context=context)
            except:
                return False
        else:
            _logger.warning('Cannot burn EAN (not in unused list): %s' % ean13)
            return True    
        
    def get_ean13(self, cr, uid, context=None):
        ''' Pop the number form database
        '''
        ean_ids = self.search(cr, uid, [], context=context)
        if ean_ids:
            # Read and delete key:
            ean13 = self.browse(cr, uid, ean_ids, context=context)[0].name
            self.unlink(cr, uid, ean_ids[0])
            return ean13
        else:
            _logger.error('No EAN code in database!!!')
            return ''
        
    _columns = {
        'name': fields.char('Free EAN', size=13, required=True),
        }

class ProductProductExclude(orm.Model):
    """ Model name: ProductProduct
    """
    _name = 'product.codebar.exclude'
    _description = 'Code excluded'
    _order = 'name'

    def write(self, cr, uid, ids, vals, context=None):
        """ Update redord(s) comes in {ids}, with new value comes as {vals}
            return True on success, False otherwise
            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of record ids to be update
            @param vals: dict of new values to be set
            @param context: context arguments, like lang, time zone
            
            @return: True on success, False otherwise
        """    
        unused_pool = self.pool.get('product.codebar.unused')
        name = vals.get('name', False)
        if name:
            unused_pool.burn_ean13_code(cr, uid, name, partial=True,
                context=context)
        
        return super(ProductProductExclude, self).write(
            cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        """ Create a new record for a model ClassName
            @param cr: cursor to database
            @param uid: id of current user
            @param vals: provides a data for new record
            @param context: context arguments, like lang, time zone
            
            @return: returns a id of new record
        """
        unused_pool = self.pool.get('product.codebar.unused')
        name = vals.get('name', False)
        if name:
            unused_pool.burn_ean13_code(cr, uid, name, partial=True,
                context=context)

        return super(ProductProductExclude, self).create(
            cr, uid, vals, context=context)
                    
    # Onchange function:
    def onchange_exclude_name(self, cr, uid, ids, name, context=None):
        res = {}
        if not name:
            return res
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
        }
    
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The Name must be unique !'),        
        ]
    
class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """
    _inherit = 'product.product'

    def write(self, cr, uid, ids, vals, context=None):
        """ Update redord(s) comes in {ids}, with new value comes as {vals}
            return True on success, False otherwise
            @param cr: cursor to database
            @param uid: id of current user
            @param ids: list of record ids to be update
            @param vals: dict of new values to be set
            @param context: context arguments, like lang, time zone
            
            @return: True on success, False otherwise
        """    
        unused_pool = self.pool.get('product.codebar.unused')
        ean13 = vals.get('ean13', False)
        if ean13:
            unused_pool.burn_ean13_code(cr, uid, ean13, context=context)
        
        return super(ProductProduct, self).write(
            cr, uid, ids, vals, context=context)
    
    def create(self, cr, uid, vals, context=None):
        """ Create a new record for a model ClassName
            @param cr: cursor to database
            @param uid: id of current user
            @param vals: provides a data for new record
            @param context: context arguments, like lang, time zone
            
            @return: returns a id of new record
        """
        unused_pool = self.pool.get('product.codebar.unused')
        ean13 = vals.get('ean13', False)
        if ean13:
            unused_pool.burn_ean13_code(cr, uid, ean13, context=context)
            
        elif vals.get('ean13_auto', False):
            # Generate if not present and checked auto boolean:
            vals['ean13'] = unused_pool.get_ean13(cr, uid, context=context)
                
        vals['ean13_auto'] = False   
        return super(ProductProduct, self).create(
            cr, uid, vals, context=context)

    # --------------
    # Button events:    
    # --------------
    def generate_barcode_ean13(self, cr, uid, ids, context=None):
        ''' Create EAN code, not duplicated and not in exclude list
        '''            
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        if current_proxy.ean13:
            raise osv.except_osv(
                _('Error'), 
                _('EAN yet present, delete and press button again'))
        
        ean13 = self.pool.get('product.codebar.unused').get_ean13(
            cr, uid, context=context)
        if ean13:
            return self.write(cr, uid, ids, {
                'ean13': ean13,                
                }, context=context)      
        return True

    _columns = {
        'ean13_auto': fields.boolean('Auto EAN'),                  
        }
        
    _defaults = {
        'ean13_auto': lambda *x: True,
        }    
        
class ResCompany(orm.Model):
    """ Model name: Company
    """
    _inherit = 'res.company'

    def generate_whitelist_unused_code(self, cr, uid, ids, context=None):
        ''' Generate white list of unused code
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
        unused_pool = self.pool.get('product.codebar.unused')
        product_pool = self.pool.get('product.product')
        package_pool = self.pool.get('product.packaging')
        
        # ---------------------------------------------------------------------    
        # Read parameters:
        # ---------------------------------------------------------------------    
        company_ids = self.search(cr, uid, [], context=context)
        company_proxy = self.browse(
            cr, uid, company_ids, context=context)[0]
        fixed = company_proxy.codebar_fixed
        if not fixed or len(fixed) != 7:
            _logger.error('No fixed part for generate EAN!')
            return False
        
        # ---------------------------------------------------------------------    
        # Generate black list:
        # ---------------------------------------------------------------------
        black_list = []
        
        # From product code:
        product_ids = product_pool.search(cr, uid, [
            ('ean13', '=ilike', '%s%%' % fixed),
            ], context=context)
        product_proxy = product_pool.browse(
            cr, uid, product_ids, context=context)
        black_list = [p.ean13[7:12] for p in product_proxy]
        
        # From package:
        package_ids = package_pool.search(cr, uid, [
            ('ean', '=ilike', '%s%%' % fixed),
            ], context=context)
        package_proxy = package_pool.browse(
            cr, uid, package_ids, context=context)
        black_list.extend([p.ean[7:12] for p in package_proxy])
        
        # From blacklist:
        exclude_ids = exclude_pool.search(cr, uid, [], context=context)
        exclude_proxy = exclude_pool.browse(
            cr, uid, exclude_ids, context=context)
        black_list.extend([item.name for item in exclude_proxy])        
        
        # ---------------------------------------------------------------------    
        # Regenerate codes:
        # ---------------------------------------------------------------------    
        # Remove current:
        unused_ids = unused_pool.search(cr, uid, [], context=context)
        unused_pool.unlink(cr, uid, unused_ids, context=context)
        
        # Regenerate:
        for i in range(1, 100000):
            code = '%05d' % i
            if code not in black_list:
                unused_pool.create(cr, uid, {
                    'name': generate_code('%s%s' % (fixed, code)),
                    }, context=context)        
        return True

    _columns = {
        'codebar_fixed': fields.char('Codebar fixed', size=7, 
            help='Fixed part, ex: 8012345 for 8012345678901'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
