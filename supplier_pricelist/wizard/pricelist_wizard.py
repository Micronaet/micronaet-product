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


class ProductProductExtractWizard(orm.TransientModel):
    """ Product product extract wizard
    """
    _name = 'product.product.extract.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_export(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        if context is None:
            context = {}

        wiz_browse = self.browse(cr, uid, ids, context=context)[0]
        partner = wiz_browse.partner_id
        partner_id = partner.id
        from_date = wiz_browse.from_date
        to_date = wiz_browse.to_date

        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        pricelist_pool = self.pool.get('pricelist.partnerinfo')
        product_pool = self.pool.get('product.product')

        # ---------------------------------------------------------------------
        # Product selection
        # ---------------------------------------------------------------------
        domain = [
            ('suppinfo_id.name', '=', partner_id),
            ]
        filter_text = 'Listino fornitore: %s' % partner.name

        if from_date:
            domain.append(('date_quotation', '>=', from_date))
            filter_text = '; dalla data: %s' % from_date
        if to_date:
            domain.append(('date_quotation', '<=', to_date))
            filter_text = '; alla data: %s' % to_date

        pricelist_ids = pricelist_pool.search(
            cr, uid, domain, context=context)
        pricelist_proxy = pricelist_pool.browse(
            cr, uid, pricelist_ids, context=context)

        # --------------------------------------1-------------------------------
        #                          Excel export:
        # ---------------------------------------------------------------------
        ws_name = u'Listino'
        header = [
            'Codice nostro', 'Nome nostro', 'UM',

            'Codice forn.', 'Nome forn.',
            'Cons. gg.', 'Q. min.',

            'Taglio', 'Prezzo',
            'Data prezzo', 'Aggiornato il',
            ]

        width = [
            15, 40, 5,
            15, 40,
            7, 7,
            5, 10,
            10, 20,
            ]

        ws = excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, width)
        title = filter_text

        # ---------------------------------------------------------------------
        # Generate format used:
        # ---------------------------------------------------------------------
        excel_pool.set_format(number_format='#,##0.####0')
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

        # ---------------------------------------------------------------------
        # Detail line
        # ---------------------------------------------------------------------
        record_list = []
        product_db = {}
        for line in pricelist_proxy:
            template = line.suppinfo_id.product_tmpl_id
            template_id = template.id
            suppinfo = line.suppinfo_id

            if template_id not in product_db:
                product_ids = product_pool.search(cr, uid, [
                    ('product_tmpl_id', '=', template_id),
                    ], context=context)
                if product_ids:
                    product_proxy = product_pool.browse(
                        cr, uid, product_ids, context=context)[0]
                    product_db[template_id] = product_proxy.default_code or ''
                else:
                    product_db[template_id] = product_proxy.default_code or '?'

            record_list.append([
                product_db[template_id],
                template.name or '',
                template.uom_id.name or '',

                suppinfo.product_code or '',
                suppinfo.product_name or '',
                suppinfo.delay or '',
                suppinfo.min_qty or '',

                line.min_quantity or '',
                (line.price or 0.0, f_number),
                line.date_quotation or '',
                line.write_date or '',
                ])

        for record in sorted(record_list):
            row += 1
            excel_pool.write_xls_line(
                ws_name, row, record, default_format=f_text)

        return excel_pool.return_attachment(cr, uid, _('Listino fornitore'))

    _columns = {
        'partner_id': fields.many2one(
            'res.partner', 'Supplier', required=True),
        'from_date': fields.date('From date'),
        'to_date': fields.date('To date'),
        }
