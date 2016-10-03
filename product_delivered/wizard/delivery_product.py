# -*- coding: utf-8 -*-
###############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
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

class ProductProductMovedWizard(orm.TransientModel):
    ''' Procurements depend on sale
    '''    
    _name = 'product.product.moved.wizard'
    _description = 'Product moved'
    
    # -------
    # Utilty:
    # -------
    def get_domain_moves_from_wizard(self, cr, uid, wiz_proxy, context=None):
        ''' Utility used to create domain from wizard selection and report
        '''
        # Pool used:
        picking_pool = self.pool.get('stock.picking')

        domain = []
        domain.append(('picking_type_id', '=', wiz_proxy.type_id.id))
        if wiz_proxy.from_date:
            domain.append(('date', '>=', '%s 00:00:00' % wiz_proxy.from_date))
        if wiz_proxy.to_date:
            domain.append(('date', '<=', '%s 23:59:59' % wiz_proxy.to_date))
        pick_ids = picking_pool.search(cr, uid, domain, context=context)

        domain_move = [('picking_id', 'in', pick_ids)]
        if wiz_proxy.code:
            domain_move.append(
                ('product_id.default_code', 'ilike', wiz_proxy.code))
        if wiz_proxy.start_code:
            domain_move.append(
                ('product_id.default_code', '=like', '%s%s' % (
                    wiz_proxy.start_code, '%')))
        return domain_move            

    # --------------
    # Button events:
    # --------------        
    def open_move_report(self, cr, uid, ids, context=None):
        ''' 
        '''    
        move_pool = self.pool.get('stock.move')

        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        domain = self.get_domain_moves_from_wizard(
            cr, uid, wiz_proxy, context=context)
                    
        datas = {
            'domain': domain,
            'report_code_break': wiz_proxy.report_code_break,
            'report_detailed': wiz_proxy.report_detailed,
            }
            
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'delivered_status_report',
            'datas': datas,
            }
                    
    def open_move(self, cr, uid, ids, context=None):
        ''' Open moved from pick
        ''' 
        move_pool = self.pool.get('stock.move')
        
        wiz_proxy = self.browse(cr, uid, ids, context=context)[0]
        domain = self.get_domain_moves_from_wizard(
            cr, uid, wiz_proxy, context=context)
        move_ids = move_pool.search(cr, uid, domain, context=context)
        
        # Search view and open:
        model_pool = self.pool.get('ir.model.data')
        try:
            tree_view = model_pool.get_object_reference(
                cr, uid, 'product_delivered', 
                'view_stock_move_packed_form')[1]
        except:
            tree_view = False        
        try:
            # DOESN'T WORK!!!
            search_view = model_pool.get_object_reference(
                cr, uid, 'product_delivered', 
                'product_product_search_view')[1]
        except:
            search_view = False

        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock move status',
            'res_model': 'stock.move',
            'view_type': 'form',
            'view_mode': 'tree',
            'search_view_id': search_view,
            'views': [
                (tree_view or False, 'tree'), 
                #(search_view or False, 'search'), 
                ],
            'domain': [('id', 'in', move_ids)],
            'context': {'search_default_product_group': True},
            }

    _columns = {
        'from_date': fields.date('From >=', help='Date >='),
        'to_date': fields.date('To <=', help='Date <='),
        'code': fields.char('Code', size=24), 
        'start_code': fields.char('Start code', size=24), 
        'type_id': fields.many2one(
            'stock.picking.type', 'Picking type', required=True), 
        
        # Report fields:    
        'report_detailed': fields.boolean('Report detailed'),    
        'report_code_break': fields.integer('Code break', required=True,
            help='Break and write total when product change x char of code'), 
        }
    
    _defaults = {
        'report_detailed': lambda *x: True,
        'report_code_break': lambda *x: 6,
        }    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
