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

    def get_range_inventory_date(self, cr, uid, context=None):
        """ Overridable function for get the from date
        """
        # Company 1 standard:
        now = datetime.now()
        if now.month >= 9:  # 9 - 12
            season_year = now.year
        else:  # 1 - 8
            season_year = now.year - 1

        from_date = '%s-09-01 00:00:00' % season_year  # todo restore this
        # from_date = '2023-09-01 00:00:00'  # todo REMOVE THIS!!

        # Limit up date parameter:
        limit_up_date = context.get('limit_up_date', False)  # limit for invent
        if limit_up_date:
            to_date = limit_up_date
            _logger.warning('Limite date: %s' % limit_up_date)
        else:
            to_date = '%s-08-31 23:59:59' % (season_year + 1)
        _logger.warning('>>> START INVENTORY [%s - %s] <<<' % (
            from_date, to_date))
        return from_date, to_date
