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
    
    # Scheduled action:    
    def scheduled_import_campaign(self, cr, uid,
            script, filename, header=1, separator='$|$', context=None):
        ''' Scheduled event that launch campaign read status and import in
            product field
            script: name of script to launch
            filename: name of file generated from the script
            separator: csv char that separate colums
            header: num of line for header
        '''
        _logger.info('Start import campaign: script=%s filename=%s' % (
            script, filename))
        
        # -----------------------
        # Get CSV files from web:    
        # -----------------------
        try:
            script = os.path.expanduser(script)
            os.system(script)
        except:
            _logger.error('Error launching import script: %s' % script)    
            
        # -----------------    
        # Import procedure:    
        # -----------------    
        try:
            filename = os.path.expanduser(filename)
            csv_in = open(filename, 'r')
            load_data = {}
            tot_col = False
            i = 0
            
            # Reset all data value:
            product_ids = self.search(cr, uid, [
                ('pm_campaign_out', '!=', False)], context=context)
            self.write(cr, uid, product_ids, {
                'pm_campaign_out': False,
                'pm_campaign_detail': False,
                }, context=context)    
                
            for line in csv_in:
                i += 1
                
                # jump header line
                if header: 
                    header -= 1
                    continue   
                    
                # Clean line:    
                line = line.strip()[1:-1]
                line = line.split(separator)
                # save total colums for test
                if not tot_col: 
                    tot_col = len(line)
                    
                # check columns number:
                if tot_col != len(line): 
                    _logger.error('%s. Line with different cols' % i)
                    continue
                
                # parse line:
                campaign = line[0]
                from_date = line[1]
                to_date = line[2]
                code = line[3]
                description = line[4]
                qty = float(line[5])

                # save total (update after)
                product_ids = self.search(cr, uid, [
                    ('default_code', '=', code)], context=context)

                if not product_ids:
                    _logger.error('Code not found code: %s' % code)
                    continue
                   
                if len(product_ids) > 1:
                    _logger.warning('Double code: %s' % code)
                product_id = product_ids[0]    
                detail = '%s: %s (%s - %s)\n' % (
                    qty, campaign, from_date, to_date)
                if product_id not in load_data:
                    load_data[product_id] = [qty, detail]
                else:
                    load_data[product_id][0] += qty
                    load_data[product_id][1] += detail
                    
            
            # Update product on database:
            for product_id, data in load_data.iteritems():            
                qty, detail = data
                self.write(cr, uid, product_id, {
                    'pm_campaign_out': qty,
                    'pm_campaign_detail': detail,
                    }, context=context)
        except:
            _logger.error('Error read filename: %s' % filename)
        
        _logger.info('End import campaign status')
        return True

    # Scheduled action:    
    def button_import_campaign_web(self, cr, uid, ids, context=None):
        ''' Manually launch operations
        '''
        return True
        # TODO launch operation reading parameters from scheduler:
        return self.scheduled_import_campaign(cr, uid,
            script, filename, header=1, separator='$|$', context=context)        
        
    _columns = {
        'pm_campaign_out': fields.float(
            '(Campaign OC)', digits=(16, 2)),
        'pm_campaign_detail': fields.text('Campaign detail'),    
        }
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
