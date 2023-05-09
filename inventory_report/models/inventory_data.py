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
excluded_category = ('Esclusi', 'Lavorazioni')

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

semiproduct_code = [
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
        default_code = default_code or ''
        default_code = default_code.replace('NON USARE ', '').strip()
        default_code = default_code.replace('/', '-')
        return default_code

    def generate_folder_structure(
            self, cr, uid, root_path=False, context=None):
        """ Generate folder structure
        """
        if not root_path:
            root_path = '~/inventory'

        # Create folder structure
        # base_folder = os.path.join(root_path, year)
        base_folder = os.path.expanduser(root_path)
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

    def button_extract_all(self, cr, uid, ids, context=None):
        """ Extract all
        """
        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        # from_date = inventory.from_date
        # to_date = inventory.to_date
        base_folder = inventory.base_folder

        # todo Clean Pickle folder
        path = os.path.join(base_folder, 'pickle')
        # clean = os.system('rm %s/*.pickle' % path)

        # todo Clean Excel folder
        path = os.path.join(base_folder, 'excel')
        # clean = os.system('rm %s/*.xlsx' % path)

        # ---------------------------------------------------------------------
        #                          Export Document:
        # ---------------------------------------------------------------------
        # Invoice:
        self.button_extract_invoice(cr, uid, ids, context=context)
        _logger.info(  # done_date
            'Generate: [Fatture.pickle NC.pickle] [Invoice.xlsx NC.xlsx]\n'
            'Generate total: product.pickle')

        # Production MRP:
        self.button_extract_mrp(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: [MRP.pickle] [MRP.xlsx: MRP, Componenti]\n'
            'Generate total: product.pickle')

        # Production Job:
        self.button_extract_job(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: [Semilavorati.pickle] [Semilavorati.xlsx: '
            '    Semilavorati, Materie prime]\n'
            'Generate total: product.pickle')

        # Picking (CL, SL):
        self.button_extract_picking(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: [Correzioni.pickle] [Correzioni.xlsx: CL, SL]\n'
            'Generate total: product.pickle')

        # Purchase:
        self.button_extract_purchase(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: [Acquisti.pickle] [Acquisti.xlsx: CL, SL]\n'
            'Generate total: product.pickle')

        # ---------------------------------------------------------------------
        #                          Export Price:
        # ---------------------------------------------------------------------
        # Product price:
        self.button_extract_raw_material_price(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: '
            '    [raw_price.pickle, raw_price_now.pickle] '
            '    [PrezziMP.xlsx: Periodo, Attuali]')

        # Semiproduct price:
        self.button_extract_semiproduct_price(cr, uid, ids, context=context)
        _logger.info(  #
            'Input: raw_price.pickle, raw_price_now.pickle'
            'Output: '
            '    [semiproduct.pickle] '
            '    [Prezzi_semilavorati.xlsx]\n')

        # Product price:
        self.button_extract_product_price(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: '
            '    [product_template.pickle] '
            '    [MRP_Prodotti.xlsx]')

        # ---------------------------------------------------------------------
        # Inventory status:
        # ---------------------------------------------------------------------
        # Excel last year end inventory (manually):
        self.button_extract_begin(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: '
            '    [start.pickle] ')

        # ODOO end of period inventory (for check totals):
        # todo check procedure!
        self.button_extract_final(cr, uid, ids, context=context)
        _logger.info(
            'Generate: ')

        # Export product list:
        self.button_extract_product_move(cr, uid, ids, context=context)
        _logger.info(
            'Input: '
            '    [raw_price.pickle] '
            '    [semiproduct.pickle] '
            '    [product_mrp.final_inventory] '
            ' '
            '     Prodotti.xlsx'
            'Output: '
            '    [final_inventory.pickle]'
        )

        # ---------------------------------------------------------------------
        #                             Inventory:
        # ---------------------------------------------------------------------
        # Excel last year end inventory (manually):
        self.button_inventory(cr, uid, ids, context=context)
        _logger.info(  #
            'Generate: '
            '    [start.pickle] ')


    def button_update_product_price(self, cr, uid, ids, context=None):
        """ Update price from MRP
        """
        product_pool = self.pool.get('product.product')

        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder
        file_in = os.path.join(base_folder, 'excel', 'MRP_Prodotti.xlsx')

        # ---------------------------------------------------------------------
        # Load origin name from XLS
        # ---------------------------------------------------------------------
        try:
            wb = xlrd.open_workbook(file_in)
        except:
            raise osv.except_osv(
                _('No file:'),
                _('[ERROR] Cannot read XLS file: %s' % file_in))

        # Code | Name | UOM | QTY | SUBTOTAL
        # 3 pages
        ws = wb.sheet_by_index(0)
        row_start = 1
        product_price = {}
        for row in range(row_start - 1, ws.nrows):
            default_code = str(ws.cell(row, 0).value) or ''
            if default_code.endswith('.0'):
                default_code = default_code[:-2]
            default_code = self.clean_code(default_code)
            price = ws.cell(row, 2).value
            product_price[default_code] = price

        pdb.set_trace()
        for mask in sorted(product_price):
            price = product_price[mask]
            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=ilike', '%s%%' % mask),
            ], context=context)
            if product_ids:
                _logger.info('Update %s with %s # %s' % (
                    mask, price, len(product_ids)))
                product_pool.write(cr, uid, product_ids, {
                    'standard_price': price,
                }, context=context)
            else:
                _logger.warning('Not found %s' % mask)

        return True

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

        # Call original data structure used in report:
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
        self.save_product_db(base_folder, mrp_data, 'product_template')
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
        price_db = self.get_product_db(base_folder, 'raw_price')  # Raw
        price_now_db = self.get_product_db(base_folder, 'raw_price_now')
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
            default_code = self.clean_code(product.default_code)
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
                component_code = self.clean_code(component.default_code)
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
        price_db = self.get_product_db(base_folder, 'raw_price')  # For price
        semiproduct_db = self.get_product_db(base_folder, 'semiproduct')
        mrp_db = self.get_product_db(base_folder, 'product_mrp')
        check_db = self.get_product_db(base_folder, 'check_final')

        final_db = {}  # Pack per code for final report

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

                # Recoded Normal product:
                if default_code[:3].isdigit():
                    new_code = default_code[:6].strip()

                # Recoded Semiproduct:
                elif not default_code[:2].isdigit() and \
                        default_code[2:5].isdigit():
                    new_code = default_code[:8].strip()

                # Price from template:
                code6 = default_code[:6].strip()
                price = mrp_db.get(code6, product.standard_price)

            elif hw_bom:
                mode = 'Semilavorato'

                # Recoded:
                if default_code[:2] in semiproduct_code and \
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
                inventory_code = new_code or default_code
                check_qty = check_db.get(product_id, 0.0)
                if inventory_code in final_db:
                    final_db[inventory_code][2] += total_load
                    final_db[inventory_code][3] += total_unload
                    if not final_db[inventory_code][3]:
                        final_db[inventory_code][3] = price
                        # todo check if different?
                    final_db[inventory_code][5] += check_qty
                else:
                    final_db[inventory_code] = [
                        mode,
                        category,
                        total_load,
                        total_unload,
                        price,
                        check_qty,
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

        base_folder = self.generate_folder_structure(
            cr, uid, inventory.base_folder, context=context)

        # Product management:
        product_db = self.get_product_db(base_folder)  # product.pickle file

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
        # Sheet 1:
        ws_name = setup
        excel_pool.create_worksheet(name=ws_name)

        # Sheet 2:
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

        # Code | Name | UOM | QTY | SUBTOTAL
        # 3 pages
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

    def button_extract_raw_material_price(self, cr, uid, ids, context=None):
        """ Extract product price
        """
        price_pool = self.pool.get('pricelist.partnerinfo.history')
        excel_pool = self.pool.get('excel.writer')

        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder
        to_date = inventory.to_date

        excel_file = os.path.join(
            base_folder, 'excel', 'PrezziMP.xlsx')
        loops = [
            [{}, [
                ('date_quotation', '<=', to_date),
            ], 'raw_price', 'Periodo'],
            [{}, [], 'raw_price_now', 'Attuali'],
        ]
        excel_format = False
        # ---------------------------------------------------------------------
        #                         Excel export:
        # ---------------------------------------------------------------------
        for data, domain, pickle_name, ws_name in loops:
            excel_pool.create_worksheet(name=ws_name)
            if not excel_format:
                excel_format = self.get_excel_format(excel_pool)

            # Start writing in the sheet:
            width = [
                5, 15, 40, 25, 10, 5,
                ]
            excel_pool.column_width(ws_name, width)
            header = [
                'ID', 'Codice', 'Nome', 'Data', 'Prezzo', 'Uso std',
            ]
            row = 0
            excel_pool.write_xls_line(
                ws_name, row, header, default_format=excel_format['header'])

            price_ids = price_pool.search(cr, uid, domain, context=context)
            prices = price_pool.browse(cr, uid, price_ids, context=context)
            for price in sorted(
                    prices, key=lambda x: x.date_quotation or x.create_date,
                    reverse=True,
                    ):
                product = price.product_id
                product_id = product.id
                default_code = self.clean_code(product.default_code)
                date = price.date_quotation
                last_price = price.price

                if product_id in data:
                    continue  # yet present
                data[product_id] = last_price

                row += 1
                excel_pool.write_xls_line(
                    ws_name, row, [
                        product.id,
                        default_code,
                        product.name,
                        date,
                        last_price,
                        ''
                    ],
                    default_format=excel_format['white']['text'])

            self.save_product_db(base_folder, data, pickle_name)
        excel_pool.save_file_as(excel_file)

    def button_extract_final(self, cr, uid, ids, context=None):
        """ Extract final status for check
        """
        product_pool = self.pool.get('product.product.start.history')
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        to_date = inventory.to_date
        base_folder = inventory.base_folder

        # Product management:
        # product_db = self.get_product_db(base_folder)

        pickle_file = os.path.join(
            base_folder, 'pickle', 'check_final.pickle')
        excel_file = os.path.join(
            base_folder, 'excel', 'Check_Finale.xlsx')

        product_ids = product_pool.search(
            cr, uid, [
                ('mx_start_date', '=', to_date),
            ], context=context)
        _logger.info('Found %s product' % len(product_ids))

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
        check_data_pickle = {}
        for line in product_pool.browse(cr, uid, product_ids, context=context):
            product = line.product_id
            product_id = product.id
            default_code = self.clean_code(product.default_code)
            real_code = default_code
            name = product.name
            qty = line.mx_start_qty
            if product.inventory_category_id:
                category = product.inventory_category_id.name
            else:
                category = ''

            status = 'Usato'
            jump = False
            if not default_code:
                # pickle_data = u'Prodotto non usato %s' % name
                jump = True

            if default_code[:4] in pipe_codes:
                # Clean pipe:
                default_code = pipe_codes[default_code[:4]]
                product_id = ''
            elif default_code[:2] in semiproduct_code:
                # Clean HW packed:
                default_code = default_code[:8].strip()
                product_id = ''
            elif category == 'Prodotti finiti':
                # Final product packed:
                if not default_code[:3].isdigit():
                    default_code = default_code[:6].strip()
                    product_id = ''
            elif category in excluded_category:
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
            if qty <= 0:
                excel_color = excel_format['red']
            else:
                excel_color = excel_format['white']
            excel_pool.write_xls_line(
                ws_name, row, excel_line,
                default_format=excel_color['text'])
            if jump:
                continue

            # Save in pickle only used data:
            check_data_pickle[product_id] = qty

            # {
            #    'product_id': product_id,
            #    'name': name,
            #    'category': category,
            #    'qty': qty,
            #    'default_code': real_code,
            #    'compress_code': default_code,
            #    'status': status,
            # })
            # self.product_db_update(product_db, product_id, qty, 'Finale')

        pickle.dump(check_data_pickle, open(pickle_file, 'wb'))
        excel_pool.save_file_as(excel_file)
        # self.save_product_db(base_folder, product_db)
        return self.write(cr, uid, ids, {
            'done_end': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        }, context=context)

    def button_inventory(self, cr, uid, ids, context=None):
        """ Extract final status
        """
        excel_pool = self.pool.get('excel.writer')

        # Read parameters:
        inventory = self.browse(cr, uid, ids, context=context)[0]
        base_folder = inventory.base_folder

        # Product management:
        start_db = self.get_product_db(base_folder, 'start')
        # From product report packed data:
        inventory_db = self.get_product_db(base_folder, 'final_inventory')
        # todo not here:
        #  check_db = self.get_product_db(base_folder, 'check_final')

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
            15, 15, 15, 40,
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
            'Inv. ODOO', 'Inventario', 'Valore',
            'Errore',
            ])
        empty = ['' for i in range(len(header) - old_col)]

        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=excel_format['header'])

        # Old present:
        for default_code in sorted(start_db):
            error = ''
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
                end_qty = start_qty + load_qty + unload_qty
                price = next[4]

                if end_qty < 0:
                    error += '[NEGATIVO] '
                if price <= 0.0:
                    error += '[PREZZO A ZERO] '

                excel_line_new = [
                    next[0],  # mode
                    next[1],  # category
                    load_qty,
                    unload_qty,
                    price,
                    next[5],  # Final from ODOO
                    end_qty,
                    price * end_qty,

                    error,
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
            error = ''
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
            end_qty = start_qty + load_qty + unload_qty
            price = next[4]

            if end_qty < 0.0:
                error += '[NEGATIVO] '
            if price <= 0.0:
                error += '[PREZZO A ZERO] '

            excel_line_new = [
                next[0],  # mode
                next[1],  # category
                load_qty,
                unload_qty,
                price,  # price

                next[5],  # Final from ODOO
                end_qty,
                price * end_qty,

                error,  # todo write difference
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


