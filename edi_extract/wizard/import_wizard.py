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


import pdb
import logging
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from openerp.tools.translate import _
import xlrd
import base64
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)

_logger = logging.getLogger(__name__)


class EdiProductProductImportWizard(orm.TransientModel):
    """ Wizard for edi product extract wizard
    """
    _name = 'edi.product.product.import.wizard'

    def action_import_edi_update(self, cr, uid, ids, context=None):
        """ Update product data from Excel file
        """
        # Internal function:
        def read_all_line(ws, row, mask_mode=False, mask_default=False):
            """ Real all line from WS selected
            """
            line = []
            for col in range(ws.ncols):
                data = ws.cell(row, col).value.upper()
                if mask_mode:
                    line.append((data and data in 'XS') or mask_default)
                else:
                    line.append(data)
            return line

        def extract_data_lang_line(ws, row, mask):
            """ Extract data from row with mask
                @return dict with data setup
            """
            product_pool = self.pool.get('product.product')
            data_lang = {}
            for col in range(ws.ncols):
                # Check read from mask
                try:
                    if not mask[col]:  # jump cell
                        continue
                except:
                    # Cell not present (mask short than row)
                    continue

                # A. Manage field:
                field_name, data_type, lang = \
                    product_pool._edi_field_parameter[col]
                if field_name == 'default_code':
                    # Never write default_code (always correct)
                    continue

                # B. Manage lang:
                if lang not in data_lang:
                    data_lang[lang] = {}

                # C. Manage data:
                data = ws.cell(row, col).value
                if data_type in ('char', 'text', 'float'):  # as is
                    pass  #
                elif data_type in ('boolean'):
                    data = (data and data in 'YS')
                elif data_type in ('integer'):  # TODO check
                    data = int(ws.cell(row, col).value)
                elif data_type in ('many2one'):  # TODO
                    data = int(ws.cell(row, col).value)
                # TODO Date, Datetime
                else:  # Not used
                    _logger.warning('Mapped field not used: %s' % field_name)

                data_lang[lang][field_name] = data
            return data_lang

        if context is None:
            context = {}

        # Pool used:
        product_pool = self.pool.get('product.product')
        wizard = self.browse(cr, uid, ids, context=context)[0]

        # ---------------------------------------------------------------------
        # Save file passed:
        # ---------------------------------------------------------------------
        if not wizard.filename:
            raise osv.except_osv(
                _('No file:'),
                _('Please pass a XLSX file for import EDI product'),
                )

        b64_file = base64.decodestring(wizard.filename)
        now = datetime.now().strftime(
            DEFAULT_SERVER_DATETIME_FORMAT).replace(
            ':', '_').replace('-', '_')
        filename = '/tmp/edi_import_wizard_%s.xlsx' % now
        f = open(filename, 'wb')
        f.write(b64_file)
        f.close()

        # ---------------------------------------------------------------------
        # Load force name (for web publish)
        # ---------------------------------------------------------------------
        product_pool.load_edi_parameter(cr, uid, context=context)
        field_mapping = product_pool._edi_field_parameter

        row_start = 0
        try:
            wb = xlrd.open_workbook(filename)
        except:
            raise osv.except_osv(
                _('Error XLSX'),
                _('Cannot read XLS file: %s' % filename),
                )

        # ---------------------------------------------------------------------
        # Loop on all pages:
        # ---------------------------------------------------------------------
        # today = now[:10]
        ws = wb.sheet_by_index(0)
        pos = 0
        error = ''
        mask_line = False
        mask_default = False
        selected_ids = []
        for row in range(row_start, ws.nrows):
            pos += 1
            default_code = ws.cell(row, 0).value
            if not default_code:
                _logger.warning('Jump empyt line %s' % default_code)
                continue

            if pos == 1:
                if default_code.lower() in ('tutte', 'tutto', 'all'):
                    mask_default = True
                elif default_code not in 'xXSs':
                    raise osv.except_osv(
                        _('Errore riga maschera'),
                        _('Il file per essere improtato deve aver come prima'
                          'riga la maschera code indicare le colonne da '
                          'utilizzare, la prima deve sempre essere marcata con'
                          'x, X, s o S!'),
                    )

                mask_line = read_all_line(
                    ws, row, mask_mode=True, mask_default=mask_default)
                continue
            elif pos == 2:
                continue   # Header line

            # Key field:
            if not default_code:
                _logger.error('No product code')
                error += 'Riga: %s > No codice prodotto\n' % row
                continue

            # Search product:
            product_ids = product_pool.search(cr, uid, [
                ('default_code', '=', default_code)
                ], context=context)

            # Manage product error:
            if not product_ids:
                _logger.error(
                    'No product with passed code: %s' % default_code)
                # FATAL ERROR (maybe file not in correct format, raise:
                '''raise osv.except_osv(
                    _('Errore controllare anche il formato del file'),
                    _('Non trovato il codice prodotto: %s' % (
                        default_code)),
                    )'''
                continue

            # TODO manage warning more than one product
            elif len(product_ids) > 1:
                _logger.error('More material code: %s' % default_code)
                error += 'Riga: %s > Codice doppio: %s\n' % (
                    row, default_code)
                pass  # TODO multi code

            product_id = product_ids[0]

            # Lang loop for write data records:
            context_lang = context.copy()
            data_lang = extract_data_lang_line(ws, row, mask_line)
            for lang in data_lang:
                context_lang['lang'] = lang
                product_pool.write(
                    cr, uid, [product_id],
                    data_lang[lang],
                    context=context_lang)
            selected_ids.append(product_id)
            _logger.info('Update code: %s' % default_code)

        # Return product updated:
        model_pool = self.pool.get('ir.model.data')
        tree_view_id = False
        form_view_id = model_pool.get_object_reference(
            cr, uid,
            'edi_extract', 'view_product_product_edi_form')[1]

        return {
            'type': 'ir.actions.act_window',
            'name': _('Prodotti aggiornati'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            # 'res_id': 1,
            'res_model': 'product.product',
            'view_id': tree_view_id,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'domain': [('id', 'in', selected_ids)],
            'context': context,
            'target': 'current',
            'nodestroy': False,
            }

    _columns = {
        'filename': fields.binary('XLSX file', filters=None),
    }
