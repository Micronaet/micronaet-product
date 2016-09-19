# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP) 
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
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


class ProductMethodForceCalcWizard(orm.TransientModel):
    ''' Wizard for
    '''
    _name = 'product.method.force.calc.wizard'
    _description = 'Force calc or assign method to product'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_execute(self, cr, uid, ids, context=None):
        ''' Event for button execute
        '''
        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        
        product_pool = self.pool.get('product.product')
        
        # ---------------------------------------------------------------------
        # 1. generate filter and search product
        # ---------------------------------------------------------------------
        domain = []
        
        # Supplier filter:
        if wiz_browse.first_supplier_id:
            domain.append(
                ('first_supplier_id', '=', wiz_browse.first_supplier_id.id))
                
       
        product_ids = product_pool.search(cr, uid, domain, context=context)
        
        # ---------------------------------------------------------------------
        # 3. force calc method (depend on check button)
        # ---------------------------------------------------------------------
        if wiz_browse.company_set:
            product_pool.write(cr, uid, product_ids, {
                'company_method_id': wiz_browse.company_method_id.id,
                }, context=context)
        
        # ---------------------------------------------------------------------
        # 4. force calc operation
        # ---------------------------------------------------------------------
        
        return {
            'type': 'ir.actions.act_window_close'
            }

    _columns = {
        # Filter field:
        'first_supplier_id': fields.many2one(
            'res.partner', 'First supplier'),
    
        # Calculation field:
        'company_calc': fields.boolean('Company set method'),
        'customer_calc': fields.boolean('Customer set method'),
        'pricelist_calc': fields.boolean('Pricelist set method'),
        
        # Set field:
        'company_set': fields.boolean('Company set method'),
        'customer_set': fields.boolean('Customer set method'),
        'pricelist_set': fields.boolean('Pricelist set method'),
        
        'company_method_id': fields.many2one(
            'product.cost.method', 'Company Method'),
        'customer_method_id': fields.many2one(
            'product.cost.method', 'Customer Method'),
        'pricelist_method_id': fields.many2one(
            'product.cost.method', 'Pricelist Method'),        
        }
        
    _defaults = {
        
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


