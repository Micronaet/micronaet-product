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
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp import SUPERUSER_ID, api
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class PurchaseOrder(orm.Model):
    """ Custom purchase order
    """
    _inherit = 'purchase.order'

    # Override default Workflow action:
    def generate_purchase_duty_block(self, cr, uid, ids, context=None):
        """ Button event for generate duty block
        """
        assert len(ids) == 1, 'Funziona per un ordine fornitore alla volta!'

        order = self.browse(cr, uid, ids, context=context)[0]

        table = {}
        error = ''
        for line in order.order_line:
            product = line.product_id

            duty_code = product.duty_code
            quantity = line.product_qty

            # -----------------------------------------------------------------
            # Weight management:
            # -----------------------------------------------------------------
            net = product.force_weight_net or product.weight_net
            gross = product.force_weight or product.weight
            # todo manage force_package_weight

            if not duty_code:
                continue

            if duty_code not in table:
                table[duty_code] = [0.0, 0.0, 0.0]  # Amount, net, gross

            table[duty_code][0] += line.price_subtotal  # Subtotal amount
            table[duty_code][1] += net * quantity  # W. net
            table[duty_code][2] += gross * quantity  # W. gross

            if not net:
                error += '%s >> Peso netto mancante\n' % product.default_code
            if not gross:
                error += '%s >> Peso lordo mancante\n' % product.default_code

        res = ''
        for duty_code in sorted(table):
            res += u'Codice %s: %.2f € [Netto: %s Kg - Lordo %s Kg]\n' % (
                duty_code, table[duty_code][0],
                table[duty_code][1], table[duty_code][2]
                )

        return self.write(cr, uid, ids, {
            'duty_block': res,
            'duty_error': error,
            }, context=context)

    _columns = {
        'duty_block': fields.text('Tabella doganale'),
        'duty_error': fields.text('Errori calcolo doganale'),
        }
