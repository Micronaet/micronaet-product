#!/usr/bin/python
# -*- coding: utf-8 -*-
##############################################################################
#
#   Copyright (C) 2010-2012 Associazione OpenERP Italia
#   (<http://www.openerp-italia.org>).
#   Copyright(c)2008-2010 SIA "KN dati".(http://kndati.lv) All Rights Reserved.
#                   General contacts <info@kndati.lv>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import os
import sys
import logging
from openerp.report import report_sxw
from openerp.report.report_sxw import rml_parse
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)

_logger = logging.getLogger(__name__)


class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):        
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_objects': self.get_objects,
            'get_datetime': self.get_datetime,
        })

    def get_objects(self, data):
        ''' Get report from wizard filters
        '''
        # Pool used:
        move_pool = self.pool.get('stock.move')

        # Readability:
        cr = self.cr
        uid = self.uid
        context = {}
        
        # ---------------
        # Load move data:
        # ---------------        
        domain = data.get('domain', [])
        partial = data.get('report_code_break', 6)
        detailed = data.get('report_detailed', False)
        
        move_ids = move_pool.search(cr, uid, domain, context=context)
        
        moves = [move for move in move_pool.browse(
            cr, uid, move_ids, context=context)]        
        moves = sorted(moves, key=lambda x: x.product_id.default_code)
        
        # Create total blocks:
        last_code = False
        total = 0.0
        res = []
        for move in moves:
            default_code = move.product_id.default_code or ''
            if last_code == False: # first loop only
                last_code = default_code[:partial]
                
            if last_code == default_code[:partial]:
                total += move.product_uom_qty
            else:
                res.append(('total', (total, last_code[:partial])))
                last_code = default_code[:partial]
                total = move.product_uom_qty
            if detailed:    
                res.append(('data', move))

        if last_code: # add last record:
            res.append(('total', (total, last_code[:partial])))
        
        return res
        
    def get_datetime(self):
        ''' Return datetime obj
        '''
        return datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
