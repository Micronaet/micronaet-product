#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# use: partner.py file_csv_to_import

# Modules required:
import xmlrpclib
import csv
import sys
import ConfigParser
import os

cfg_file = os.path.expanduser('~/etl/Access/import/openerp.cfg')

config = ConfigParser.ConfigParser()
config.read([cfg_file])
dbname = config.get('dbaccess', 'dbname')
user = config.get('dbaccess', 'user')
pwd = config.get('dbaccess', 'pwd')
server = config.get('dbaccess', 'server')
port = config.get('dbaccess', 'port')   # verify if it's necessary: getint
separator = config.get('dbaccess', 'separator') # test
verbose = eval(config.get('import_mode', 'verbose'))

sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/common' % (server, port), allow_none=True)
uid = sock.login(dbname, user, pwd)
sock = xmlrpclib.ServerProxy(
    'http://%s:%s/xmlrpc/object' % (server, port), allow_none=True)

# -----------------------------------------------------------------------------
#                          UPDATE ELEMENTS
# -----------------------------------------------------------------------------
transport_id = 1 # XXX ID of container 1 x 40 HC
#transport_id = 4 # XXX ID of camion 1 x 82 (82 CBM)

# Read transport product yet present:
exclude_ids = []
transport_ids = sock.execute(
    dbname, uid, pwd, 'product.product.transport', 'search', [
    ('transport_id', '=', transport_id),
    ])
for transport in sock.execute(
        dbname, uid, pwd, 'product.product.transport', 'read', transport_ids):
    product_id = transport['product_id'][0]
    if product_id and product_id not in exclude_ids:
        exclude_ids.append(product_id)    

product_ids = sock.execute(dbname, uid, pwd, 'product.product', 'search', [
    ('id', 'not in', exclude_ids),
    ('pz_x_container', '>', 0),
    ])

for product in sock.execute(
        dbname, uid, pwd, 'product.product', 'read', product_ids):
    sock.execute(dbname, uid, pwd, 'product.product.transport', 'create', {
        'product_id': product['id'],
        'transport_id': transport_id,
        'quantity': product['pz_x_container'],    
        })
