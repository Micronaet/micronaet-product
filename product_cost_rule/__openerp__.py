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

{
    'name': 'Product cost rule',
    'version': '0.1',
    'category': 'Product',
    'description': '''
        Rule for generate cost f/company and f/customer
        ''',
    'author': 'Micronaet S.r.l. - Nicola Riolini',
    'website': 'http://www.micronaet.it',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'product',
        'account', # for currency
        'product_first_supplier', # to get first supplier
        'duty_management', # for duty elements
        'base_accounting_program', # q x pack field
        'product_multi_package', # multipack management
        
        # for pack_X measure:
        'product_package_volume', # XXX used?
        'purchase_extra_field', 
        
        'catalog_management', # gamma status
        'duty_management_set', # for duty management in stock
        
        # Exchange management 
        #git clone -b 8.0 https://github.com/OCA/account-financial-tools.git
        #'currency_rate_update', # for exchange fields or udate
        ],
    'init_xml': [],
    'demo': [],
    'data': [
        'security/ir.model.access.csv',    
        'rule_view.xml',
        'wizard/set_calc_rule_view.xml',
        ],
    'active': False,
    'installable': True,
    'auto_install': False,
    }
