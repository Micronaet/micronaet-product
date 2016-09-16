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

class ProductCostTransport(orm.Model):
    """ Model name: ProductCostTransport
    """    
    _name = 'product.cost.transport'
    _description = 'Transport method'
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'cost': fields.float(
            'Transport cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Transport cost in company currency', required=False),
        'mc': fields.float('M3 total', digits=(16, 2), required=False), 
        'note': fields.text('Note'),
        }
    
class ProductCostMethod(orm.Model):
    """ Product cost method
    """    
    _name = 'product.cost.method'
    _description = 'Cost method'
    
    _columns = {
        'name': fields.char('Rule', size=64, required=False),        
        'category': fields.selection([
            ('company', 'F / Company'),
            ('customer', 'F / Customer'),
            ('pricelist', 'Pricelist'),
            ], 'Category', 
            help='Used for get the cost to update, cost f/company, f/customer'
            'pricelist'),
        'transport_id': fields.many2one(
            'product.cost.transport', 'Transport'),
        }

    _defaults = {
        'category': lambda *x: 'company',            
        }
        

class ProductTemplate(orm.Model):
    """ Model name: ProductTemplate
    """    
    _inherit = 'product.template'
    
    _columns = {
        'method_id': fields.many2one('product.cost.method', 'Method'),
        'supplier_cost': fields.float('Supplier cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Supplier cost (pricelist cost, f/company)'),
        'customer_cost': fields.float('Customer cost', 
            digits_compute=dp.get_precision('Product Price'), 
            help='Customer cost (base for calculate goods f/customer)'),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
