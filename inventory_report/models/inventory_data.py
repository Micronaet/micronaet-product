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
import pdb
import sys
import logging
import pickle
import xlrd
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


# todo save in Form:
metal_price = {
    'TBAL': 3.30,
    'TBFE': 0.78,
    'TBFZ': 0.78,
    'TBFN': 0.78,
    'TBZN': 0.78,  # todo not present
}

pipe_codes = {
    'TBAL': 'TUBAL',
    'TBFE': 'TUBFE',
    'TBFZ': 'TUBFZ',
    'TBZN': 'TUBFZ',
    }

fabric_code = {
    'TEX': 'TESTEX',
    'TXM': 'TESTEX',
    'TJO': 'TESTEX',
    'TXI': 'TESTEX',
    'TXR': 'TESTEX',
    'T3D': 'TES3D',
    'TNT': 'TESTNT',

    'TESCOING': 'TESCOING',
    'TESPOL': 'TESPOLTU',
    'TESAD': 'TESAD',


}
fabric_start6 = [
    'TESACR',
    'TESINT',
    'TESJUT',
    'TESTNT',
    'TSK160',
    'TESCOT',
    'TESRET',
    'TESRAF',
]

half_text = [
    'MS', 'PO', 'TS',
    'MT', 'PA', 'TL',
    'TP',
]

total_mode = [
    'Fatture',
    'NC',
    'MRP load',
    'MRP unload',
    'Job',
    'Pick',
    'Acquisti',
    'Finale',
]


class StockInventoryHistoryYear(orm.Model):
    """ Model name: stock.inventory.history.year
    """

    _name = 'stock.inventory.history.year'
    _description = 'Inventario fine anno'
    _rec_name = 'name'
    _order = 'name'

    def clean_code(self, default_code):
        """ Code problem
        """
        if 'NON USARE ' in (default_code or ''):
            default_code = default_code.replace('NON USARE ', '').strip()
        return default_code

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

    def get_excel_format(self, excel_pool):
        """ Setup excel format
        """
        excel_pool.set_format(number_format='#,##0.####0')
        return {
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

    def product_db_update(self, product_db, product_id, qty, origin):
        """ Load product file
        """
        if product_id not in product_db:
            product_db[product_id] = {}
        if origin not in product_db[product_id]:
            product_db[product_id][origin] = [0.0, 0.0]  # Load, Unload
        if qty > 0:
            product_db[product_id][origin][0] += qty
        else:
            product_db[product_id][origin][1] += qty

    def get_product_db(self, base_folder, mode='product'):
        """ Load product file
        """
        _logger.info('Logger %s' % mode)
        filename = os.path.join(base_folder, 'pickle', '%s.pickle' % mode)
        try:
            return pickle.load(open(filename, 'rb'))
        except:
            _logger.warning('DB for %s was created now' % mode)
            return {}

    def save_product_db(self, base_folder, data, mode='product'):
        """ Load product file
        """
        _logger.info('Logger product')
        filename = os.path.join(base_folder, 'pickle', '%s.pickle' % mode)
        _logger.warning('Save # %s %ss' % (len(data), mode))
        return pickle.dump(data, open(filename, 'wb'))

    def button_extract_product_price(self, cr, uid, ids, context=None):
        """ Extract last price in history
        """
        product_pool = self.pool.get('product.product')
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder
        from_date = inventory.from_date
        to_date = inventory.to_date
        excel_file = os.path.join(
            base_folder, 'excel', 'MRP_Prodotti.xlsx')

        mrp_data = {}  # Collect price

        # Call oridinal data structure used in report:
        datas = {
            'wizard': True,
            'from_date': from_date,
            'to_date': to_date,
        }

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = 'Prezzi MRP'
        excel_pool.create_worksheet(name=ws_name)
        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            10, 15, 15, 100
        ]
        excel_pool.column_width(ws_name, width)

        header = [
            'Modello', 'Min', 'Max', 'Dettaglio',
        ]
        cols = len(header)
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])
        excel_pool.autofilter(ws_name, row, 0, row, cols)
        excel_pool.freeze_panes(ws_name, row, cols)

        for report_data in product_pool.report_get_objects_bom_industrial_cost(
                cr, uid, datas=datas, context=context):
            price_min = report_data[0]
            price_max = report_data[1]
            product_code = (report_data[8].default_code or '')[:6].strip()

            excel_record = [
                product_code,
                price_min,
                price_max,
                u'%s' % report_data,
                ]
            mrp_data[product_code] = price_min

            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_record,
                default_format=excel_format['white']['text'])

        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, mrp_data, 'product_mrp')
        return True

    def button_extract_semiproduct_price(self, cr, uid, ids, context=None):
        """ Extract Calcolo prezzo semilavorati
        """
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)  # List of product
        price_db = self.get_product_db(base_folder, 'price')  # Raw material
        price_now_db = self.get_product_db(base_folder, 'price_now')
        semiproduct_db = {}  # Clean everytime

        product_pool = self.pool.get('product.product')
        excel_file = os.path.join(
            base_folder, 'excel', 'Prezzi_semilavorati.xlsx')

        # Collect data from invoices and credit note:
        products = product_pool.browse(cr, uid, product_db, context=context)

        # -----------------------------------------------------------------
        #                          Excel export:
        # -----------------------------------------------------------------
        ws_name = 'Prezzi Semilavorati'
        excel_pool.create_worksheet(name=ws_name)
        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            10, 15, 30, 15, 30, 5
        ]
        excel_pool.column_width(ws_name, width)

        header = [
            'ID', 'Codice', 'Nome', 'Prezzo', 'Dettaglio', 'Errore',
            'Prezzo attuale',
        ]
        cols = len(header)
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])
        excel_pool.autofilter(ws_name, row, 0, row, cols)
        excel_pool.freeze_panes(ws_name, row, cols)

        for product in products:
            product_id = product.id
            default_code = product.default_code or ''
            hw = product.half_bom_ids
            if not hw:
                continue

            price_detail = ''
            price_error = ''
            price_new_error = ''
            hw_price = 0.0
            for component_line in hw:
                component = component_line.product_id
                component_id = component.id
                component_code = component.default_code
                component_qty = component_line.product_qty
                if component.is_pipe:  # Prezzo tubo
                    code4 = component_code[:4]
                    weight = component.weight
                    unit_price = metal_price.get(code4, 0.0)
                    price = unit_price * weight
                    total = price * component_qty
                    hw_price += total
                    price_detail += u'[%s€ >> Q.%s x %s: %sKg x %s€, %s€]' % (
                        total,
                        component_qty,
                        component_code,
                        weight,
                        unit_price,
                        price,
                    )
                    if not total:
                        price_error = 'X'
                else:
                    price = price_db.get(component_id, 0.0)
                    price_new = ''
                    if not price:  # Take current
                        price = price_now_db.get(component_id, 0.0)
                        price_new = '*'
                    if not price:
                        price = component.standard_price
                        price_new = 'STD'  # Fall back on standard
                    if not price:
                        price_new_error = 'X'
                    total = price * component_qty
                    hw_price += total
                    price_detail += u'[%s€ >> Q.%s x %s, %s€ %s]' % (
                        total,
                        component_qty,
                        component_code,
                        price,
                        price_new,
                    )
                    if not total:
                        price_error = 'X'

            excel_record = [
                product_id,
                default_code,
                product.name,
                hw_price,
                price_detail,
                price_error,
                price_new_error,
                ]
            semiproduct_db[product_id] = hw_price

            if price_error == 'X' or price_new_error == 'X':
                excel_color = excel_format['red']
            else:
                excel_color = excel_format['white']

            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_record,
                default_format=excel_color['text'])

        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, semiproduct_db, 'semiproduct')
        return True

    def button_extract_product_move(self, cr, uid, ids, context=None):
        """ Extract invoice and put in pickle file
        """
        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)
        price_db = self.get_product_db(base_folder, 'price')  # For price
        semiproduct_db = self.get_product_db(base_folder, 'semiproduct')
        mrp_db = self.get_product_db(base_folder, 'product_mrp')
        final_db = {}  # Pack per code

        excel_file = os.path.join(base_folder, 'excel', 'Prodotti.xlsx')
        products = product_pool.browse(cr, uid, product_db, context=context)

        # -----------------------------------------------------------------
        #                          Excel export:
        # -----------------------------------------------------------------
        ws_name = 'Prodotti'
        excel_pool.create_worksheet(name=ws_name)
        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            10, 30, 15, 15, 40,
            30, 5, 5,
            15, 15,
            10, 40, 50
        ]
        excel_pool.column_width(ws_name, width)

        header = [
            'ID', 'Tipo', 'Codice', 'Codice ragg.', 'Nome',
            'Categoria', 'MRP', 'SL',
            'Car.', 'Scar.',
            'Prezzo', 'Errore',
            'Dettaglio',
        ]
        cols = len(header)
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])
        excel_pool.autofilter(ws_name, row, 0, row, cols)
        excel_pool.freeze_panes(ws_name, row, cols)

        for product in sorted(products, key=lambda x: x.default_code):
            product_id = product.id
            default_code = self.clean_code(product.default_code)

            row += 1
            total_load = total_unload = 0.0
            move_detail = ''
            for move in product_db[product_id]:
                load, unload = product_db[product_id][move]
                move_detail += '[%s C: %s, S: %s]' % (
                    move, load, unload
                )
                total_load += load
                total_unload += unload

            category = product.inventory_category_id.name or ''
            dynamic_bom = product.dynamic_bom_line_ids
            hw_bom = product.half_bom_ids

            new_code = ''
            error = ''
            # Fall back on std price:
            price = price_db.get(product_id, product.standard_price)

            if default_code:
                inventory_selected = True
            else:
                inventory_selected = False

            if dynamic_bom:
                mode = 'Prodotto Fiam'
                if default_code[:3].isdigit():
                    new_code = default_code[:6].strip()
                elif not default_code[:2].isdigit() and \
                        default_code[2:5].isdigit():
                    new_code = default_code[:8].strip()
                code6 = default_code[:6].strip()
                price = mrp_db.get(code6, product.standard_price)
            elif hw_bom:
                mode = 'Semilavorato'

                # Recoded:
                if default_code[:2] in half_text and \
                        default_code[2:5].isdigit():
                    new_code = default_code[:8].strip()

                price = semiproduct_db.get(product_id)
            elif category == 'Commercializzati':
                mode = 'Commercializzato'
            elif product.is_pipe:
                mode = 'Tubo'
                code4 = default_code[:4].strip()

                new_code = pipe_codes.get(code4)
                if not new_code:
                    error = 'Codice tubo non trovato'

                price = metal_price.get(code4, 0.0) * product.weight

            elif category == 'Tessuti':
                mode = 'Tessuto'

                # Recoded:
                code6 = default_code[:6].strip()
                if code6 in fabric_start6:
                    new_code = code6
                else:
                    for start in fabric_code:
                        if default_code.startswith(start):
                            new_code = fabric_code[start]
                            break
                if not new_code:
                    error = 'Codice tessuto non trovato'
            elif category in ('Esclusi', 'Lavorazioni'):
                mode = 'Esclusi'
                inventory_selected = False
            else:
                mode = 'Materie prime'

            excel_record = [
                product_id,
                mode,
                product.default_code or '',
                new_code,
                product.name,

                category,
                'X' if dynamic_bom else '',
                'X' if hw_bom else '',
                total_load,
                total_unload,
                price,
                error,
                move_detail,
                ]

            if price <= 0.0000000001:
                excel_color = excel_format['red']
            else:
                excel_color = excel_format['white']

            excel_pool.write_xls_line(
                ws_name, row, excel_record,
                default_format=excel_color['text'])

            if inventory_selected:
                final_db[new_code or default_code] = [
                    mode,
                    category,
                    total_load,
                    total_unload,
                    price,
                ]

        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, final_db, 'final_inventory')
        return True

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

        # Product management:
        product_db = self.get_product_db(base_folder)

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
            ], context=context)

            # -----------------------------------------------------------------
            #                          Excel export:
            # -----------------------------------------------------------------
            ws_name = setup
            excel_pool.create_worksheet(name=ws_name)
            excel_format = self.get_excel_format(excel_pool)

            # Start writing in the sheet:
            width = [
                15, 40,
                10, 15, 35, 10,
                10, 10]
            excel_pool.column_width(ws_name, width)

            header = [
                'Data', 'Rif.',
                'ID prodotto', 'Codice', 'Nome', 'Q.',
                'Ricodifica', 'Prezzo inventario',
            ]
            row = 0
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=excel_format['header'])

            for line in line_pool.browse(
                    cr, uid, line_ids, context=context):
                row += 1
                invoice = line.invoice_id
                product_id = line.product_id.id
                qty = sign * line.quantity
                excel_record = [
                    invoice.date_invoice,
                    u'%s [%s]' % (
                        invoice.number, invoice.partner_id.name),
                    product_id,
                    line.product_id.default_code,
                    u'%s' % line.name,
                    qty,
                    u'',
                    0.0,
                    ]
                record = {
                    'date': excel_record[0],
                    'ref': excel_record[1],
                    'product_id': excel_record[2],
                    'default_code': excel_record[3],
                    'name': excel_record[4],
                    'quantity': excel_record[5],
                    'compress_code': excel_record[6],
                    'inventory_price': excel_record[7],
                }
                data.append(record)
                self.product_db_update(product_db, product_id, qty, setup)

                excel_pool.write_xls_line(
                    ws_name, row, excel_record,
                    default_format=excel_format['white']['text'])

            pickle.dump(data, open(pickle_file, 'wb'))
            excel_pool.save_file_as(excel_file)

        self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_invoice':
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
        }, context=context)

    def button_extract_mrp(self, cr, uid, ids, context=None):
        """ Extract invoice and put in pickle file
        """
        excel_pool = self.pool.get('excel.writer')
        setup = 'MRP'

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        from_date = inventory.from_date
        to_date = inventory.to_date
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)

        line_pool = self.pool.get('sale.order.line')

        pickle_file = os.path.join(
            base_folder, 'pickle', '%s.pickle' % setup)
        excel_file = os.path.join(
            base_folder, 'excel', '%s.xlsx' % setup)

        data = []
        # Collect data from invoices and credit note:
        line_ids = line_pool.search(cr, uid, [
            ('mrp_id.date_planned', '>=', '%s 00:00:00' % from_date),
            ('mrp_id.date_planned', '<=', '%s 23:59:59' % to_date),
        ], context=context)

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = setup
        excel_pool.create_worksheet(name=ws_name)

        ws_name_component = 'Componenti'
        excel_pool.create_worksheet(name=ws_name_component)

        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            15, 30,
            40, 15, 15, 15,
            15, 15]
        excel_pool.column_width(ws_name, width)
        excel_pool.column_width(ws_name_component, width)

        header = [
            'Data', 'Rif.',
            'Nome', 'Codice', 'ID prodotto', 'Ricodifica',
            'Q.', 'Prezzo inventario',
        ]
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        row_2 = 0
        excel_pool.write_xls_line(
            ws_name_component, row_2, header,
            default_format=excel_format['header'])

        bom_cache = {}
        for line in line_pool.browse(
                cr, uid, line_ids, context=context):
            # -----------------------------------------------------------------
            # MRP Product:
            # -----------------------------------------------------------------
            mrp = line.mrp_id
            product = line.product_id
            product_id = product.id
            qty = line.product_uom_qty

            excel_record = [
                mrp.date_planned,
                mrp.name,

                u'%s' % product.name,
                product.default_code,
                product_id,
                '',  # Re-code

                qty,
                0.0,
                ]
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_record,
                default_format=excel_format['white']['text'])

            record = {
                'date': excel_record[0],
                'ref': excel_record[1],
                'name': excel_record[2],
                'default_code': excel_record[3],
                'product_id': excel_record[4],
                'compress_code': excel_record[5],
                'quantity': excel_record[6],
                'inventory_price': excel_record[7],
            }
            data.append(record)
            self.product_db_update(product_db, product_id, qty, 'MRP load')

            # -----------------------------------------------------------------
            # Unload Component:
            # -----------------------------------------------------------------
            # Cache BOM:
            if product_id not in bom_cache:
                bom_cache[product_id] = product.dynamic_bom_line_ids

            for component_line in bom_cache[product_id]:
                component = component_line.product_id
                cmp_qty = - line.product_uom_qty * component_line.product_qty
                excel_record = [
                    mrp.date_planned,
                    mrp.name,

                    component.name,
                    component.default_code,
                    component.id,
                    '',  # Re-code

                    cmp_qty,
                    0.0,
                ]
                row_2 += 1
                excel_pool.write_xls_line(
                    ws_name_component, row_2, excel_record,
                    default_format=excel_format['white']['text'])

                record = {
                    'date': excel_record[0],
                    'ref': excel_record[1],
                    'name': excel_record[2],
                    'default_code': excel_record[3],
                    'product_id': excel_record[4],
                    'compress_code': excel_record[5],
                    'quantity': excel_record[6],
                    'inventory_price': excel_record[7],
                }
                if not component.bom_placeholder:
                    data.append(record)  # Only if not placeholder
                    self.product_db_update(
                        product_db, component.id, cmp_qty, 'MRP unload')

        pickle.dump(data, open(pickle_file, 'wb'))
        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_mrp': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }, context=context)

    def button_extract_job(self, cr, uid, ids, context=None):
        """ Extract Job
        """
        excel_pool = self.pool.get('excel.writer')
        setup = 'Semilavorati'

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        from_date = inventory.from_date
        to_date = inventory.to_date
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)

        move_pool = self.pool.get('stock.quant')

        pickle_file = os.path.join(
            base_folder, 'pickle', '%s.pickle' % setup)
        excel_file = os.path.join(
            base_folder, 'excel', '%s.xlsx' % setup)

        data = []
        # Collect data from invoices and credit note:
        line_ids = move_pool.search(cr, uid, [
            ('lavoration_link_id.date', '>=', '%s 00:00:00' % from_date),
            ('lavoration_link_id.date', '<=', '%s 23:59:59' % to_date),
            ('lavoration_link_id.dep_mode', 'in', ('cut', 'workshop')),
        ], context=context)

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = setup
        excel_pool.create_worksheet(name=ws_name)

        ws_name_component = 'Materie prime'
        excel_pool.create_worksheet(name=ws_name_component)

        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            15, 30,
            40, 15, 15, 15,
            15, 15]
        excel_pool.column_width(ws_name, width)
        excel_pool.column_width(ws_name_component, width)

        header = [
            'Data', 'Rif.',
            'Nome', 'Codice', 'ID prodotto', 'Ricodifica',
            'Q.', 'Prezzo inventario',
        ]
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        row_2 = 0
        excel_pool.write_xls_line(
            ws_name_component, row_2, header,
            default_format=excel_format['header'])

        for line in move_pool.browse(
                cr, uid, line_ids, context=context):
            picking = line.lavoration_link_id
            product = line.product_id
            default_code = product.default_code or ''
            product_id = product.id
            new_code = ''

            # -----------------------------------------------------------------
            # Job data: Semi product - Raw material
            # -----------------------------------------------------------------
            qty = line.qty
            if qty > 0:
                use_ws = setup
                row += 1
            else:
                use_ws = 'Materie prime'
                row_2 += 1

            excel_record = [
                picking.date,
                picking.name,

                u'%s' % product.name,
                product.default_code,
                product_id,
                new_code,

                qty,
                0.0,
                ]
            excel_pool.write_xls_line(
                use_ws, row, excel_record,
                default_format=excel_format['white']['text'])

            record = {
                'date': excel_record[0],
                'ref': excel_record[1],
                'name': excel_record[2],
                'default_code': excel_record[3],
                'product_id': excel_record[4],
                'compress_code': excel_record[5],
                'quantity': excel_record[6],
                'inventory_price': excel_record[7],
            }
            data.append(record)
            self.product_db_update(
                product_db, product_id, qty, 'Job')

        pickle.dump(data, open(pickle_file, 'wb'))
        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_job':
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }, context=context)

    def button_extract_picking(self, cr, uid, ids, context=None):
        """ Extract Job
        """
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        from_date = inventory.from_date
        to_date = inventory.to_date
        cl_id = inventory.cl_id.id
        sl_id = inventory.sl_id.id
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)

        move_pool = self.pool.get('stock.move')

        data = []
        pickle_file = os.path.join(
            base_folder, 'pickle', 'Correzioni.pickle')
        excel_file = os.path.join(
            base_folder, 'excel', 'Correzioni.xlsx')
        for setup, stock_id, sign in (('CL', cl_id, +1), ('SL', sl_id, -1)):

            # Collect data from invoices and credit note:
            line_ids = move_pool.search(cr, uid, [
                ('picking_id.date', '>=', '%s 00:00:00' % from_date),
                ('picking_id.date', '<=', '%s 23:59:59' % to_date),
                ('picking_type_id', '=', stock_id),
                ('picking_id.dep_mode', 'not in', ('cut', 'workshop')),

            ], context=context)

            # -----------------------------------------------------------------
            #                          Excel export:
            # -----------------------------------------------------------------
            ws_name = setup
            excel_pool.create_worksheet(name=ws_name)
            excel_format = self.get_excel_format(excel_pool)

            # Start writing in the sheet:
            width = [
                15, 30,
                40, 15, 15, 15,
                15, 15, 40, 15]
            excel_pool.column_width(ws_name, width)

            header = [
                'Data', 'Rif.',
                'Nome', 'Codice', 'ID prodotto', 'Ricodifica',
                'Q.', 'Prezzo inventario', 'Note', 'Stato',
            ]
            row = 0
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=excel_format['header'])

            for line in move_pool.browse(
                    cr, uid, line_ids, context=context):
                picking = line.picking_id
                product = line.product_id
                product_id = product.id

                # -------------------------------------------------------------
                # Uload SL, Load CL:
                # -------------------------------------------------------------
                qty = sign * line.product_qty
                note = picking.origin or picking.note or ''
                if note.startswith('MO'):
                    used = False
                else:
                    used = True
                excel_record = [
                    picking.date,
                    '%s: %s' % (setup, picking.name),

                    u'%s' % product.name,
                    product.default_code,
                    product_id,
                    '',  # Re-code

                    qty,
                    0.0,
                    note,
                    'Usato' if used else 'Non usato',
                    ]

                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, excel_record,
                    default_format=excel_format['white']['text'])

                if used:
                    record = {
                        'date': excel_record[0],
                        'ref': excel_record[1],
                        'name': excel_record[2],
                        'default_code': excel_record[3],
                        'product_id': excel_record[4],
                        'compress_code': excel_record[5],
                        'quantity': excel_record[6],
                        'inventory_price': excel_record[7],
                    }
                    data.append(record)
                    self.product_db_update(product_db, product_id, qty, 'Pick')

        pickle.dump(data, open(pickle_file, 'wb'))
        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_picking':
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }, context=context)

    def button_extract_purchase(self, cr, uid, ids, context=None):
        """ Extract Job
        """
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        from_date = inventory.from_date
        to_date = inventory.to_date
        purchase_id = inventory.purchase_id.id
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)

        move_pool = self.pool.get('stock.move')

        data = []
        pickle_file = os.path.join(
            base_folder, 'pickle', 'Acquisti.pickle')
        excel_file = os.path.join(
            base_folder, 'excel', 'Acquisti.xlsx')

        # Collect data from invoices and credit note:
        line_ids = move_pool.search(cr, uid, [
            ('picking_id.date', '>=', '%s 00:00:00' % from_date),
            ('picking_id.date', '<=', '%s 23:59:59' % to_date),
            ('picking_type_id', '=', purchase_id),
            ('state', '=', 'done'),
            # ('picking_id.dep_mode', 'not in', ('cut', 'workshop')),
        ], context=context)

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = 'Acquisti'
        excel_pool.create_worksheet(name=ws_name)
        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            15, 30,
            40, 15, 15, 15,
            15, 15]
        excel_pool.column_width(ws_name, width)

        header = [
            'Data', 'Rif.',
            'Nome', 'Codice', 'ID prodotto', 'Ricodifica',
            'Q.', 'Prezzo inventario',
        ]
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        for line in move_pool.browse(
                cr, uid, line_ids, context=context):
            picking = line.picking_id
            product = line.product_id
            product_id = product.id

            # -------------------------------------------------------------
            # Uload SL, Load CL:
            # -------------------------------------------------------------
            qty = line.product_qty
            excel_record = [
                picking.date,
                '%s: %s' % (picking.origin, picking.name),

                u'%s' % product.name,
                product.default_code,
                product_id,
                '',  # Re-code

                qty,
                0.0,
                ]

            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_record,
                default_format=excel_format['white']['text'])

            record = {
                'date': excel_record[0],
                'ref': excel_record[1],
                'name': excel_record[2],
                'default_code': excel_record[3],
                'product_id': excel_record[4],
                'compress_code': excel_record[5],
                'quantity': excel_record[6],
                'inventory_price': excel_record[7],
            }
            data.append(record)
            self.product_db_update(product_db, product_id, qty, ws_name)

        pickle.dump(data, open(pickle_file, 'wb'))
        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_purchase':
                datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }, context=context)

    def button_extract_begin(self, cr, uid, ids, context=None):
        """ Extract final status
        """
        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder
        row_start = inventory.row_start
        file_in = os.path.expanduser(inventory.start_filename)
        start_db = {}

        # ---------------------------------------------------------------------
        # Load origin name from XLS
        # ---------------------------------------------------------------------
        try:
            WB = xlrd.open_workbook(file_in)
        except:
            raise osv.except_osv(
                _('No file:'),
                _('[ERROR] Cannot read XLS file: %s' % file_in))

        for index in range(3):
            ws = WB.sheet_by_index(index)
            for row in range(row_start - 1, ws.nrows):
                default_code = str(ws.cell(row, 0).value) or ''
                if default_code.endswith('.0'):
                    default_code = default_code[:-2]
                default_code = self.clean_code(default_code)

                name = ws.cell(row, 1).value
                uom = ws.cell(row, 2).value
                qty = ws.cell(row, 3).value
                price = ws.cell(row, 4).value
                subtotal = ws.cell(row, 5).value

                start_db[default_code] = {
                    # Start data:
                    'qty_start': qty,
                    'price_start': price,
                    'name': name,
                    'uom': uom,
                }
        self.save_product_db(base_folder, start_db, 'start')

    def button_extract_final(self, cr, uid, ids, context=None):
        """ Extract final status
        """
        product_pool = self.pool.get('product.product.start.history')
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        to_date = inventory.to_date
        base_folder = inventory.base_folder

        # Product management:
        product_db = self.get_product_db(base_folder)

        pickle_file = os.path.join(
            base_folder, 'pickle', '%s.pickle' % 'Finale')
        excel_file = os.path.join(
            base_folder, 'excel', 'ODOO_Finale.xlsx')

        product_ids = product_pool.search(
            cr, uid, [
                ('mx_start_date', '=', to_date),
            ], context=context)

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = 'Stato finale'
        excel_pool.create_worksheet(name=ws_name)
        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            15, 15, 40, 35, 10,
            10, 12, 30]
        excel_pool.column_width(ws_name, width)

        header = [
            'ID', 'Codice', 'Nome', 'Categoria', 'Ricodifica',
            'Q.', 'Prezzo inventario', 'Stato',
        ]
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        jump = False
        pickle_data = []
        for line in product_pool.browse(cr, uid, product_ids, context=context):
            product = line.product_id
            product_id = product.id
            default_code = product.default_code or ''
            real_code = default_code
            name = product.name
            qty = line.mx_start_qty
            if product.inventory_category_id:
                category = product.inventory_category_id.name
            else:
                category = ''

            status = 'Usato'
            if not default_code:
                pickle_data = u'Prodotto non usato %s' % name
                jump = True

            if default_code[:4] in pipe_codes:
                # Clean pipe:
                default_code = pipe_codes[default_code[:4]]
                product_id = ''
            elif default_code[:2] in ('PO', 'MS', 'MT', 'TL', 'TS'):
                # Clean HW packed:
                default_code = default_code[:8].strip()
                product_id = ''
            elif category == 'Prodotti finiti':
                # Final product packed:
                if not default_code[:3].isdigit():
                    default_code = default_code[:6].strip()
                    product_id = ''
            elif category in ('Esclusi', 'Lavorazioni'):
                # Remove category:
                status = 'Categoria non in inventario: %s' % category
                jump = True

            if qty <= 0:
                status = 'Senza esistenza'
                jump = True

            # Write line in Excel:
            excel_line = [
                product_id, real_code, name, category,
                default_code, qty, 0, status,
            ]
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_line,
                default_format=excel_format['white']['text'])

            if jump:
                continue

            # Save in pickle only used data:
            pickle_data.append({
                'product_id': product_id,
                'name': name,
                'category': category,
                'qty': qty,
                'default_code': real_code,
                'compress_code': default_code,
                'status': status,
            })
            self.product_db_update(product_db, product_id, qty, 'Finale')

        pickle.dump(pickle_data, open(pickle_file, 'wb'))
        excel_pool.save_file_as(excel_file)
        self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_end': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }, context=context)

    def button_inventory(self, cr, uid, ids, context=None):
        """ Extract final status
        """
        product_pool = self.pool.get('product.product.start.history')
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder

        # Product management:
        start_db = self.get_product_db(base_folder, 'start')
        inventory_db = self.get_product_db(base_folder, 'final_inventory')

        excel_file = os.path.join(
            base_folder, 'excel', 'Finale.xlsx')

        # ---------------------------------------------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = 'Inventario'
        excel_pool.create_worksheet(name=ws_name)
        excel_format = self.get_excel_format(excel_pool)

        # Start writing in the sheet:
        width = [
            5, 12,
            10, 10, 30, 5,

            25, 35, 10, 10, 15,
            15, 15, 40,
        ]
        excel_pool.column_width(ws_name, width)

        # Write header:
        header = [
            'Nuovo', 'Codice',
            'Q. iniz.', 'Prezzo iniz.', 'Nome', 'UM',
            ]
        old_col = len(header)
        header.extend([
            'Modo', 'Categoria', 'Carico', 'Scarico', 'Prezzo',
            'Inventario', 'Valore',
            'Differenza',
            ])
        empty = ['' for i in range(len(header) - old_col)]

        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        # Old present:
        for default_code in sorted(start_db):
            previous = start_db[default_code]
            next = inventory_db.get(default_code)
            start_qty = previous['qty_start'] or 0.0
            excel_line = [
                '',
                default_code,
                start_qty,
                previous['price_start'],
                previous['name'],
                previous['uom'],
                ]
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_line,
                default_format=excel_format['white']['text'])

            if next:
                load_qty = next[2]
                unload_qty = next[3]
                end_qty = start_qty + load_qty - unload_qty
                price = next[4]
                excel_line_new = [
                    next[0],  # mode
                    next[1],  # category
                    load_qty,
                    unload_qty,
                    price,
                    end_qty,
                    price * end_qty,

                    '',  # todo write difference
                ]
                excel_pool.write_xls_line(
                    ws_name, row, excel_line_new,
                    default_format=excel_format['white']['text'], col=old_col)
            else:
                excel_pool.write_xls_line(
                    ws_name, row, empty,
                    default_format=excel_format['red']['text'], col=old_col)

        # New not present:
        for default_code in sorted(inventory_db):
            if default_code in start_db:
                continue  # yet present
            next = inventory_db[default_code]
            start_qty = 0.0
            excel_line = [
                'X',
                default_code,
                start_qty,
                0,
                '',
                '',
                ]
            load_qty = next[2]
            unload_qty = next[3]
            end_qty = start_qty + load_qty - unload_qty
            price = next[4]
            excel_line_new = [
                next[0],  # mode
                next[1],  # category
                load_qty,
                unload_qty,
                price,  # price

                end_qty,
                price * end_qty,

                '',  # todo write difference
            ]

            row += 1
            excel_pool.write_xls_line(
                ws_name, row, excel_line,
                default_format=excel_format['red']['text'])

            excel_pool.write_xls_line(
                ws_name, row, excel_line_new,
                default_format=excel_format['white']['text'], col=old_col)

        excel_pool.save_file_as(excel_file)
        return True

    _columns = {
        'start_filename': fields.char(
            'File inizio anno', size=180, required=True),
        'row_start': fields.integer('Riga inizio'),
        'name': fields.char('Anno', size=64, required=True),
        'base_folder': fields.char(
            'Cartella base', size=180,
            help='Cartella dove sono memorizzati tutti i file della gestione'),
        'from_date': fields.date('Dalla data', required=True),
        'to_date': fields.date('Alla data', required=True),

        'done_invoice': fields.datetime('Fatturato esportato'),
        'done_mrp': fields.datetime('Produzioni esportate'),
        'done_job': fields.datetime('Lavorazioni esportate'),
        'done_picking': fields.datetime('Picking CL SL esportati'),
        'done_purchase': fields.datetime('Acquisti esportati'),
        'done_start': fields.datetime('Stato iniziale esportato'),
        'done_end': fields.datetime('Stato finale esportato'),

        'cl_id': fields.many2one('stock.picking.type', 'CL', required=True),
        'sl_id': fields.many2one('stock.picking.type', 'SL', required=True),
        'purchase_id': fields.many2one(
            'stock.picking.type', 'Acquisti', required=True),
    }


