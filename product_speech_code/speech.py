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

class StructureStructure(orm.Model):
    """ Model name: StructureStructure
    """    
    _name = 'structure.structure'
    _description = 'Product code structure'
    
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'note': fields.text('Note'),
        }

class StructureBlock(orm.Model):
    """ Model name: StructureBlock
    """    
    _name = 'structure.block'
    _description = 'Structure block'
    _order = 'from_char'
    
    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'code': fields.char('Code', size=10, required=True, 
            help='Used for future ref (name is translated)'),
        'structure_id': fields.many2one(
            'structure.structure', 'Code structure'), 
        'mirror_structure_id': fields.many2one(
            'structure.structure', 'Mirror structure', 
            help='This block work as the mirror code structure'), 
        'from_char': fields.integer('From char', required=True), 
        'to_char': fields.integer('To char', required=True),
        'output_field_id': fields.many2one(
            'ir.model.fields', 'Output field', help='Text will write here',
            required=True, # XXX manage default
            ),
        'output_mask': fields.boolean('Output mask', 
            help='Text with title and return'),
        'mandatory': fields.boolean('Mandatory'),
        'note': fields.text('Note'),
        }

class StructureBlockValore(orm.Model):
    """ Model name: StructureBlockValue
    """    
    _name = 'structure.block.value'
    _description = 'Block value'
    _order = 'rely_value_id,code'
    
    _columns = {
        'code': fields.char('Code', size=10, required=True),
        'name': fields.char('Name', size=64, required=True, translate=True),        
        'block_id': fields.many2one('structure.block', 'Block'),
        'rely_value_id': fields.many2one(
            'structure.block.value', 'Rely value'),
        'note': fields.text('Note'),
        }

class StructureBlockEmptyValore(orm.Model):
    """ Model name: StructureBlockValue
    """    
    _name = 'structure.block.empty.value'
    _description = 'Block empty value'
    _order = 'empty_name'
    
    _columns = {
        'empty_case': fields.text('Empty value parent', 
            help='Example: 030|031|032', required=True),        
        'empty_name': fields.char('Empty name', size=64, translate=True,
            required=True),        
        'empty_test': fields.char('Empty rule', size=64,
            help='Example: default_code[0:3]', required=True),        
        'block_id': fields.many2one('structure.block', 'Block'),
        }

class StructureBlock(orm.Model):
    """ Model name: StructureBlock inherited for add 2many relation fields
    """    
    _inherit = 'structure.block'
    
    _columns = {
        'rely_id': fields.many2one(
            'structure.block', 'Rely block'), 
        'value_ids': fields.one2many(
            'structure.block.value', 'block_id', 'Value'), 
        'emptyvalue_ids': fields.one2many(
            'structure.block.empty.value', 'block_id', 'Empty Value'), 
        }

class StructureStructure(orm.Model):
    """ Model name: StructureStructure inherited for add 2many relation fields
    """    
    _inherit = 'structure.structure'

    _columns = {
        'block_ids': fields.one2many(
            'structure.block', 'structure_id', 'Block'), 
        }

class ProductProduct(orm.Model):
    """ Model name: Add extra fields to product
    """    
    _inherit = 'product.product'
    
    # -------------------------------------------------------------------------    
    # Utility:
    # -------------------------------------------------------------------------
    def get_all_fields_to_update(self, all_db=None):
        ''' Overridable function for update other fields:
        '''    
        res = {}

        if all_db is None:
            all_db = {}
        return res
        
    def get_name_from_default_code(self, default_code, structure_proxy):
        ''' Utility function for calculate product name from code and structure
            selected (passed as arguments)
            self: class instance
            default_code: product code
            structure_proxy: browse object for obj: structure.structure
        '''
        if not default_code or not structure_proxy.id:
            raise osv.except_osv(
                _('Error'), 
                _('Insert manadatory fields: code and structure'),
                )
        
        # ---------------------------------------------
        # Crete database structure for name generation:
        # ---------------------------------------------
        code_db = {}
        for block in structure_proxy.block_ids:
            key = (block.from_char - 1, block.to_char)
            if block.mirror_structure_id:
                mirror_structure_proxy = block.mirror_structure_id
            else:                                
                if block.rely_id:
                    rely_range = (
                        block.rely_id.from_char - 1,
                        block.rely_id.to_char, 
                        )
                    rely_len = \
                        block.rely_id.to_char - block.rely_id.from_char + 1 
                    mask = '%-' + str(rely_len) + 's%s'
                else:
                    rely_range = False
                    mask = False
                mirror_structure_proxy = False    
           
            code_db[key] = [
                {}, rely_range, mask, mirror_structure_proxy, 
                block,
                ]
            for value in block.value_ids:
                if block.rely_id:
                    code = mask % (value.rely_value_id.code, value.code)
                else:
                    code = value.code    
                code_db[key][0][code] = value.name

        # ----------------
        # Name generation:
        # ----------------
        all_db = {}
        name_db = {}
        error = ''

        for key in sorted(code_db):
            # Explose database value:
            value = code_db[key][0]
            rely_range = code_db[key][1]
            mask = code_db[key][2]
            mirror_structure_proxy = code_db[key][3]
            block = code_db[key][4]            
            output = block.output_field_id.name
            if block.output_mask:
                output_mask = block.name + ' %s\n'
            else:                
                output_mask = '%s '
            
            v = default_code[key[0]:key[1]].strip()
            
            if mirror_structure_proxy:    
                # --------------------
                # Recursion structure:
                # --------------------
                name_mirror_db, error_mirror = self.get_name_from_default_code(
                    v, mirror_structure_proxy)
                # integrate 2 database:
                all_fields_db = set(name_db.keys() + name_mirror_db.keys())
                for key in all_fields_db:
                    if key in name_db:
                        if key in name_mirror_db:
                            # XXX problem with title: BUG!!!
                            name_db[key] += ' %s' % name_mirror_db[key]
                        else:
                            pass # nothing, yet present
                    else:
                        name_db[key] = name_mirror_db[key]
                error += error_mirror + '\n'
            else:
                # ------------------
                # Normale structure:
                # ------------------
                if rely_range:
                    v = mask % (
                        default_code[rely_range[0]:rely_range[1]].strip(),
                        v,
                        )

                if output not in name_db:
                    name_db[output] = ''                         
                if v in value:
                    #if output not in name_db:
                    #    name_db[output] = ''                         
                    name_db[output] += output_mask % value[v]
                    all_db[block.code] = value[v]
                else:
                    # Check empty block:                    
                    if v: 
                        error += 'Value %s not present in block (%s, %s)\n' % (
                            v, key[0] + 1, key[1])
                    elif block.emptyvalue_ids:
                        for empty in block.emptyvalue_ids:        
                            empty_data = eval(empty.empty_test)
                            if empty_data in empty.empty_case.split('|'):
                                # has empty block ref:
                                name_db[output] += \
                                    output_mask % empty.empty_name
                                all_db[block.code] = empty.empty_name
                                break

        if error:
            _logger.error('Code error: [%s]' % error)        
        return (name_db, all_db, error)
        
    # -------------------------------------------------------------------------    
    # Button event:
    # -------------------------------------------------------------------------    
    def generate_name_from_code(self, cr, uid, ids, context=None):
        ''' Generate product name depend on structure and code insert
            context parameters:
                update_only_field: means to update extra fields not name
                log_file: if present log data error on file
                
        '''
        assert len(ids) == 1, 'Works only with one record a time'
        
        if context is None:
            context = context
        update_only_field = context.get('update_only_field', False)
        log_file = context.get('log_file', False)

        # Load in every language:            
        lang_pool = self.pool.get('res.lang')
        lang_ids = lang_pool.search(cr, uid, [], context=context)
        lang_proxy = lang_pool.browse(cr, uid, lang_ids, context=context) 
        lang_org = context.get('lang', False)
        
        for language in lang_proxy:
            context['lang'] = language.code
            
            product_proxy = self.browse(cr, uid, ids, context=context)[0]
            default_code = product_proxy.default_code or ''
            default_code = default_code.upper()
            structure_proxy = product_proxy.structure_id
            
            (name_db, all_db, error) = self.get_name_from_default_code(
                default_code, structure_proxy)
            
            if language.code == (lang_org or 'it_IT'): # only for italian
                _logger.warning('Update for lang: %s' % language.code)
                if error:
                    error = error.replace('\n', '<br/>')
                    error = '''
                        <div style="background-color: red;
                            text-align: center; font-weight:bold;
                            color:white; font-size:12px; width=100px;">
                                %s
                            </div>''' % error
                            
                name_db.update({
                    'default_code': default_code,
                    'structure_error': error,            
                    })
            name_db.update(self.get_all_fields_to_update(all_db))

            # Update only field if option selected:
            if update_only_field:
                only_db = {}
                for f in update_only_field:
                    if f in name_db:
                        only_db[f] = name_db[f]
                if only_db:
                    self.write(cr, uid, ids, only_db, context=context)
            else: # write all fields:                  
                self.write(cr, uid, ids, name_db, context=context)
                
        context['lang'] = lang_org # restore
        if log_file and error:
            try:
                f = open(log_file, 'a')
                f.write('%s: %s\n' % (
                    default_code.replace(' ', '*'), 
                    error.replace('\n', ' - '),
                    ))
                f.close()
            except:
                _logger.error('Error write on log file: %s' % log_file)
                   
        return True    

    _columns = {
        'structure_id': fields.many2one(
            'structure.structure', 'Code structure'), 
        'structure_error': fields.text(
            'Structure error', readonly=True), 
        }        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
