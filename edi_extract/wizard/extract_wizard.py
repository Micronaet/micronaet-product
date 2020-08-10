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


class EdiProductProductExtractWizard(orm.TransientModel):
    """ Wizard for edi product extract wizard
    """
    _name = 'edi.product.product.extract.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_extract(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        # Parameters:
        langs = ['it_IT', 'en_US']
        if context is None:
            context = {}

        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')

        # wizard_browse = self.browse(cr, uid, ids, context=context)[0]

        # Search product:
        product_ids = product_pool.search(cr, uid, [], context=context)

        # Excel:
        header = [
            'Code',
            'Name',
            '',
        ]
        width = [
            10,
            30,
        ]

        ws_name = _('EDI Product')
        row = 0
        excel_pool.create_worksheet(ws_name)
        excel_pool.write_xls_line(ws_name, row, header)
        excel_pool.column_width(ws_name, width)

        for lang in langs:
            record = False
            for product in product_pool.browse(
                    cr, uid, product_ids, context=context):
                row += 1
                excel_pool.write_xls_line(ws_name, row, header)

        return excel_pool.return_attachment(
            cr, uid, 'EDI product', 'product.xlsx', context=context)

    _columns = {
        # TODO inventory category?
        }


