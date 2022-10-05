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
        #                         Start Excel file:
        # ---------------------------------------------------------------------
        # Page: Detail:
        # ---------------------------------------------------------------------
        ws_name = 'Dettaglio'
        header = [
            # Header:
            'Tipo',
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
            5, 15, 15, 40, 15, 25,
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
        format_db = {
            'title': excel_pool.get_format(key='title'),
            'header': excel_pool.get_format(key='header'),
            'white': {
                'text': excel_pool.get_format(key='text'),
                'number': excel_pool.get_format(key='number'),
                },
            'red': {
                'text': excel_pool.get_format(key='bg_red'),
                'number': excel_pool.get_format(key='bg_red_number'),
                },
            'green': {
                'text': excel_pool.get_format(key='bg_green'),
                'number': excel_pool.get_format(key='bg_green_number'),
                },
            'grey': {
                'text': excel_pool.get_format(key='bg_grey'),
                'number': excel_pool.get_format(key='bg_grey_number'),
                },
            }

        # ---------------------------------------------------------------------
        # Write title / header
        # ---------------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, [title], default_format=format_db['title'])

        row += 1
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=format_db['header'])
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)

        row += 1
        subtotal = {}
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

            duty_code = product.duty_id.code or ''

            # -----------------------------------------------------------------
            # Color setup:
            # -----------------------------------------------------------------
            if invoice.type == 'out_invoice':
                sign = +1.0
                color_format = format_db['white']
            else:
                sign = -1.0
                color_format = format_db['red']
            if not duty_code:
                color_format = format_db['grey']
            quantity = sign * line.quantity
            weight = quantity * extra_data.weight_net  # quantity has yet sign
            total = sign * line.price_subtotal

            # -----------------------------------------------------------------
            # Subtotal data (next sheet):
            # -----------------------------------------------------------------
            if duty_code and sign > 0:  # With code and only FT
                key = (partner, duty_code)
                if key not in subtotal:
                    subtotal[key] = {
                        'quantity': 0.0,
                        'weight': 0.0,
                        'total': 0.0,
                    }
                subtotal[key]['quantity'] += quantity
                subtotal[key]['weight'] += weight
                subtotal[key]['total'] += total

            # -----------------------------------------------------------------
            # Data:
            # -----------------------------------------------------------------
            line = [
                'FT' if sign > 0 else 'NC',
                invoice.date_invoice,
                invoice.number,
                partner.name,
                partner.vat or '',
                invoice.fiscal_position.name or '',

                product.default_code or '',
                line.name or '',
                duty_code,
                (weight, color_format['number']),
                (quantity, color_format['number']),
                (total, color_format['number']),
            ]
            excel_pool.write_xls_line(
                ws_name, row, line, default_format= color_format['text'])
            row += 1

        # ---------------------------------------------------------------------
        # Page: Summary
        # ---------------------------------------------------------------------
        ws_name = 'Riepilogo'
        header = [
            # Header:
            'Cliente',
            'P. IVA',

            # Detail:
            'Codice doganale',
            'Peso netto',
            'Q.',
            'Importo',
            ]
        width = [
            40, 15,
            15, 15, 10, 10,
        ]

        excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, width)

        # ---------------------------------------------------------------------
        # Write title / header
        # ---------------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=format_db['header'])
        excel_pool.autofilter(ws_name, row, 0, row, len(header) - 1)

        for key in sorted(subtotal, key=lambda k: (k[0].name, k[1])):
            row += 1
            partner, duty_code = key
            data = subtotal[key]
            excel_pool.write_xls_line(
                ws_name, row, [
                    partner.name,
                    partner.vat,

                    duty_code,
                    (data['weight'], format_db['white']['number']),
                    (data['quantity'], format_db['white']['number']),
                    (data['total'], format_db['white']['number']),
                ], default_format=format_db['white']['text'])

        return excel_pool.return_attachment(cr, uid, 'Intrastat')

    _columns = {
        'fiscal_position_id': fields.many2one(
            'account.fiscal.position', 'Posizione fiscale', required=True),
        'from_date': fields.date('From date >='),
        'to_date': fields.date('To date <='),
        }
