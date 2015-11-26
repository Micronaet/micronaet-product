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

class ProductProductImportationTrace(orm.Model):
    ''' Importation log element trace of fields
    ''' 
    _name = 'product.product.importation.trace'
    _description = 'File trace'

    _columns = {
        'name': fields.char('Record trace', size=80, required=True),
        'filename': fields.char('Default filename', size=80),
        'format': fields.selection([
            ('xls', 'XLS (old file)'),
            ], 'format'),            
        'note': fields.char('Note'),
        }

    _defaults = {
        'format': lambda *x: 'xls',
        }

class ProductProductImportationTraceColumn(orm.Model):
    ''' Importation log element trace of fields
    ''' 
    _name = 'product.product.importation.trace.column'
    _description = 'Columns to import'
    _order = 'column'

    _columns = {
        'column': fields.integer('Column #', required=True),
        'description': fields.char('Description', size=80),

        'from_line': fields.integer('From line'), 
        'max_line': fields.integer('Max line'),

        'field': fields.selection([
            ('default_code', 'Product code'),
            ('name', 'Product name'),
            ('eng_name', 'Product name (eng.)'),

            ('supplier_code', 'Supplier product code'),
            ('supplier_name', 'Supplier product name'),

            ('color', 'Color'),
            ('glass', 'Pillow / Glass'),

            ('l', 'Length'),
            ('w', 'Weight'),
            ('h', 'Height'),
            
            ('volume', 'Volume'),
            ('pack', 'Package'),
            ('pack_item', 'Itam /pack'),
           
            ('pack_l', 'Package length'),
            ('pack_w', 'Package weight'),
            ('pack_h', 'Package height'),

            ('lst_price', 'List price (EUR)'),
            ('standard_price', 'Standard (EUR)'),

            ('usd_lst_price', 'List price (USD)'),
            ('usd_standard_price', 'Standard (USD)'),
            ], 'Field linked'),
        'trace_id': fields.many2one('product.product.importation.trace',
            'Trace', ondelete='cascade'),
        }

class ProductProductImportationTrace(orm.Model):
    ''' Importation log element trace of fields
    ''' 
    _inherit = 'product.product.importation.trace'

    _columns = {
        'column_ids': fields.one2many('product.product.importation.trace.column', 
            'trace_id', 'Columns'),
        }

class ProductProductImportation(orm.Model):
    ''' Importation log element
    ''' 
    _name = 'product.product.importation'
    _description = 'Importation log'

    # Button event:
    def open_product_tree(self, cr, uid, ids, context=None):
        ''' Open list product for importation selected
        '''
        # TODO 
        return {}
        
    _columns = {
        'name': fields.char('Log description', size=80, required=True),
        'datetime': fields.date('Import date', required=True),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'trace_id': fields.many2one('product.product.importation.trace',
            'Trace', ondelete='set null'),
        'note': fields.char('Note'),
        }

    _defaults = {
        'datetime': lambda *x: datetime.now(),
        'user_id': lambda s, cr, uid, ctx: uid,
        }

class ProductProduct(orm.Model):
    ''' Product for link import log
    '''    
    _inherit = 'product.product'
    
    _columns = {
        'csv_import_id': fields.many2one('product.product.importation',
            'Log import'),
        }

class ProductProductImportation(orm.Model):
    ''' Importation log element
    ''' 
    _inherit = 'product.product.importation'

    _columns = {
        'product_ids': fields.one2many('product.product', 
            'csv_import_id', 'Products'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
