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
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DATETIME_FORMATS_MAP,
    float_compare)


_logger = logging.getLogger(__name__)


class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """

    _inherit = 'product.product'

    _columns = {
        'edi_short_description': fields.char(
            'Short description', size=64, translate=True),
        'edi_seat_material': fields.char(
            'Seat material', size=64, translate=True),
        'edi_pillow_material': fields.char(
            'Pillow material', size=64, translate=True),
        'edi_padding_material': fields.char(
            'Padding material', size=64, translate=True),
        'edi_pillow_color': fields.char(
            'Pillow color', size=64, translate=True),
        'edi_diameter': fields.float('Diameter', digits=(16, 2)),
        'edi_seat_height': fields.float('Seat height', digits=(16, 2)),
        'edi_armrest_height': fields.float('Armrest height', digits=(16, 2)),

        'edi_closed_height': fields.float('Closed height cm.', digits=(16, 2)),
        'edi_closed_width': fields.float('Closed width cm.', digits=(16, 2)),
        'edi_closed_length': fields.float('Closed length cm.', digits=(16, 2)),

        'edi_set_data': fields.text(
             'Composition and dimension (for set)', translate=True),
        'edi_accessory': fields.text(
             'Accessory', translate=True),

        'edi_position': fields.integer('Number of position'),
        'edi_max_weight': fields.float('Max weight Kg.', digits=(16, 2)),

        'edi_removable':fields.boolean('Removable'),
        'edi_mounted':fields.boolean('Product mounted'),

        'edi_volume': fields.float('Volume m³', digits=(16, 2)),
        'edi_gross_weight': fields.float(
            'Gross weight Kg.', digits=(16, 2)),
        'edi_package_weight': fields.float(
            'Package weight Kg.', digits=(16, 2)),
        'edi_cellophane_weight': fields.float(
            'Cellophane weight Kg.', digits=(16, 2)),

        'edi_pallet_dimension': fields.char(
            'Pallet dimension', size=64, translate=True),

        'edi_maintenance': fields.text(
             'Maintenance', translate=True),
        'edi_benefit': fields.text(
             'Benefit', translate=True),
        'edi_warranty': fields.text(
             'Warranty', translate=True),

        'edi_category': fields.char(
            'Category', size=64, translate=True),
        'edi_origin_country': fields.char(
            'Origin country', size=64, translate=True),

    }

