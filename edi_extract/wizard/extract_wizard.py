#!/usr/bin/python
# -*- coding: utf-8 -*-
###############################################################################
#
# ODOO (ex OpenERP)
# Open Source Management Solution
# Copyright (C) 2001-2015 Micronaet S.r.l. (<https://micronaet.com>)
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


import pdb
import logging
from openerp.osv import fields, osv, expression, orm
from datetime import datetime, timedelta
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class EdiProductProductExtractWizard(orm.TransientModel):
    """ Wizard for edi product extract wizard
    """
    _name = 'edi.product.product.extract.wizard'

    # --------------------
    # Wizard button event:
    # --------------------
    def action_extract(self, cr, uid, ids, context=None):
        """ Event for button done
        """
        def flat_record(record, langs=False, header=False):
            """ Put all list in extension of record
                langs used for header only, if present
            """
            res = []
            for item in record:
                if type(item) == list:
                    if langs:
                        item = item[0]
                        for lang in langs:
                            if header:  # For header title
                                res.append('%s [%s]' % (item, lang[:2]))
                            else:  # For columns value
                                res.append(item)
                    else:  # normal data record
                        res.extend(item)
                else:
                    res.append(item)
            return res

        # Parameters:
        langs = ['it_IT', 'en_US']
        if context is None:
            context = {}
        lang_context = context.copy()

        excel_pool = self.pool.get('excel.writer')
        product_pool = self.pool.get('product.product')

        # wizard_browse = self.browse(cr, uid, ids, context=context)[0]

        # Search product:
        product_ids = product_pool.search(cr, uid, [
            ('default_code', 'not in', (False, '')),
        ], context=context)[:10]  # TODO remove

        # Excel:
        header = [
            'Codice', ['Nome'],
            ['Descizione breve'], ['Descrizione dettagliata'],
            ['Descrizione extra'],
            ['Materiale telaio'],
            ['Materiale seduta'],
            ['Materiale cuscino'],
            ['Materiale imbottitura'],
            ['Colore telaio'],
            ['Colore seduta'],
            ['Colore cuscino'],
            'Alt. prod.',
            'Larg. prod.',
            'Lung. prod.',
            'Diametro',
            'H. seduta',
            'H. bracciolo',
            'Alt. chiuso',
            'Larg. chiuso',
            'Lung. chiuso',
            ['Composizione e dimensione set'],
            'Peso netto',
            'N. posizioni',
            'Peso massimo',
            'Sfoderabile',
            'Arriva montato',
            ['Accessori'],
            'Q. per collo',
            'Alt. imballo',
            'Larg. imballo',
            'Lung. imballo',
            'Volume',
            'Peso lordo',
            'Peso scatola',
            'Peso cellophane',
            'EAN scatola',
            #'EAN interno',
            'Pezzi bancale',
            'Pezzi M3',
            'Pezzi camion 13.6mt',
            'Dim. bancale',
            ['Manutenzioni'],
            ['Vantaggi'],
            ['Garanzia'],
            ['Categoria'],
            ['Paese produzione'],
        ]
        width = [
            10, [30],
            [40], [40],
            [40],
            [40],
            [30],
            [30],
            [30],
            [30],
            [30],
            [30],
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            [40],
            10,
            10,
            10,
            5,
            5,
            [40],
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            10,
            20,
            # 20 'EAN interno',
            10,
            10,
            10,
            10,
            [40],
            [40],
            [40],
            [40],
            [30],
        ]
        ws_name = _('EDI Product')
        row = 0
        excel_pool.create_worksheet(ws_name)
        excel_pool.write_xls_line(
            ws_name, row, flat_record(header, langs, header=True))
        excel_pool.column_width(
            ws_name, flat_record(width, langs, header=False))

        records = {}
        jump_ids = []
        for lang in langs:
            lang_context['lang'] = lang
            for product in product_pool.browse(
                    cr, uid, product_ids, context=lang_context):
                default_code = product.default_code
                if lang == 'it_IT':  # First loop
                    if default_code in records:
                        _logger.error('Double code jumped')
                        jump_ids.append(product.id)
                        continue
                    records[default_code] = [
                        default_code,  # 0 default code
                        [product.name],  # 1 name (lang)

                        [product.edi_short_description],  # 2
                        [product.telaio],  # 3
                        [product.colour],  # 4
                        [product.fabric],  # 5
                        [product.edi_seat_material],  # 6
                        [product.edi_pillow_material],  # 7
                        [product.edi_padding_material],  # 8
                        ['Colore telaio?'],  # 9
                        ['Colore seduta?'],  # 10
                        [product.edi_pillow_color],  # 11
                        product.height,  # 12
                        product.width,  # 13
                        product.length,  # 14
                        product.edi_diameter,  # 15
                        product.edi_seat_height,  # 16
                        product.edi_armrest_height,  # 17
                        product.edi_closed_height,  # 18
                        product.edi_closed_width,  # 19
                        product.edi_closed_length,  # 20
                        [product.edi_set_data],  # 21
                        product.weight_net,  # 22
                        product.edi_position,  # 23
                        product.edi_max_weight,  # 24
                        'S' if product.edi_removable else 'N',  # 25
                        'S' if product.edi_mounted else 'N',  # 26
                        [product.edi_accessory],  # 27
                        product.q_x_pack,  # 28
                        product.pack_l,  # 29
                        product.pack_h,  # 30
                        product.pack_p,  # 31
                        product.volume,  # 32
                        product.weight,  # 33
                        product.edi_package_weight,  # 34
                        product.edi_cellophane_weight,  # 35
                        product.ean13,  # 36
                        # 'EAN interno',
                        product.item_per_pallet,  # 37
                        product.item_per_mq,  # 38
                        product.item_per_camion,  # 39
                        product.edi_pallet_dimension,  # 40
                        [product.edi_maintenance],  # 41
                        [product.edi_benefit],  # 42
                        [product.edi_warranty],  # 43
                        [product.edi_category],  # 44
                        [product.edi_origin_country],  # 45
                    ]
                else:
                    if product.id in jump_ids:
                        continue
                    records[default_code][1].append(product.name)
                    records[default_code][2].append(
                        product.edi_short_description)
                    records[default_code][3].append(product.telaio)
                    records[default_code][4].append(product.colour)
                    records[default_code][5].append(product.fabric)
                    records[default_code][6].append(product.edi_seat_material)
                    records[default_code][7].append(
                        product.edi_pillow_material)
                    records[default_code][8].append(
                        product.edi_padding_material)
                    records[default_code][9].append('Colore telaio?')
                    records[default_code][10].append('Colore seduta?')
                    records[default_code][11].append(product.edi_pillow_color)
                    records[default_code][21].append(product.edi_set_data)
                    records[default_code][27].append(product.edi_accessory)
                    records[default_code][41].append(product.edi_maintenance)
                    records[default_code][42].append(product.edi_benefit)
                    records[default_code][43].append(product.edi_warranty)
                    records[default_code][44].append(product.edi_category)
                    records[default_code][45].append(product.edi_origin_country)

        for default_code in records:
            record = records[default_code]

            row += 1
            excel_pool.write_xls_line(ws_name, row, flat_record(record))

        return excel_pool.return_attachment(
            cr, uid, 'EDI product', 'product.xlsx', context=context)

    _columns = {
        # TODO inventory category?
        }
