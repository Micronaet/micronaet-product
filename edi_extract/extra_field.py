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


class ProductProductMasterPricelist(orm.Model):
    """ Model for manage pricelist for parent code
    """
    _name = 'product.product.master.pricelist'
    _description = 'Master pricelist'
    _order = 'name, product_id'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'product_id': fields.many2one(
            'product.product', 'Prodotto',
            help=u'Utilizzare per le particolarità prodotto '
                 u'(alternativo all\'iniziale del codice)'),

        'name': fields.char(
            'Iniziale codice', size=20,
            help='Parte iniziale del codice '
                 '(alternativo al prodotto effettivo)'),
        'pricelist': fields.float('Prezzo listino', digits=(16, 2)),
    }


class ResPartner(orm.Model):
    """ Model name: res.partner
    """

    _inherit = 'res.partner'

    _columns = {
        'master_pricelist_ids': fields.one2many(
            'product.product.master.pricelist', 'partner_id',
            'Listino master',
            help='Listino per iniziale codice e per particolarità prodotto',
        ),
    }


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """

    _inherit = 'product.product'

    _columns = {
        'edi_short_description': fields.char(
            'Descrizione breve', size=64, translate=True),
        'edi_long_description': fields.text(
            'Descrizione lunga', translate=True),
        'edi_seat_color': fields.char(
            'Colore seduta', size=64, translate=True),
        'edi_frame_color': fields.char(
            'Colore telaio', size=64, translate=True),
        'edi_seat_material': fields.char(
            'Materiale seduta', size=64, translate=True),
        'edi_pillow_material': fields.char(
            'Materiale cuscino', size=64, translate=True),
        'edi_padding_material': fields.char(
            'Materiale imbottitura', size=64, translate=True),
        'edi_pillow_color': fields.char(
            'Colore cuscino', size=64, translate=True),
        'edi_diameter': fields.float(
            'Diametero', digits=(16, 2)),
        'edi_seat_height': fields.float(
            'Altezza seduta', digits=(16, 2)),
        'edi_armrest_height': fields.float(
            'Altezza bracciolo', digits=(16, 2)),

        'edi_closed_height': fields.float(
            'Altezza chiuso cm.', digits=(16, 2)),
        'edi_closed_width': fields.float(
            'Larghezza chiuso cm.', digits=(16, 2)),
        'edi_closed_length': fields.float(
            'Lunghezza chiuso cm.', digits=(16, 2)),

        'edi_set_data': fields.text(
             'Composizione e dimensione (per i set)', translate=True),
        'edi_accessory': fields.text(
             'Accessori', translate=True),

        'edi_position': fields.char('Numero di posizioni', size=20),
        'edi_max_weight': fields.float('Peso max. Kg.', digits=(16, 2)),

        'edi_removable': fields.boolean('Removibile'),
        'edi_mounted': fields.boolean('Arriva montato'),

        'edi_volume': fields.float('Volume m³', digits=(16, 2)),
        'edi_net_weight': fields.float(
            'Peso netto Kg.', digits=(16, 2)),
        'edi_gross_weight': fields.float(
            'Peso lordo Kg.', digits=(16, 2)),
        'edi_package_weight': fields.float(
            'Peso imballo Kg.', digits=(16, 2)),
        'edi_cellophane_weight': fields.float(
            'Peso Cellophane Kg.', digits=(16, 2)),

        'edi_pallet_dimension': fields.char(
            'Dimensioni pallet', size=64, translate=True),

        'edi_maintenance': fields.text(
             'Manutenzione', translate=True),
        'edi_benefit': fields.text(
             'Benefit', translate=True),
        'edi_warranty': fields.text(
             'Garanzia', translate=True),

        'edi_category': fields.char(
            'Categoria', size=64, translate=True),
        'edi_origin_country': fields.char(
            'Paese di origine', size=64, translate=True),
    }
