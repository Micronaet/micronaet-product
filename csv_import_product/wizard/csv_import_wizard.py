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
import xlrd
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

class ProductProductCsvImportWizard(orm.TransientModel):
    ''' Wizard to import CSV product updating price
    '''    
    _name = 'product.product.csv.import.wizard'

    # ---------------
    # Utility funtion
    # ---------------
    def preserve_window(self, cr, uid, ids, context=None):
        ''' Create action for return the same open wizard window
        '''
        view_id = self.pool.get('ir.ui.view').search(cr,uid,[
            ('model', '=', 'product.product.csv.import.wizard'),
            ('name', '=', 'Create production order') # TODO needed?
            ], context=context)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Wizard create production order',
            'res_model': 'mrp.production.create.wizard',
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'target': 'new',
            'nodestroy': True,
            }

    # --------------
    # Wizard button:
    # --------------
    def action_import_csv(self, cr, uid, ids, context=None):
        ''' Import pricelist and product description
        '''
        # TODO:
        filename = '/home/administrator/photo/xls'
        _logger.info('Start import from path: %s' % filename)
        
        context = context or {}        
        current_lang = context.get('lang', 'it_IT')   

        # Pool used:
        product_pool = self.pool.get('product.product')
        log_pool = self.pool.get('log.importation')
        column_pool = self.pool.get('product.product.importation.trace.column')

        # Wizard proxy:
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        _logger.info('Start import XLS product file: %s' % wiz_proxy.name)
        from_line = wiz_proxy.from_line # 14
        to_line = wiz_proxy.to_line #24
        with_new = wiz_proxy.with_new
        cost_id = wiz_proxy.cost_id.id
        revenue_id = wiz_proxy.revenue_id.id
        
        filename = os.path.join(filename, wiz_proxy.name)        
        error = ''
        annotation = ''
        
        # Return view:
        log_view = {
            'type': 'ir.actions.act_window',
            'name': 'Log import',
            'res_model': 'log.importation',
            'view_type': 'form',
            'view_mode': 'form,tree',
            #'view_id': view_id,
            #'target': 'new',
            #'nodestroy': True,            
            }

        # Load trace:
        column_trace = {}
        lang_trace = []
        key_field = ['default_code']

        for item in wiz_proxy.trace_id.column_ids:
            column_trace[item.name] = item #.field
            if item.lang_id.code not in lang_trace:
                lang_trace.append(item.lang_id.code)
        
        # ---------------------------------------------------------------------
        #                Open XLS document (first WS):
        # ---------------------------------------------------------------------
        try:
            # from xlrd.sheet import ctype_text   
            wb = xlrd.open_workbook(filename)
            ws = wb.sheet_by_index(0)
        except:
            error = 'Error opening XLS file: %s' % (sys.exc_info(), )

        # Create import log for this import:
        partner_id = wiz_proxy.partner_id.id or False
        exchange = wiz_proxy.exchange or 1.0
        log_id = log_pool.create(cr, uid, {
            'name': wiz_proxy.comment or 'No comment',
            'trace_id': wiz_proxy.trace_id.id,
            'partner_id': partner_id,
            'exchange': exchange,
            'error': error,
            # Extra info write at the end
            }, context=context)
        log_view['res_id'] = log_id    
        
        if error:
            return log_view

        from_line -= 1 # Start from 0 (different from line number)
        for i in range(from_line, to_line or 10000):
            #  Prepare new record:
            data = {}
            for lang in lang_trace:
                data[lang] = {}                
            try:
                row = ws.row(i)                
            except:
                # Out of range error ends import:
                annotation += _('Import end at line: %s\n') % i
                break
            try:
                # Loop on colums (trace)                
                default_code = False
                for col, field in column_trace.iteritems():
                    try:        
                        v = row[col - 1].value
                    except: 
                        error += _(
                            '''%s. Col %s, field <b>%s</b>, not present!</br>
                            ''') % (i, col, field.field)
                        continue        
                        
                    # ---------------------------------------------------------    
                    #       Default_code:
                    # ---------------------------------------------------------    
                    if field.field == 'default_code': # key:
                        default_code = v
                    
                    # ---------------------------------------------------------    
                    #       Float field or exchange field (so float):    
                    # ---------------------------------------------------------    
                    elif field.field in column_pool.get_float_list() or \
                            field.need_exchange:
                        f = v or 0.0
                        if type(f) not in (float, int) :
                            f = float(f.replace(',', '.'))
                            
                        data[field.lang_id.code][field.field] = f
                    # ---------------------------------------------------------                        
                    #       String elements:
                    # ---------------------------------------------------------    
                    else: 
                        data[field.lang_id.code][field.field] = v
                            
                    if field.need_exchange:
                        data[field.lang_id.code][
                            field.field] *= exchange

                # Search product with code:
                if not default_code:
                    error += _(
                        'Error no code present in line: <b>%s</b></br>') % i
                    continue

                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)], context=context)

                if product_ids:
                    product_id = product_ids[0]
                    if len(product_ids) > 1:
                        error += _(
                            '''%s. Error more code (take first), 
                                code: <b>%s</b></br>''') % (
                                    i, default_code)
                else:                
                    if not with_new:
                        error += _(
                            '%s. Error code not found, code: <b>%s</b></br>'
                            ) % (i, default_code)                                
                        continue   

                    # Create product:
                    _logger.info('Create product code: %s' % default_code)            
                    product_id = product_pool.create(cr, uid, {
                        'name': default_code, # will be update after
                        'default_code': default_code,
                        'type': 'product',
                        'property_account_income': revenue_id, 
                        'property_account_expense': cost_id,
                        #'categ_id'
                        # taxes_id
                        # supplier_taxes_id
                        # uom_id product.uom                        
                        }, context=context)

                # Write product in lang:
                for lang in lang_trace:
                    context['lang'] = lang
                    if data[lang]: # else no write operation:
                        # Add fixed field (always present):
                        data[lang]['csv_import_id'] = log_id # link to log event
                        if partner_id: 
                            data[lang]['first_supplier_id'] = partner_id
                        
                        product_pool.write(
                            cr, uid, product_id, data[lang], 
                            context=context)
                _logger.info('Update product code: %s' % default_code)            
            except:
                error += _('%s. Import error code: <b>%s</b> [%s]</br>') % (
                    i, default_code, sys.exc_info())

        # End operations:    
        context['lang'] = current_lang
        # Update lof with extra information:    
        log_pool.write(cr, uid, log_id, {
            'error': error,
            'note': '''
                File: <b>%s</b></br>
                Import note: <i>%s</i></br>
                Operator note:</br><i>%s</i>
                ''' % (
                    wiz_proxy.name, 
                    annotation, 
                    wiz_proxy.note or ''),
            }, context=context)

        _logger.info('End import XLS product file: %s' % wiz_proxy.name)
        return log_view
        
    _columns = {
        'name': fields.char('File name', size=80, required=True),
        'comment': fields.char('Log comment', size=80, required=False),
        'from_line': fields.integer('From line >=', required=True), 
        'to_line': fields.integer('To line <='),#, required=True), 
        'exchange': fields.float('Exchange', digits=(16, 3), required=True), 
        'trace_id': fields.many2one('product.product.importation.trace',
            'Trace', required=True),
        'partner_id': fields.many2one('res.partner', 'Supplier'),
        'price_force': fields.selection([
            ('product', 'Direct in product'),
            ('pricelist', 'Create Pricelist'),
            ], 'Force price'),            
        'with_new': fields.boolean('Create product'),
        'cost_id': fields.many2one('account.account', 'Cost'),
        'revenue_id': fields.many2one('account.account', 'Revenue'), 
        # taxes_id cost
        # taxes_id revenue
        # uom
        
        # TODO extra fields for new:
        'note': fields.text('Note'),
        }
        
    _defaults = {
        'from_line': lambda *x: 1,
        'price_force': lambda *x: 'product',
        'exchange': lambda *x: 1.0,
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
