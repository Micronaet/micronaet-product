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

    def restore_stock_status_user_value(
            self, cr, uid, no_inventory_status, context=None):
        ''' Update with previous value
        '''
        return self.pool.get('res.users').write(
            cr, uid, [uid], {
                'no_inventory_status': no_inventory_status,
                }, context=context)

        
    def return_view_assign_wizard(self, cr, uid, ids, context=None):
        ''' Open wizard view:
        '''
        wiz_pool = self.pool.get('sale.order.line.assign.stock.wizard')

        # Activate stock status:
        user_pool = self.pool.get('res.users')
        user = user_pool.browse(cr, uid, uid, context=context)
        no_inventory_status = user.no_inventory_status
        user_pool.write(cr, uid, [uid], {
            'no_inventory_status': False,
            }, context=context)    
            
        # ---------------------------------------------------------------------
        #                             Check data:
        # ---------------------------------------------------------------------
        # A. Check previsional order:
        line = self.browse(cr, uid, ids, context=context)[0]
        order = line.order_id
        if order.previsional:
            self.restore_stock_status_user_value(
                cr, uid, no_inventory_status, context=context)
            raise osv.except_osv(
                _('Errore'), 
                _('''Ordine previsionale, non permessa una assegnazione da 
                     magazzino in quando viene fatto per caricare il magazzino
                     '''))
        
        # B. State of order:             
        if order.state not in ('manual', 'progress'):
            self.restore_stock_status_user_value(
                cr, uid, no_inventory_status, context=context)
            raise osv.except_osv(
                _('Errore'), 
                _('''Ordine non nel corretto stato:
                     solo gli ordini attivi non chiusi possono avere 
                     assegnazioni da magazzino.
                     '''))

        # C. Available in stock:    
        product = line.product_id
        available = product.mx_net_mrp_qty - product.mx_mrp_b_locked
        if available <= 0.0:
            self.restore_stock_status_user_value(
                cr, uid, no_inventory_status, context=context)
            raise osv.except_osv(
                _(u'Errore'), 
                _(u'Il prodotto %s non ha disponibilità a magazzino!' % (
                    product.default_code or product.name or '?'
                    )),
                )
        
        # D. Remain positive:
        oc_qty = line.product_uom_qty
        delivery_qty = line.delivered_qty
        assigned = line.mx_assigned_qty # current

        to_assign = oc_qty # all ordered
        maked = 0.0
        warning = ''
        if 'product_uom_maked_sync_qty' in line._columns:
            maked = line.product_uom_maked_sync_qty
            # XXX if yet production use wait the production?
            if line.mrp_id:
                warning = 'PRESENTE UNA PRODUZIONE COLLEGATA'
            if maked:
                to_assign = oc_qty - maked # remain to produce
                warning += ' CON MATERIALE PRECEDENTEMENTE CARICATO'    
            warning += '!!!'

        if to_assign <= 0:
            self.restore_stock_status_user_value(
                cr, uid, no_inventory_status, context=context)
            raise osv.except_osv(
                _(u'Errore'), 
                _(u'Al prodotto %s non servono assegnazioni di magazzino!' % (
                    product.default_code or product.name or '?'
                    )),
                )
        # XXX To remove assign I cannot add this check!!!
        #elif abs(to_assign - assigned) <= 0.01: # approx check
        #    self.restore_stock_status_user_value(
        #        cr, uid, no_inventory_status, context=context)
        #    raise osv.except_osv(
        #        _(u'Errore'), 
        #        _(u'Al prodotto %s sono già assegnati %s!' % (
        #            product.default_code or product.name or '?',
        #            assigned,
        #            )),
        #        )

        # ---------------------------------------------------------------------
        # Create record for wizard and open:
        # ---------------------------------------------------------------------
        # Default assignement:
        if to_assign >= (available + assigned):
            new_assigned_qty = available
        else:
            new_assigned_qty = to_assign   
            
        wiz_id = wiz_pool.create(cr, uid, {
            'new_assigned_qty': new_assigned_qty,
            'line_id': ids[0],
            'status': '''
                OC: <b>%s</b><br/>
                Produzione: <b>%s</b><br/>
                Consegnate: <b>%s</b><br/><br/>
                
                <i>Assegnabili per il prodotto: <b>%s</b><br/>
                (di cui assegnate a questo in precedenza: <b>%s</b>)<br/></i>
                
                <font color="red"><b>%s</b></font>
                ''' % (
                    oc_qty,
                    maked,
                    delivery_qty,
                    
                    available,
                    assigned,
                    warning,
                    )
            }, context=context)

        # Get and return correct view:
        model_pool = self.pool.get('ir.model.data')
        view_id = model_pool.get_object_reference(
            cr, uid,
            'inventory_status_assign_wizard', 
            'sale_order_line_assign_stock_wizard_view')[1]

        self.restore_stock_status_user_value(
            cr, uid, no_inventory_status, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Assegna q. magazzino'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz_id,
            'res_model': 'sale.order.line.assign.stock.wizard',
            'view_id': view_id,
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

    # -------------------------------------------------------------------------
    # Wizard button event:
    # -------------------------------------------------------------------------
    def action_remove_qty(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        if context is None: 
            context = {}

        # Remove assignement:
        line_pool = self.pool.get('sale.order.line')    
        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        line_id = wiz_browse.line_id

        return line_pool.write(cr, uid, line_id.id, {
            'mx_assigned_qty': 0,
            }, context=context)
        
    def action_assign_qty(self, cr, uid, ids, context=None):
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
        return line_pool.write(cr, uid, line_id.id, {
            'mx_assigned_qty': new_assigned_qty,
            }, context=context)

    _columns = {
        'line_id': fields.many2one(
            'sale.order.line', 'Sale line'),
        'status': fields.text('Stato riga'),
        'new_assigned_qty': fields.float('Nuova assegnazione', digits=(16, 2)),    
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
