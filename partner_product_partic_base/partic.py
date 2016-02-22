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
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger(__name__)

class ResPartnerProductPartic(osv.osv):
    ''' Add product partic obj
    '''    
    _inherit = 'res.company'
    
    _columns = {
        'partic_parent_len': fields.integer('Partic parent len'), 
        }

class ResPartnerProductPartic(osv.osv):
    ''' Add product partic obj
    '''    
    _name = 'res.partner.product.partic'
    _description = 'Partner product partic'
    _rec_name = 'product_id'
    _order = 'product_id'

    # -------------------------------------------------------------------------
    #                                 Columns
    # -------------------------------------------------------------------------
    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'), 
        'product_id': fields.many2one('product.product', 'Product', 
            required=True), 
        }

class ResPartner(osv.osv):
    ''' Add product partic in partner
    '''    
    _inherit = 'res.partner'
        
    _columns = {
        'use_partic': fields.boolean('Use partic.', 
            help='Customer use partic. for product descriptions'),
        'partic_ids': fields.one2many(
            'res.partner.product.partic', 'partner_id', 'Product partic.'), 
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
