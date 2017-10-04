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

class ProductProductPriceRule(orm.Model):
    """ Model name: ProductProductPriceRule
    """
    
    _name = 'product.product.price.rule'
    _description = 'Price rule'
    _order = 'name'
    
    # Utility:
    def get_list_with_this_rule(self, cr, uid, ids, context=None):
        ''' Utility for generate list of product selected with current rule
        '''
        where = ''
        for rule in sorted(self.browse(cr, uid, ids, context=context), 
                key=lambda r: (-len(rule.name), name)):
            where += '%s%s' % (
                ' or ' if where else '',
                'default_code ilike \'%s\'' % line.name
                )

        if not where:
            raise osv.except_osv(
                _('Error!'), _('No product with the mask selected!'), )
                    
        cr.execute('SELECT distinct id FROM product_product WHERE %s' % where)
        product_ids = [item[0] for item in cr.fetchall()]        

        if not product_ids:
            raise osv.except_osv(
                _('Error!'), _('No product with mask selected!'), )
        return product_ids
    
    def force_product_list(self, cr, uid, ids, context=None):
        ''' Force price with product mask
        '''
        return True

    def get_product_list(self, cr, uid, ids, context=None):
        ''' Get selection list:
        '''
        #current_proxy
        #product_ids = self.get_list_with_this_rule(
        #    cr, uid, ids, context=context)
        #return self.write(cr, uid, 
        return True

    def product_use_this_mask(self, cr, uid, ids, context=None):
        ''' Check product that work with this rule
        '''
        rule_proxy = self.browse(cr, uid, ids, context=context)[0]
        where = 'default_code ilike \'%s\'' % rule_proxy.name

        cr.execute('SELECT distinct id FROM product_product WHERE %s' % where)
        product_ids = [item[0] for item in cr.fetchall()]        

        if not product_ids:
            raise osv.except_osv(
                _('Error!'), _('No product with mask selected!'), )
             
        return {
            'type': 'ir.actions.act_window',
            'name': _('Product with rule'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'product.product',
            #'view_id': tree_view_id,
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('id', 'in', product_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }
    
    _columns = {        
        'name': fields.char(
            'Rule mask', size=64, required=True, 
            help='''Product mask, use _ for replace char % for no care, ex.
                127_X%  >>> 172OX1  127AX34  etc.
                '''),
        'price': fields.float('Price', digits=(16, 3), required=True),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
