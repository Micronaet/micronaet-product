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
import pickle
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


class StockInventoryHistoryYear(orm.Model):
    """ Model name: stock.inventory.history.year
    """

    _name = 'stock.inventory.history.year'
    _description = 'Inventario fine anno'
    _rec_name = 'name'
    _order = 'name'

    def generate_folder_structure(self, cr, uid, year, context=None):
        """ Generate folder structure
        """
        root_path = os.path.expanduser('~/inventory')

        # Create folder structure
        base_folder = os.path.join(root_path, year)
        os.system('mkdir -p %s' % base_folder)
        folder = os.path.join(base_folder, 'pickle')
        os.system('mkdir -p %s' % folder)
        folder = os.path.join(base_folder, 'excel')
        os.system('mkdir -p %s' % folder)
        folder = os.path.join(base_folder, 'log')
        os.system('mkdir -p %s' % folder)
        folder = os.path.join(base_folder, 'data')
        os.system('mkdir -p %s' % folder)
        folder = os.path.join(base_folder, 'result')
        os.system('mkdir -p %s' % folder)
        return base_folder

    def button_extract_invoice(self, cr, uid, ids, context=None):
        """ Extract invoice and put in pickle file
        """
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        from_date = inventory.from_date
        to_date = inventory.to_date

        if inventory.base_folder:
            base_folder = inventory.base_folder
        else:
            base_folder = self.generate_folder_structure(
                cr, uid, inventory.name, context=context)
            self.write(cr, uid, ids, {
                'base_folder': base_folder,
            }, context=context)

        line_pool = self.pool.get('account.invoice.line')
        modes = {
            'Fatture': ('out_invoice', -1),  # unload
            'NC': ('out_refund', +1),  # load
        }
        for setup in modes:
            mode, sign = modes[setup]
            pickle_file = os.path.join(
                base_folder, 'pickle', '%s.pickle' % setup)
            excel_file = os.path.join(
                base_folder, 'excel', '%s.xlsx' % setup)

            data = []
            # Collect data from invoices and credit note:
            line_ids = line_pool.search(cr, uid, [
                ('invoice_id.date_invoice', '>=', from_date),
                ('invoice_id.date_invoice', '<=', to_date),
                ('invoice_id.type', '=', mode),
            ], context=context)[:30]

            # --------------------------------------1--------------------------
            #                          Excel export:
            # -----------------------------------------------------------------
            ws_name = setup
            excel_pool.create_worksheet(name=ws_name)
            excel_pool.set_format(number_format='#,##0.####0')
            excel_format = {
                'title': excel_pool.get_format('title'),
                'header': excel_pool.get_format('header'),
                'text': excel_pool.get_format('text'),
                'number': excel_pool.get_format('number'),
                'white': {
                    'title': excel_pool.get_format('title'),
                    'header': excel_pool.get_format('header'),
                    'text': excel_pool.get_format('text'),
                    'number': excel_pool.get_format('number'),
                },
                'red': {
                    'title': excel_pool.get_format('title'),
                    'header': excel_pool.get_format('header'),
                    'text': excel_pool.get_format('bg_red'),
                    'number': excel_pool.get_format('bg_red_number'),
                },
                'green': {
                    'title': excel_pool.get_format('title'),
                    'header': excel_pool.get_format('header'),
                    'text': excel_pool.get_format('bg_green'),
                    'number': excel_pool.get_format('bg_green_number'),
                },

            }

            # Start writing in the sheet:
            width = [20, 40, 10, 30, 10, 10, 10]
            excel_pool.column_width(ws_name, width)

            header = {
                'Data', 'Rif.',
                'ID prodotto', 'Nome', 'Q.',
                'Ricodifica', 'Prezzo inventario',
            }
            row = 0
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=excel_format['header'])

            for line in line_pool.browse(
                    cr, uid, line_ids, context=context):
                row += 1
                invoice = line.invoice_id
                excel_record = [
                    invoice.date_invoice,
                    u'%s [%s]' % (
                        invoice.number, invoice.partner_id.name),
                    line.product_id.id,
                    u'%s' % line.name,
                    sign * line.quantity,
                    u'',
                    0.0,
                    ]
                record = {
                    'date': excel_record[0],
                    'ref': excel_record[1],
                    'product_id': excel_record[2],
                    'name': excel_record[3],
                    'quantity': excel_record[4],
                    'compress_code': excel_record[5],
                    'inventory_price': excel_record[6],
                }
                data.append(record)

                excel_pool.write_xls_line(
                    ws_name, row, excel_record,
                    default_format=excel_format['white']['text'])

            pickle.dump(data, open(pickle_file, 'wb'))
            excel_pool.save_file_as(excel_file)
        return True

    _columns = {
        'name': fields.char('Anno', size=64, required=True),
        'base_folder': fields.char(
            'Cartella base', size=180,
            help='Cartella dove sono memorizzati tutti i file della gestione'),
        'from_date': fields.date('Dalla data', required=True),
        'to_date': fields.date('Alla data', required=True),
    }


