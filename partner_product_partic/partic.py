# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP module
#    Copyright (C) 2010 Micronaet srl (<http://www.micronaet.it>) 
#    
#    Italian OpenERP Community (<http://www.openerp-italia.com>)
#
#############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import sys
import os
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger(__name__)

class ResPartnerProductPartic(osv.osv):
    ''' Add product partic obj
    '''    
    _inherit = 'res.partner.product.partic'

    # -------------------------------------------------------------------------
    #                                 Columns
    # -------------------------------------------------------------------------
    _columns = {
        'partner_code': fields.char('Partner code', size=40, required=True), 
        'partner_description': fields.char('Partner description', size=60,
            help='Description in partner\'s language'
            ),
        'partner_price': fields.float('Price', 
            digits_compute=dp.get_precision('Product Price')),     
        'price_from_date': fields.date('From date'),
        'price_to_date': fields.date('To date'),    
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
