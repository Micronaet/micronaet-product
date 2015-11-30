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

    def _get_user_lang(self, cr, uid, context=None):
        ''' Get user language
        '''
        try:
            lang_code = self.pool.get('res.users').browse(
                cr, uid, uid, context=context).lang
            return self.pool.get('res.lang').search(cr, uid, [
                ('code', '=', lang_code)], context=context)[0]
        except:
            return 1
        
    _columns = {
        'column': fields.integer('Column #', required=True),
        'description': fields.char('Description', size=80),

        'from_line': fields.integer('From line'), 
        'max_line': fields.integer('Max line'),
        'lang_id': fields.many2one('res.lang', 'Language', required=True),
        'field': fields.selection([
            ('default_code', 'Product code (key field)'), # Key field
            ('description_sale', 'Sale description'), # Lang
            
            ('default_supplier_code', 'Purchase product code'),
            ('description_purchase', 'Purchase description'), # Lang

            #('colour_code', 'Color'),
            ('colour', 'Color'),
            ('fabric', 'Pillow / Glass'),

            ('length', 'Length'),
            ('width', 'Width'),
            ('height', 'Height'),
            # Weight?
            
            ('volume', 'Volume'),
            ('pack', 'Package'),
            ('item_per_box', 'Item x pack'),
           
            ('package_type', 'Package type'),
            ('pack_l', 'Package length'),
            ('pack_p', 'Package width'),
            ('pack_h', 'Package height'),

            ('lst_price', 'Sale price (* exchange = company curr.)'),
            ('standard_price', 'Cost price (* exchange = company curr.)'),

            # Needed ?!?!:
            #('usd_lst_price', 'List price (USD)'),
            #('usd_standard_price', 'Standard (USD)'),
            
            # Not used now:
            ('weight', 'Weight'),
            ('weight_net', 'Weight net'),
            
            ], 'Field linked'),
        'trace_id': fields.many2one('product.product.importation.trace',
            'Trace', ondelete='cascade'),
        }
        
    _defaults = {
        'lang_id': lambda s, cr, uid, ctx: s._get_user_lang(cr, uid, ctx),
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
    _order = 'datetime desc'

    # Button event:
    def open_product_tree(self, cr, uid, ids, context=None):
        ''' Open list product for importation selected
        '''
        log_proxy = self.browse(cr, uid, ids, context=context)[0]
        item_ids = [item.id for item in log_proxy.product_ids]
        return {        
            'type': 'ir.actions.act_window',
            'name': 'Product ',
            'res_model': 'product.product',
            'res_id': item_ids,
            'domain': [('id', 'in', item_ids)],
            'view_type': 'form',
            'view_mode': 'tree,form',
            #'view_id': view_id, # product.product_product_tree_view
            #'target': 'new',
            #'nodestroy': True,
        }
        
    _columns = {
        # No required is automated:
        'name': fields.char('Log description', size=80),
        'datetime': fields.datetime('Import date'),
        'user_id': fields.many2one('res.users', 'User'),
        'partner_id': fields.many2one('res.partner', 'Supplier'),
        'trace_id': fields.many2one('product.product.importation.trace',
            'Trace', ondelete='set null'),
        'note': fields.char('Note'),
        'error': fields.char('Error'),
        'exchange': fields.float('Exchange', digits=(16, 3)), 
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
            'Log import', ondelete='set null'),
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
