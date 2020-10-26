# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<http://www.micronaet.it>)
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
import erppeek
import xlsxwriter
import ConfigParser
from datetime import datetime

partner_id = 30442
import pdb; pdb.set_trace()

# -----------------------------------------------------------------------------
# Read configuration parameter:
# -----------------------------------------------------------------------------
# cfg_file = os.path.expanduser('../openerp.cfg')
cfg_file = os.path.expanduser('../local.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint

# Static parameter:
filename = './listino.csv'

# -----------------------------------------------------------------------------
# Connect to ODOO:
# -----------------------------------------------------------------------------
print('Connect to ODOO')
odoo = erppeek.Client(
    'http://%s:%s' % (
        server, port),
    db=dbname,
    user=user,
    password=pwd,
    )
product_pool = odoo.model('product.product.master.pricelist')

product_ids = product_pool.search([
    ('partner_id', '=', partner_id),
    ('product_id', '=', False),
    ])
product_pool.unlink(product_ids)

product_db = {}
for product in product_pool.browse(product_ids):
    product_db[(product.single, product.name)] = product.id

counter = {}
records = []
for line in open(filename, 'r'):
    line = line.strip()
    row = line.split('|')

    default_code = '%-6s' % row[0].upper()
    q_x_pack = int(row[1])
    pricelist = float(row[2].replace(',', '.'))
    records.append((default_code, q_x_pack, pricelist))
    if default_code in counter:
        counter[default_code] += 1
    else:
        counter[default_code] = 1

for default_code, q_x_pack, pricelist in records:
    single = q_x_pack == 1 and counter[default_code] > 1

    data = {
        'partner_id': partner_id,
        'name': default_code,
        'single': single,
        'pricelist': pricelist,
        }

    key = single, default_code
    if key in product_db:
        product_pool.write([product_db[key]], data)
    else:
        product_pool.create(data)


