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

class ProductMultiPackaging(orm.Model):
    ''' Object for manage multi pack in product
    '''
    _name = 'product.multi.packaging'
    _description = 'Multi packaging'
    _rec_name = 'sequence'
    _order = 'sequence'

    # On change event:
    def onchange_ul_multidimension(self, cr, uid, ids, ul, context=None):
        ''' Load dimension from ul
        '''
        ul_pool = self.pool.get('product.ul')
        res = {}
        if not ul:
           return 
        ul_proxy = ul_pool.browse(cr, uid, ul, context=context)
        res['value'] = {
            'length': ul_proxy.length,
            'height': ul_proxy.height,
            'width': ul_proxy.width,            
            }
        return res           
           
    # Button event:
    def load_from_multipack(self, cr, uid, ids, context=None):
        ''' Load pack measure from box
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        current_proxy = self.browse(cr, uid, ids, context=context)[0]
        return self.write(cr, uid, ids, {
            'length': current_proxy.ul.length,
            'height': current_proxy.ul.height,
            'width': current_proxy.ul.width,
            }, context=context)
    
    _columns = {
        'sequence': fields.integer('Seq.', 
            help='Sequence order when displaying a list of packaging.'),
        'name': fields.char('Description', size=80),
        'number': fields.integer('Tot.',
            help='The total number of this package.'),
        'ul_id': fields.many2one('product.ul', 'Package', 
            required=True),
        #'product_tmpl_id': fields.many2one('product.template', 
        #    'Product', select=1, ondelete='cascade'),
        'product_id': fields.many2one('product.template', 
            'Product', select=1, ondelete='cascade'),
        #'ean': fields.char('EAN', size=14, 
        #    help='The EAN code of the package unit.'),
        'code': fields.char('Code', 
            help='The code of the transport unit.'),

        'height': fields.float('Height', help='Height of the pack'),
        'width': fields.float('Width', help='Width of the pack'),
        'length': fields.float('Length', help='Length of the pack'),

        'weight': fields.float('Weight',
            help='The weight of a full package, pallet or box.'),
        }
        
    _defaults = {
        'number': lambda *x: 1,
        }    

class ProductTemplate(orm.Model):
    ''' Add relation fields
    '''
    _inherit = 'product.template'
    
    _columns = {
        'has_multipackage': fields.boolean('Has multipackage', 
            help='If product has multipackage not use pack variant mode'),
        'multi_pack_ids': fields.one2many(
            'product.multi.packaging', 'product_id', 'Multipack',
            help='Multipack for package one item'),
        'multipack_dimension': fields.text('Multipack dimension'),
        # TODO colls in product? > campo function
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
