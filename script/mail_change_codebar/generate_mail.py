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
import ConfigParser

# -----------------------------------------------------------------------------
# Parameters:
# -----------------------------------------------------------------------------
# A. Static parameter:
subject = 'Comunicazione cambio EAN'
mode_label = {
    1: 'EAN Imballo standard scatola',
    2: 'EAN Imballo standard interno',
    3: 'EAN Imballo prodotto singolo',
    }

from_date = '2023-01-01'
filename = './data/EAN_rimappati.csv'

# B. Read configuration parameter:
cfg_file = os.path.expanduser('../openerp.fia')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint


# -----------------------------------------------------------------------------
#                                      Utility:
# -----------------------------------------------------------------------------
def generate_mail(mail_db, partner, verbose=True):
    """ Generate mail
    """
    product_ids = mail_db[partner]

    text = 'Cliente %s mail: %s\n' % (
        partner.name, partner.email,
        )

    for product_id in product_ids:
        for mode in ean_db[product_id]:
            code, ean_old, ean_new = ean_db[product_id][mode]
            text += '%s|Codice %s|Da %s|A %s\n' % (
                mode_label.get(mode),
                code,
                ean_old,
                ean_new,
                )
    if verbose:
        print(text)
    return text


# -----------------------------------------------------------------------------
#                                 Connect to ODOO:
# -----------------------------------------------------------------------------
odoo = erppeek.Client(
    'http://%s:%s' % (
        server, port),
    db=dbname,
    user=user,
    password=pwd,
    )
product_pool = odoo.model('product.product')
line_pool = odoo.model('account.invoice.line')

# -----------------------------------------------------------------------------
#                             Populate EAN DB changed:
# -----------------------------------------------------------------------------
ean_db = {}
counter = -1
for line in open(filename, 'r'):
    counter += 1
    if not counter:
        continue
    row = line.strip().split('|')
    if len(row) != 5:
        print('Jump')
        continue

    product_id = int(row[0].strip())
    code = row[1].strip()
    ean_old = row[2].strip()
    ean_new = row[3].strip()
    mode = int(row[4].strip())

    if product_id not in ean_db:
        ean_db[product_id] = {}
    if mode not in ean_db[product_id]:
        ean_db[product_id][mode] = [code, ean_old, ean_new]


# -----------------------------------------------------------------------------
#                                Read invoice line
# -----------------------------------------------------------------------------
line_ids = line_pool.search([
    ('product_id', 'in', ean_db.keys()),
    ('invoice_id.date_invoice', '>=', from_date),
    ])

mail_db = {}
for line in line_pool.browse(line_ids):
    invoice = line.invoice_id
    partner = invoice.partner_id
    product = line.product_id

    if partner not in mail_db:
        mail_db[partner] = []
    if product_id not in mail_db[partner]:
        mail_db[partner].append(product_id)

import pdb; pdb.set_trace()
# Mail generator (report)
for partner in sorted(mail_db, key=lambda p: p.name):
    mail = generate_mail(mail_db, partner)



