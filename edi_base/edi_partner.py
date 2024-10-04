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


class EDIPartner(orm.Model):
    """ EDI Partner
    """
    _name = 'edi.partner'
    _description = 'EDI Partner'
    _order = 'name'
    _order = 'code'

    def EDI_order(self, cr, uid, ids, context=None):
        """ Export Order for partner Company 1
        """
        _logger.error('This function must be overridden')
        raise osv.except_osv(
            _('Errore EDI'),
            _('Partner non impostato per gestione EDI'),
        )

    def EDI_invoice(self, cr, uid, ids, context=None):
        """ Export Invoice for partner Company 1
        """
        _logger.error('This function must be overridden')
        raise osv.except_osv(
            _('Errore EDI'),
            _('Partner non impostato per gestione EDI'),
        )

    _columns = {
        'name': fields.char('Nome EDI', size=50, required=True),
        'code': fields.char(
            'Codice', size=4, required=True,
            help='Codice usato per differenziare le procedure'),
        'email': fields.char('E-mail', help='Invia per E-mail'),
        'folder': fields.char('Folder', help='Esporta in cartella'),

        'quotation': fields.boolean('Offerte EDI'),
        'order': fields.boolean('Ordini EDI'),
        'invoice': fields.boolean('Fatture EDI'),
    }


class ResPartner(orm.Model):
    """ Model name: res.partner
    """

    _inherit = 'res.partner'

    _columns = {
        'edi_partner_id': fields.many2one(
            'edi.partner', 'EDI partner',
            help='Se il cliente EDI abbinato è partner di esportazione per '
                 'fatture, ordini o offerte',
        ),
    }


class SaleOrder(orm.Model):
    """ Model name: res.partner
    """

    _inherit = 'sale.order'

    def _get_has_edi_partner(
            self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate
        """
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = order.partner_id.edi_partner_id
        return res

    _columns = {
        'has_edi_partner': fields.function(
            _get_has_edi_partner, method=True,
            type='boolean', string='EDI partner', store=False, readonly=True),
        }


class AccountInvoice(orm.Model):
    """ Model name: account.invoice
    """

    _inherit = 'account.invoice'

    def _get_has_edi_partner(
            self, cr, uid, ids, fields, args, context=None):
        """ Fields function for calculate
        """
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = order.partner_id.edi_partner_id
        return res

    _columns = {
        'has_edi_partner': fields.function(
            _get_has_edi_partner, method=True,
            type='boolean', string='EDI partner', store=False, readonly=True),
        }
