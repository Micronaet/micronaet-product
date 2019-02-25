#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
# Developer: Nicola Riolini @thebrush (<https://it.linkedin.com/in/thebrush>)
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################


import os
import sys
import logging
import openerp
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class SaleOrderLine(orm.Model):
    """ Model name: SaleOrderLine
    """
    
    _inherit = 'sale.order.line'

    def return_view_assign_wizard(self, cr, uid, ids, context=None):
        ''' Open wizard view:
        '''
        model_pool = self.pool.get('ir.model.data')
        view_id = model_pool.get_object_reference(
            cr, uid,
            'inventory_status_assign_wizard', 
            'sale_order_line_assign_stock_wizard_view')[1]

        # Check previsional order:
        line_proxy = self.browse(cr, uid, ids, context=context)[0]
        order = line_proxy.order_id
        if order.previsional:
            raise osv.except_osv(
                _('Errore'), 
                _('''Ordine previsionale, non permessa una assegnazione da 
                     magazzino in quando viene fatto per caricare il magazzino
                     '''))
        if order.state not in ('manual', 'progress'):
            raise osv.except_osv(
                _('Errore'), 
                _('''Ordine non nel corretto stato:
                     solo gli ordini attivi non chiusi possono avere 
                     assegnazioni da magazzino.
                     '''))
    
        wiz_pool = self.pool.get('sale.order.line.assign.stock.wizard')
        wiz_id = wiz_pool.create(cr, uid, {
            'line_id': ids[0],
            }, context=context)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Assegna q. magazzino'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz_id,
            'res_model': 'sale.order.line.assign.stock.wizard',
            'view_id': view_id, # False
            'views': [(view_id, 'form')],
            'domain': [],
            'context': context,
            'target': 'new',
            'nodestroy': False,
            }
            

class SaleOrderLineAssignStockWizard(orm.TransientModel):
    ''' Wizard for stock wizard
    '''
    _name = 'sale.order.line.assign.stock.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_done(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        if context is None: 
            context = {}
            
        line_pool = self.pool.get('sale.order.line')    
        
        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        
        # Parameters:
        line_id = wiz_browse.line_id
        new_assigned_qty = wiz_browse.new_assigned_qty
        
        # Update new assignement:
        line_pool.write(cr, uid, line_id.id, {
            'mx_assigned_qty': new_assigned_qty,
            }, context=context)
        
        return {
            'type': 'ir.actions.act_window_close'
            }

    def _get_status_line(self, cr, uid, context=None):
        ''' Fields function for calculate 
        '''
        if context is None:
            context = {}
        line_pool = self.pool.get('sale.order.line')
        
        line_id = context.get('default_line_id', False)
        if not line_id:
            raise osv.except_osv(
                _('Errore'), 
                _('Nessuna riga ordine presente'),
                )
        line = line_pool.browse(cr, uid, line_id, context=context)
        product = line.product_id
        available = product.mx_net_mrp_qty - product.mx_mrp_b_locked
        if available < 0.0:
            raise osv.except_osv(
                _(u'Errore'), 
                _(u'Il prodotto non ha quantità disponibili a magazzino!'),
                )
        
        return '''
            Attualmente rimaste assegnate: <b>%s</b><br/>
            Assegnabili per il prodotto: <b>%s</b><br/>
            <i>(Assegnate manualmente in origine: %s)</i>
            ''' % (
                line.mx_locked_qty,
                available,
                line.mx_assigned_qty,
                )
        
    _columns = {
        'line_id': fields.many2one(
            'sale.order.line', 'Sale line'),
        'status': fields.text('Stato riga'),
        'new_assigned_qty': fields.float('Nuova assegnazione', digits=(16, 2)),    
        }

    _defaults = {
        'status': lambda s, cr, uid, ctx: s._get_status_line(cr, uid, ctx),
        }    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
