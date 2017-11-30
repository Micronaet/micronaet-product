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
    ''' Link product to inventory purchase order
    '''
    _inherit = 'product.product'
    
    _columns = {
        'inventory_cost_no_move': fields.float(
            'Cost no move', digits=(16, 3),
            help='Init cost for no move product'),
        'inventory_cost_transport': fields.float(
            'Transport cost', digits=(16, 3),
            help='Transport cost from last delivery'),
        'inventory_cost_exchange': fields.float(
            'Buy exchange', digits=(16, 3), 
            help='USD exchange from last delivery'),
        }

class StockPicking(orm.Model):
    """ Model name: Stock picking
    """
    
    _inherit = 'stock.picking'
    
    # Button event:
    def force_purchase_data_in_product(self, cr, uid, ids, context=None):
        ''' Save in product the transport and USD exchange when created
        '''
        # Pool used:
        product_pool = self.pool.get('product.product')
        
        for picking in self.browse(cr, uid, ids, context=context):
            # TODO split cost!
            inventory_cost_transport = picking.inventory_cost_transport
            inventory_cost_exchange = picking.inventory_cost_exchange
            transport_id = picking.container_id.id
            
            for line in picking.move_lines:
                product = line.product_id
                
                # XXX not check if is present, write with button!
                container_q = 0
                for container in product.transport_ids:
                    if container.transport_id.id == transport_id:
                        container_q = container.quantity
                        break
                    
                if container_q:
                    inventory_cost_transport /= container_q
                else:
                    product.item_per_pallet = 0.0 # reset! TODO save a warning?

                product_pool.write(cr, uid, product.id, {
                    'inventory_cost_transport': inventory_cost_transport,
                    'inventory_cost_exchange': inventory_cost_exchange,
                    }, context=context)
        return True
        
    _columns = {
        'inventory_cost_transport': fields.float(
            'Transport cost', digits=(16, 3),
            help='Transport cost total for this order'),
        'inventory_cost_exchange': fields.float(
            'USD exchange', digits=(16, 3), 
            help='USD exchange for this order'),
        'container_id': fields.many2one(
            'product.cost.transport', 'Container / Camion'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
