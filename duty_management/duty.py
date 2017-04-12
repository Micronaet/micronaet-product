# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2001-2014 Micronaet SRL (<http://www.micronaet.it>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import os
import sys
import logging
import openerp
import openerp.netsvc as netsvc
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp import tools
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round as round
from openerp.tools import (DEFAULT_SERVER_DATE_FORMAT, 
    DEFAULT_SERVER_DATETIME_FORMAT, 
    DATETIME_FORMATS_MAP, 
    float_compare)


_logger = logging.getLogger(__name__)


class ProductCustomDutyTax(orm.Model):
    '''Cost for country to import in Italy
    '''
    _name = 'product.custom.duty.tax'
    _description = 'Product custom duty tax'
    _rec_name = 'tax'

    _columns = {
        'tax': fields.float('% Tax', digits=(8, 3)),
        'country_id':fields.many2one('res.country', 'Country', required=True),
        'duty_id':fields.many2one('product.custom.duty', 'Duty code'),
        }

class ProductCustomDuty(orm.Model):
    '''Anagrafic to calculate product custom duty depending of his category
       (using % of tax per supplier cost)
    '''
    _name = 'product.custom.duty'
    _description = 'Product custom duty'

    def load_product_duty_category(self, cr, uid, connector_id, context=None):
        ''' Assign category to product selected
        '''
        res = {}
        category_ids = self.search(cr, uid, [
            ('start', '!=', False),
            ], context=context)
        for category in self.browse(cr, uid, category_ids, context=context):
            for start in category.start.split('|'):
                res[start] = category.id
        return res

    _columns = {
        'name': fields.char('Custom duty', size=100, required=True),
        'code': fields.char('Code', size=24),
        'start': fields.text('Start code', 
            help='Write start code as: 127|027|029'),
        'tax_ids': fields.one2many(
            'product.custom.duty.tax', 'duty_id', '% Tax'),
        }

class ProductProductExtra(orm.Model):
    _inherit = 'product.product'

    # TODO override write or create element for generate duty code!!!!!!!!!!!!
    _columns = {
        'duty_id': fields.many2one('product.custom.duty', 'Custom duty'),
        'duty_code': fields.related(
            'duty_id', 'code', type='char', string='Duty code', readonly=True), 
        #'dazi': fields.float('Dazi (USD)', digits=(16, 2)),
        #'dazi_eur': fields.function(_get_full_calculation, method=True,
        #    type='float', string='Dazi (EUR)', digits=(16, 2), store=False,
        #    multi="total_cost"),
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
