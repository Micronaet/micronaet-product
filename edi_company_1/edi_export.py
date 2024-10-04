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
module_edi_code = '1'


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
        destination = document.destination_partner_id or partner
        invoice = document.invoice_partner_id or partner
        company = document.company_id

        edi_partner = partner.edi_partner_id

        if edi_partner.code != module_edi_code:
            return super(EDIPartner, self).EDI_quotation(
                cr, uid, ids, context=context)

        # ---------------------------------------------------------------------
        # Procedure for this Company
        # ---------------------------------------------------------------------
        _logger.info('START EDI Confirm Order company 1')

        ws_name = 'Conferma ordine'
        header = [
            u'RecordType',
            u'H-Partita IVA Fornitore',
            u'H-Dest. Codice Punto Vendita',
            u'RecordID',
            u'H-Nr. Documento',
            u'H-Data Documento',
            u'H-Nazione Fornitore',
            u'H-CF Fornitore',
            u'H-Partita IVA Cliente',
            u'H-NazioneCliente',
            u'H-CF Cliente',
            u'H-Dest. Indirizzo',
            u'H-Dest. Città',
            u'H-Dest. Data Cons. Prevista',
            u'H-Nr. Ordine GT',
            u'H-Data Ordine GT',
            u'H-Nr. Ordine Fornitore',
            u'H-Metodo di Pagamento',
            u'H-Condizioni di Pagamento',
            u'H-IBAN Pagamento',
            u'H-Nr. Fornitore Origine',
            u'H-Percentuale Commissione',
            u'H-Costo Commissioni',
            u'H-Costo Trasporto',
            u'H-Costo Etichettatura',
            u'H-Costo Imballi',
            u'H-Nr. Carrelli CC',
            u'H-Nr. Carrello c/Placca',
            u'H-Nr. Carrelli senza Placca',
            u'H-Nr. Pianali',
            u'H-Nr. Prolunghe Corte',
            u'H-Nr. Prolunghe Lunghe',
            u'H-Nr. Colli',
            u'H-Nr. Pallet EPAL',
            u'H-Nr. Pallet a Perdere',
            u'H-Nome Corriere Incaricato',
            u'H-Stato',
            u'L-Posizione',
            u'L-EAN',
            u'L-Nr. Articolo Fornitore',
            u'L-Nr. Articolo Interno',
            u'L-Descrizione',
            u'L-Quantità',
            u'L-Unità di Misura',
            u'L-Quantità UdM',
            u'L-Costo Lordo',
            u'L-IVA %',
            u'L-Sconto 1%',
            u'L-Sconto 2%',
            u'L-Sconto 3%',
            u'L-Sconto 4%',
            u'L-Sconto 5%',
            u'L-Sconto Promo 1%',
            u'L-Sconto Promo 2%',
            u'L-Sconto Promo 3%',
            u'L-Sconto Promo 4%',
            u'L-Sconto Promo 5%',
            u'L-Importo Riga',
            u'L-Prezzo Etichette',
            u'L-Quantità Etichette',
            u'L-Intra Cod. Tariffa',
            u'L-Intra Peso Lordo',
            u'L-Intra Peso Netto',
            u'L-Intra Numero Colli',
            u'L-Passp. Nr. RUOP',
            u'L-Passp. Lotto',
            u'L-Quantità per Kit',
            u'L-Ean Padre',
            u'L-Codice Famiglia',
        ]
        width = [20 for l in range(len(header))]

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
        edi_code = destination.edi_code or ''  # if not destination is partner!
        header_line = [
            1,  # RecordType
            (company.vat or '')[-11:],  # H-Partita IVA Fornitore
            edi_code or '',  # H-Dest. Codice Punto Vendita
            '',  # RecordID BLANK
            document.name,  # H-Nr. Documento
            self.edi_date(document.date_order),  # H-Data Documento
            company.country_id.code or 'IT',  # H-Nazione Fornitore
            '',  # H-CF Fornitore  (only if VAT not present)

            # todo Chi è il cliente?
            (partner.vat or '')[-11],  # H-Partita IVA Cliente  ???
            partner.country_id.code or 'IT',  # H-NazioneCliente  ???
            '',  # H-CF Cliente  ???
            destination.street or '',  # H-Dest. Indirizzo  ???
            destination.city or '',  # H-Dest. Città
            self.edi_date(
                document.date_deadline),  # H-Dest. Data Cons. Prevista
            document.client_order_code or '',  # H-Nr. Ordine GT
            '',  # H-Data Ordine GT  OPTIONAL
            '',  # H-Nr. Ordine Fornitore
            3,  # H-Metodo di Pagamento  # todo manage in payment
            0,  # H-Condizioni di Pagamento  # todo manage in paymeny
            '',  # H-IBAN Pagamento
            '',  # H-Nr. Fornitore Origine
            0.0,  # H-Percentuale Commissione
            0.0,  # H-Costo Commissioni
            0.0,  # H-Costo Trasporto
            0.0,  # H-Costo Etichettatura
            0.0,  # H-Costo Imballi
            0,  # H-Nr. Carrelli CC
            0,  # H-Nr. Carrello c/Placca
            0,  # H-Nr. Carrelli senza Placca
            0,  # H-Nr. Pianali
            0,  # H-Nr. Prolunghe Corte
            0,  # H-Nr. Prolunghe Lunghe
            document.parcels or 0,  # H-Nr. Colli
            0,  # H-Nr. Pallet EPAL
            0,  # H-Nr. Pallet a Perdere
            '',  # H-Nome Corriere Incaricato
            '1',  # H-Stato  # '1' Definitivo
            ]
        detail_col = len(header_line)

        position = 0
        for line in document.order_line:
            position += 1
            row += 1

            # Header part:
            excel_pool.write_xls_line(
                ws_name, row, header_line, default_format=f_text)

            # Data:
            product = line.product_id
            # todo ean13 or ean13_mono
            vat = line.tax_id[0].code or ''

            # Detail part:
            detail_line = [
                position,  # L-Posizione
                product.ean13 or '',  # L-EAN
                product.default_code or '',  # L-Nr. Articolo Fornitore
                '',  # L-Nr. Articolo Interno  # OPTIONAL
                line.name or '',  # L-Descrizione
                line.product_uom_qty or 0.0,  # L-Quantità
                '',  # L-Unità di Misura  OPTIONAL (they use custom code!)
                line.product_uom_qty or 0.0,  # L-Quantità UdM
                line.price_unit or 0.0,  # L-Costo Lordo  # todo unit?
                vat,  # L-IVA %
                '',  # L-Sconto 1%
                '',  # L-Sconto 2%
                '',  # L-Sconto 3%
                '',  # L-Sconto 4%
                '',  # L-Sconto 5%
                '',  # L-Sconto Promo 1%
                '',  # L-Sconto Promo 2%
                '',  # L-Sconto Promo 3%
                '',  # L-Sconto Promo 4%
                '',  # L-Sconto Promo 5%
                '',  # L-Importo Riga
                '',  # L-Prezzo Etichette
                '',  # L-Quantità Etichette
                '',  # L-Intra Cod. Tariffa
                '',  # L-Intra Peso Lordo
                '',  # L-Intra Peso Netto
                '',  # L-Intra Numero Colli
                '',  # L-Passp. Nr. RUOP
                '',  # L-Passp. Lotto
                '',  # L-Quantità per Kit
                '',  # L-Ean Padre
                '',  # L-Codice Famiglia
                ]
            excel_pool.write_xls_line(
                ws_name, row, detail_line, default_format=f_text,
                col=detail_col)

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
