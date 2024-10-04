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

import logging
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)

# This module code:
edi_code = '1'


class EDIPartner(orm.Model):
    """ EDI Partner
    """
    _inherit = 'edi.partner'

    # -------------------------------------------------------------------------
    # Override method for export Order confirm:
    # -------------------------------------------------------------------------
    '''
    def EDI_quotation(self, cr, uid, ids, context=None):
        """ Export Order for partner Company 1
        """
        if context is None:
            context = {}
        document_id = context['document_id']

        document = self.browse(cr, uid, document_id, context=context)
        partner = document.partner_id
        edi_partner = partner.edi_partner_id
        if edi_partner.code != edi_code:
            return super(EDIPartner, self).EDI_quotation(
                cr, uid, ids, context=context)

        _logger.info('START EDI Quotation Order company 1')
        # Note: No Quotation management for this EDI
        return True
    '''

    # -------------------------------------------------------------------------
    # Override method for export Order confirm:
    # -------------------------------------------------------------------------
    def EDI_order(self, cr, uid, ids, context=None):
        """ Export Order for partner Company 1
        """
        if context is None:
            context = {}
        document_id = context['document_id']

        document = self.browse(cr, uid, document_id, context=context)
        partner = document.partner_id
        edi_partner = partner.edi_partner_id

        if edi_partner.code != edi_code:
            return super(EDIPartner, self).EDI_quotation(
                cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # Procedure for this Company
        # ---------------------------------------------------------------------
        _logger.info('START EDI Confirm Order company 1')

        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        ws_name = 'Conferma ordine'
        header = []
        width = [40, ]

        excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, width)

        # Format
        f_text = excel_pool.get_format(key='text')
        f_number = excel_pool.get_format(key='number')

        row = 0
        line = ['Prova']
        excel_pool.write_xls_line(
            ws_name, row, line, default_format=f_text)
        return True

    # -------------------------------------------------------------------------
    # Override method for export Invoice:
    # -------------------------------------------------------------------------
    def EDI_invoice(self, cr, uid, ids, context=None):
        """ Export Order for partner Company 1
        """
        if context is None:
            context = {}
        document_id = context['document_id']

        document = self.browse(cr, uid, document_id, context=context)
        partner = document.partner_id
        edi_partner = partner.edi_partner_id

        if edi_partner.code != edi_code:
            return super(EDIPartner, self).EDI_quotation(
                cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # Procedure for this Company
        # ---------------------------------------------------------------------
        _logger.info('START EDI Confirm Order company 1')

        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        return True
