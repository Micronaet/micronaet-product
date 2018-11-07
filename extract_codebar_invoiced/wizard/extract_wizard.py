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


class AccountInvoiceExtractCodebarWizard(orm.TransientModel):
    ''' Wizard for extract product invoice wizard
    '''
    _name = 'account.invoice.extract.codebar.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_done(self, cr, uid, ids, context=None):
        ''' Event for button done
        '''
        if context is None: 
            context = {}        
        
        wiz_browse = self.browse(cr, uid, ids, context=context)[0]

        # Pool used:
        line_pool = self.pool.get('account.invoice.line')
        excel_pool = self.pool.get('excel.writer')

        # Generate domain:
        domain = []
        filter_name = ''
        partner = wiz_browse.partner_id
        if partner:
            domain.append(('invoice_id.partner_id', '=', partner.id))
            filter_name += ' Partner: %s' % partner.name

        if wiz_browse.from_date:
            domain.append(
                ('invoice_id.date_invoice', '>=', wiz_browse.from_date))
            filter_name += ' From date >= %s' % wiz_browse.from_date

        if wiz_browse.to_date:
            domain.append(
                ('invoice_id.date_invoice', '<=', wiz_browse.to_date))
            filter_name += ' To date <= %s' % wiz_browse.to_date
                
        line_ids = line_pool.search(cr, uid, domain, context=context)        
        product_db = []
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            product = line.product_id
            if product and product not in product_db:
                product_db.append(product)

        # ---------------------------------------------------------------------
        # Start Excel file:        
        # ---------------------------------------------------------------------
        ws_name = 'EAN'
        header = [
            'Codice prodotto', 
            'Nome prodotto', 
            'EAN Pack',
            'EAN Singolo',
            ]
        width = [20, 40, 15, 15]
        
        ws = excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, width)
        #excel_pool.row_height(ws_name, row_list, height=10)
        title = _('Filtro: %s') % filter_name

        # ---------------------------------------------------------------------
        # Generate format used:
        # ---------------------------------------------------------------------
        excel_pool.set_format()
        f_title = excel_pool.get_format(key='title')
        f_header = excel_pool.get_format(key='header')
        f_text = excel_pool.get_format(key='text')
        f_number = excel_pool.get_format(key='number')

        # ---------------------------------------------------------------------
        # Write title / header    
        # ---------------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, [title], default_format=f_title)

        row += 1
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)
        
        row += 1
        for product in sorted(product_db, key=lambda x: x.default_code):
            try: 
                ean13_mono = product.ean13_mono
            except:
                ean13_mono = ''

            line = [
                product.default_code or '',
                product.name or '',
                product.ean13,
                ean13_mono,
                ]
            excel_pool.write_xls_line(
                ws_name, row, line, default_format=f_text)
            row += 1
        return excel_pool.return_attachment(cr, uid, 'EAN')

    _columns = {
        'partner_id': fields.many2one(
            'res.partner', 'Partner', help='Partner selected', required=True),
        'from_date': fields.date('From date >='),    
        'to_date': fields.date('To date <='),
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
