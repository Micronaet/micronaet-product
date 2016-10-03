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

class ProductDutySet(orm.Model):
    """ Model name: ProductDutySet
    """
    
    _name = 'product.duty.set'
    _description = 'Duty for set'
    _rec_name = 'duty_id'
    _order = 'duty_id'

    # Function field:
    def _get_partal_total_duty_set(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Fields function for calculate 
        '''    
        res = {}
        total = sum([duty.partial_value for duty in self.browse(
            cr, uid, ids, context=context)])
        for duty in self.browse(cr, uid, ids, context=context):
            if total:
                res[duty.id] = \
                    duty.partial_value / total * 100.0
            else:
                res[duty.id] = 0.0 # error!            
        return res
        
    _columns = {
        'product_id': fields.many2one(
            'product.product', 'Product'),
        'duty_id': fields.many2one(
            'product.custom.duty', 'Duty', 
            required=True),
        'partial': fields.function(
            _get_partal_total_duty_set, method=True, 
            type='float', string='Partial %', 
            store=False, readonly=True), 
                        
        'partial_value': fields.float('Partial value', 
            digits=(16, 2), required=True,
            help='Duty part for this category'),
        'note': fields.text('Note'),
            
        # Set management for compoment: TODO    
        #'component_id': fields.many2one(
        #    'product.product', 'Component'),
        #'total': fields.integer('Total'),    
        }

class ProductProduct(orm.Model):
    """ Model name: Product product
    """
    
    _inherit = 'product.product'
    
    # Function field:
    def _get_partal_total_duty_set(self, cr, uid, ids, fields, args, 
            context=None):
        ''' Fields function for calculate 
        '''    
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = sum([
                duty.partial_value for duty in product.duty_set_ids])
        return res
        
    _columns = {
        'is_duty_set': fields.boolean('Is duty set'),
        'duty_set_ids': fields.one2many(
            'product.duty.set', 'product_id', 'Duty for set'),
        'duty_set_reference': fields.function(
            _get_partal_total_duty_set, method=True, 
            type='float', string='Total value for set', 
            help='Total of single part in this list, used for perc calc.',
            store=False, readonly=True), 
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
