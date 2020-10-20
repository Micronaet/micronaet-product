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

    def load_edi_parameter(self, cr, uid, context=None):
        """ Load EDI parameter for import (done once if present)
        """
        try:
            return self._edi_field_parameter
        except:
            pdb.set_trace()
            # Create parameter once:
            product_pool = self.pool.get('product.product')
            self._edi_field_parameter = {}
            for field_name in self._edi_field_parameter:
                if type(field_name) == list:
                    field_name = field_name[0]
                    langs = product_pool._edi_lang
                else:
                    langs = ['it_IT']
                for lang in langs:
                    field = product_pool._columns[field_name]
                    self._edi_field_parameter[field] = [
                        field_name,
                        lang,
                        field.type,
                    ]

    def action_import_edi_update(self, cr, uid, ids, context=None):
        """ Update product data from Excel file
        """
        if context is None:
            context = {}

        # Pool used:
        product_pool = self.pool.get('product.product')
        wizard = self.browse(cr, uid, ids, context=context)[0]

        # ---------------------------------------------------------------------
        # Save file passed:
        # ---------------------------------------------------------------------
        if not wizard.file:
            raise osv.except_osv(
                _('No file:'),
                _('Please pass a XLSX file for import EDI product'),
                )

        b64_file = base64.decodestring(wizard.file)
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
        for row in range(row_start, ws.nrows):
            pos += 1
            if pos == 1:
                # ---------------------------------------------------------
                # Read product code:
                # ---------------------------------------------------------
                default_code = ws.cell(row, 0).value
                _logger.info('Find material: %s' % default_code)

                # Manage code error:
                if not default_code:
                    _logger.error('No material code')
                    error += 'Riga: %s > No codice materiale\n' % row
                    continue

                # Search product:
                product_ids = product_pool.search(cr, uid, [
                    ('default_code', '=', default_code)
                    ], context=context)

                # Manage product error:
                if not product_ids:
                    _logger.error(
                        'No product with code: %s' % default_code)
                    # FATAL ERROR (maybe file not in correct format, raise:
                    raise osv.except_osv(
                        _('Errore controllare anche il formato del file'),
                        _('Non trovato il codice prodotto: %s' % (
                            default_code)),
                        )

                # TODO manage warning more than one product
                elif len(product_ids) > 1:
                    _logger.error('More material code: %s' % default_code)
                    error += 'Riga: %s > Codice doppio: %s\n' % (
                        row, default_code)
                    pass # TODO multi code

                product_id = product_ids[0]
                product_proxy = product_pool.browse(
                    cr, uid, product_id, context=context)

    _columns = {
        'filename': fields.binary('XLSX file', filters=None),
    }
