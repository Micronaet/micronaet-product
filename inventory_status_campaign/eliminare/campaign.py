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

class ProductProduct(orm.Model):
    """ Model name: ProductProduct
    """    
    _inherit = 'product.product'

    def _get_campaign_product_status_inventory(
            self, cr, uid, ids, fields, args, context=None):
        ''' Fields function for calculate 
        '''
        result = {}
        _logger.error('CAMPAIGN STATUS')
        campaign_pool = self.pool.get('campaign.product')
        campaign_ids = campaign_pool.search(cr, uid, [
            ('product_id.id', 'in', ids), # only selected product
            ('campaign_id.state', '=', 'confirmed'), # onli confirmed campaign
            ], context=context)
            
        for item in campaign_pool.browse(cr, uid, campaign_ids, 
                context=context):                
            # Readability:                
            campaign = item.campaign_id
            
            # Data:
            product_id = item.product_id.id
            qty = item.qty#_ordered
            text = '%s: %s (%s - %s)\n' % (
                qty, campaign.code, campaign.from_date, 
                campaign.to_date)                
            if product_id not in result:
                result[item.product_id.id] = {
                    'mx_campaign_out': qty,
                    'mx_campaign_detail': text,
                    }
            else:
                result[product_id]['mx_campaign_out'] += qty
                result[product_id]['mx_campaign_detail'] += text

        # Add empty campaign:
        for item_id in ids:
            if item_id not in result:
                result[item_id] = {
                    'mx_campaign_out': 0.0,
                    'mx_campaign_detail': False,
                    }
        return result

    _columns = {
        'mx_campaign_out': fields.function(
            _get_campaign_product_status_inventory, method=True, 
            type='float', string='(Campaign OC)', digits=(16, 2),
            store=False, multi=True,
            ), 
        'mx_campaign_detail': fields.function(
            _get_campaign_product_status_inventory, method=True, 
            type='text', string='(Campaign detail)', store=False, multi=True,
            ), 
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
