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
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        order_pool = self.pool.get('sale.order')

        if context is None:
            context = {}
        document_id = context['document_id']

        document = order_pool.browse(cr, uid, document_id, context=context)
        partner = document.partner_id
        edi_partner = partner.edi_partner_id

        if edi_partner.code != edi_code:
            return super(EDIPartner, self).EDI_quotation(
                cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # Procedure for this Company
        # ---------------------------------------------------------------------
        _logger.info('START EDI Confirm Order company 1')

        ws_name = 'Conferma ordine'
        header = [
            'RecordType',
            'H-Partita IVA Fornitore',
            'H-Dest. Codice Punto Vendita',
            'RecordID',
            'H-Nr. Documento',
            'H-Data Documento',
            'H-Nazione Fornitore',
            'H-CF Fornitore',
            'H-Partita IVA Cliente',
            'H-NazioneCliente',
            'H-CF Cliente',
            'H-Dest. Indirizzo',
            'H-Dest. Città',
            'H-Dest. Data Cons. Prevista',
            'H-Nr. Ordine GT',
            'H-Data Ordine GT',
            'H-Nr. Ordine Fornitore',
            'H-Metodo di Pagamento',
            'H-Condizioni di Pagamento',
            'H-IBAN Pagamento',
            'H-Nr. Fornitore Origine',
            'H-Percentuale Commissione',
            'H-Costo Commissioni',
            'H-Costo Trasporto',
            'H-Costo Etichettatura',
            'H-Costo Imballi',
            'H-Nr. Carrelli CC',
            'H-Nr. Carrello c/Placca',
            'H-Nr. Carrelli senza Placca',
            'H-Nr. Pianali',
            'H-Nr. Prolunghe Corte',
            'H-Nr. Prolunghe Lunghe',
            'H-Nr. Colli',
            'H-Nr. Pallet EPAL',
            'H-Nr. Pallet a Perdere',
            'H-Nome Corriere Incaricato',
            'H-Stato',
            'L-Posizione',
            'L-EAN',
            'L-Nr. Articolo Fornitore',
            'L-Nr. Articolo Interno',
            'L-Descrizione',
            'L-Quantità',
            'L-Unità di Misura',
            'L-Quantità UdM',
            'L-Costo Lordo',
            'L-IVA %',
            'L-Sconto 1%',
            'L-Sconto 2%',
            'L-Sconto 3%',
            'L-Sconto 4%',
            'L-Sconto 5%',
            'L-Sconto Promo 1%',
            'L-Sconto Promo 2%',
            'L-Sconto Promo 3%',
            'L-Sconto Promo 4%',
            'L-Sconto Promo 5%',
            'L-Importo Riga',
            'L-Prezzo Etichette',
            'L-Quantità Etichette',
            'L-Intra Cod. Tariffa',
            'L-Intra Peso Lordo',
            'L-Intra Peso Netto',
            'L-Intra Numero Colli',
            'L-Passp. Nr. RUOP',
            'L-Passp. Lotto',
            'L-Quantità per Kit',
            'L-Ean Padre',
            'L-Codice Famiglia',
        ]
        width = [5, 10]

        excel_pool.create_worksheet(name=ws_name)
        excel_pool.column_width(ws_name, width)

        # Format
        f_header = excel_pool.get_format(key='header')
        f_text = excel_pool.get_format(key='text')
        f_number = excel_pool.get_format(key='number')

        # ---------------------------------------------------------------------
        # A. Header line:
        # ---------------------------------------------------------------------
        row = 0
        excel_pool.write_xls_line(
            ws_name, row, header, default_format=f_header)

        # ---------------------------------------------------------------------
        # B. Data lines:
        # ---------------------------------------------------------------------
        row += 1
        line = ['Prova']
        excel_pool.write_xls_line(
            ws_name, row, line, default_format=f_text)

        return excel_pool.return_attachment(
            cr, uid, 'Order confirm')

    # -------------------------------------------------------------------------
    # Override method for export Invoice:
    # -------------------------------------------------------------------------
    def EDI_invoice(self, cr, uid, ids, context=None):
        """ Export Order for partner Company 1
        """
        # Pool used:
        excel_pool = self.pool.get('excel.writer')
        invoice_pool = self.pool.get('account.invoice')

        if context is None:
            context = {}
        document_id = context['document_id']

        document = invoice_pool.browse(
            cr, uid, document_id, context=context)
        partner = document.partner_id
        edi_partner = partner.edi_partner_id

        if edi_partner.code != edi_code:
            return super(EDIPartner, self).EDI_quotation(
                cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # Procedure for this Company
        # ---------------------------------------------------------------------
        _logger.info('START EDI Confirm Order company 1')

        return True
