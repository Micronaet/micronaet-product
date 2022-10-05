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

from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta

from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


class AccountDutyInvoiceExtractWizard(orm.TransientModel):
    """ Wizard for extract product invoice wizard
    """
    _name = 'account.duty.invoice.extract.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_print(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        line_pool = self.pool.get('account.invoice.line')
        excel_pool = self.pool.get('excel.writer')

        if context is None:
            context = {}

        wizard = self.browse(cr, uid, ids, context=context)[0]
        from_date = wizard.from_date
        to_date = wizard.to_date
        fiscal_position_id = wizard.fiscal_position_id.id

        # Generate domain:
        domain = [
            ('invoice_id.date_invoice', '>=', from_date),
            ('invoice_id.date_invoice', '<=', to_date),
            ('invoice_id.fiscal_position', '=', fiscal_position_id),
        ]
        filter_name = 'Movimenti periodo [%s : %s] posizione fiscale: %s ' % (
            from_date, to_date, wizard.fiscal_position_id.name)

        line_ids = line_pool.search(cr, uid, domain, context=context)
        # product_db = {}

        lines = []
        for line in line_pool.browse(cr, uid, line_ids, context=context):
            lines.append(line)
            # product = line.product_id
            # if product and product not in product_db:
            #     product_db.append(product)

        # ---------------------------------------------------------------------
        # Start Excel file:
        # ---------------------------------------------------------------------
        ws_name = 'Dettaglio'
        header = [
            # Header:
            'Data',
            'Fattura',
            'Cliente',
            'P. IVA',
            'Posizione fiscale',

            # Detail:
            'Codice',
            'Prodotto',
            'Codice doganale',

            # Total:
            'Peso netto',
            'Q.',
            'Importo',
            ]
        width = [
            15, 15, 40, 15, 25,
            25, 40, 15, 15, 10, 10,
        ]

        excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, width)
        # excel_pool.row_height(ws_name, row_list, height=10)
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
        for line in sorted(
                lines,
                key=lambda x: (
                    x.invoice_id.partner_id.name,
                    x.invoice_id.date_invoice,
                    x.product_id.duty_id.code,
                    x.product_id.default_code,
                    )):
            product = line.product_id
            invoice = line.invoice_id
            partner = invoice.partner_id
            extra_data = product.extra_data_id

            line = [
                invoice.date_invoice,
                invoice.number,
                partner.name,
                partner.vat or '',
                invoice.fiscal_position.name or '',

                product.default_code or '',
                product.name,
                product.duty_id.code or '',
                (extra_data.weight_net, f_number),
                (line.quantity, f_number),
                (line.price_subtotal, f_number),
            ]
            excel_pool.write_xls_line(
                ws_name, row, line, default_format=f_text)
            row += 1
        return excel_pool.return_attachment(cr, uid, 'Intrastat')

    _columns = {
        'fiscal_position_id': fields.many2one(
            'account.fiscal.position', 'Posizione fiscale', required=True),
        'from_date': fields.date('From date >='),
        'to_date': fields.date('To date <='),
        }
