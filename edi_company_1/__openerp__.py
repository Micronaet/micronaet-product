#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
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

{
    'name': 'EDI - Order and Invoice Company 1',
    'version': '0.1',
    'category': 'EDI',
    'description': '''        
        EDI procedure for extract data for Company 1
        ''',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'edi_base',
        'excel_export',  # Export report
        ],
    'init_xml': [],
    'demo': [],
    'data': [
        'edi_view.xml',

        'data/edi_partner_data.xml',
        ],
    'active': False,
    'installable': True,
    'auto_install': False,
    }
