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

class ProductProductImportation(orm.Model):
    ''' Importation log element
    ''' 
    _name = 'product.product.importation'
    _description = 'Importation log'
    
    _columns = {
        'name': fields.char('Log description', size=80, required=True),
        'datetime': fields.date('Import date', required=True),
        'user_id': fields.many2one('res.users', 'User', required=True)
        'note': fields.char('Note'),
        }

    _defaults = {
        'datetime': lambda *x: datetime.now()
        'user_id': lambda s, cr, uid, ctx: uid,
        }

class ProductProduct(orm.Model):
    ''' Product for link import log
    '''    
    _name = 'product.product'
    
    _columns = {
        'csv_import_id': fields.one2many('product.product.importation',
            'Log import'),
        }
        
class ProductProductImportation(orm.Model):
    ''' Importation log element
    ''' 
    _inherit = 'product.product.importation'
    
    _columns = {
        'product_ids': fields.one2many('product.product', 'csv_import_id', 
            'Products'),
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
