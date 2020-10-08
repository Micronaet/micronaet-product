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


class EdiProductProductExtractWizard(orm.Model):
    """ Wizard for edi product extract wizard
    """
    _name = 'edi.product.product.extract.wizard'
    _order = 'default_template desc'
    _description = 'EDI Extract'
    _rec_name = 'default_template'

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
        # Album / image:
        url_image_mask = 'http://my.%s.it/upload/EDI/%%s/%%s \n' % \
                         cr.dbname.lower()

        langs = ['it_IT', 'en_US']
        if context is None:
            context = {}
        lang_context = context.copy()

        excel_pool = self.pool.get('excel.writer')
        album_image_pool = self.pool.get('product.image.file')
        product_pool = self.pool.get('product.product')
        line_pool = self.pool.get('sale.order.line')
        invoice_line_pool = self.pool.get('account.invoice.line')

        wizard_browse = self.browse(cr, uid, ids, context=context)[0]
        default_code = wizard_browse.default_code
        statistic_category = wizard_browse.statistic_category
        categ_ids = wizard_browse.categ_ids
        catalog_ids = wizard_browse.catalog_ids
        inventory_category_id = wizard_browse.inventory_category_id.id
        template_partner_id = wizard_browse.template_partner_id.id
        status = wizard_browse.status  # gamma

        select_mode = wizard_browse.select_mode
        from_date = wizard_browse.from_date

        # Image management:
        album_ids = [item.id for item in wizard_browse.album_ids]

        # Search product:
        domain = []
        filter_text = 'Tutti i prodotti'

        # ---------------------------------------------------------------------
        # Prefilter for select mode:
        # ---------------------------------------------------------------------
        if template_partner_id:
            if select_mode == 'order_all':  # all order
                # Select order domain:
                select_domain = [
                    ('order_id.partner_id', '=', template_partner_id)]
                if from_date:
                    select_domain.append(
                        ('order_id.date_order', '>=',
                         '%s 00:00:00' % from_date))

                line_ids = line_pool.search(
                    cr, uid, select_domain, context=context)
                product_ids = tuple(set([
                    sale_line.product_id.id for sale_line in
                    line_pool.browse(cr, uid, line_ids, context=context)]))
                domain.append(('id', 'in', product_ids))
            elif select_mode == 'order_stock':  # all order on hand qty present
                pass  # TODO not used for now
            else:  # 'all' depend on other filters
                pass

        if default_code:
            domain.append(('default_code', '=ilike', '%s%%' % default_code))
            filter_text += u', con codice: %s' % default_code

        if statistic_category:
            domain.append(
                ('statistic_category', 'in', statistic_category.split('|')))
            filter_text += \
                u', con categoria statistica: %s' % statistic_category

        if categ_ids:
            domain.append(('categ_id', 'in', categ_ids))
            filter_text += u', con categorie in: %s' % categ_ids

        if catalog_ids:  # TODO test
            domain.append(('catalog_ids', 'in', catalog_ids))
            filter_text += u', con catalogo: %s' % catalog_ids

        if inventory_category_id:
            domain.append(
                ('inventory_category_id', '=', inventory_category_id))
            filter_text += u', con categoria inventario: %s' % \
                           wizard_browse.inventory_category_id.name

        if status:
            domain.append(('status', '=', status))
            filter_text += u', con gamma: %s' % status

        product_ids = product_pool.search(cr, uid, domain, context=context)

        # Excel:
        header = [
            'Codice', ['Nome'],
            ['Descizione breve'], ['Descrizione dettagliata'],
            ['Descrizione extra'], ['Materiale telaio'], ['Materiale seduta'],
            ['Materiale cuscino'], ['Materiale imbottitura'],
            ['Colore telaio'], ['Colore seduta'], ['Colore cuscino'],
            'Alt. prod.', 'Larg. prod.', 'Lung. prod.', 'Diametro',
            'H. seduta', 'H. bracciolo', 'Alt. chiuso',
            'Larg. chiuso', 'Lung. chiuso',
            ['Composizione e dimensione set'],
            'Peso netto', 'N. posizioni', 'Peso massimo', 'Sfoderabile',
            'Arriva montato',
            ['Accessori'],
            'Q. per collo', 'Alt. imballo', 'Larg. imballo',
            'Lung. imballo', 'Volume', 'Peso lordo', 'Peso scatola',
            'Peso cellophane', 'EAN scatola',  # 'EAN interno',
            'Pezzi bancale', 'Pezzi M3', 'Pezzi camion 13.6mt',
            'Dim. bancale',
            ['Manutenzioni'], ['Vantaggi'], ['Garanzia'], ['Categoria'],
            ['Paese produzione'],
            'Immagini',
        ]
        width = [
            12, [30],
            [40], [40],
            [40], [40], [30], [30], [30], [30], [30], [30],
            10, 10, 10, 10, 10, 10, 10, 10, 10,
            [40],
            10, 10, 10, 5, 5,
            [40],
            10, 10, 10, 10, 10, 10, 10, 10, 20,  # 20 'EAN interno',
            10, 10, 10, 10,
            [40], [40], [40], [40], [30], 40,
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
        album_cache = {}
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

                    # Generate image list:
                    images_cell = ''
                    if album_ids:
                        if default_code in album_cache:
                            images_cell = album_cache[default_code]
                        else:
                            # Load album images:
                            image_ids = album_image_pool.search(cr, uid, [
                                ('status', '=', 'ok'),
                                ('album_id', 'in', album_ids),
                                ('product_id.default_code', '=', default_code),
                            ], context=context)
                            for image in album_image_pool.browse(
                                    cr, uid, image_ids, context=context):
                                images_cell += url_image_mask % (
                                    image.album_id.code.lower(),
                                    image.filename,
                                )
                            album_cache[default_code] = images_cell

                    records[default_code] = [
                        default_code,  # 0 default code
                        [product.name],  # 1 name (lang)

                        [product.edi_short_description],  # 2
                        ['Descrizione dettagliata?'],  # 3
                        ['Colore?'],  # 4

                        [product.telaio],  # 5  product.fabric
                        [product.edi_seat_material],  # 6
                        [product.edi_pillow_material],  # 7

                        [product.edi_padding_material],  # 8
                        [product.edi_frame_color],  # 9
                        [product.colour],  # 10  product.edi_seat_color
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
                        product.edi_volume,  # 32
                        product.edi_gross_weight,  # 33
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
                        images_cell,
                    ]
                else:
                    if product.id in jump_ids:
                        continue
                    records[default_code][1].append(product.name)
                    records[default_code][2].append(
                        product.edi_short_description)
                    records[default_code][3].append('Descrizione dettagliata?')
                    records[default_code][4].append('Colore?')
                    records[default_code][5].append(product.fabric)
                    records[default_code][6].append(product.edi_seat_material)
                    records[default_code][7].append(
                        product.edi_pillow_material)
                    records[default_code][8].append(
                        product.edi_padding_material)
                    records[default_code][9].append(product.edi_frame_color)
                    records[default_code][10].append(product.colour)
                    records[default_code][11].append(product.edi_pillow_color)
                    records[default_code][21].append(product.edi_set_data)
                    records[default_code][27].append(product.edi_accessory)
                    records[default_code][41].append(product.edi_maintenance)
                    records[default_code][42].append(product.edi_benefit)
                    records[default_code][43].append(product.edi_warranty)
                    records[default_code][44].append(product.edi_category)
                    records[default_code][45].append(
                        product.edi_origin_country)

        for default_code in records:
            record = records[default_code]

            row += 1
            excel_pool.write_xls_line(ws_name, row, flat_record(record))

        return excel_pool.return_attachment(
            cr, uid, 'EDI product', 'product.xlsx', context=context)

    _columns = {
        'default_template': fields.boolean(
            'EDI', help='Utilizzato come predefinito per esportare i dati EDI '
                        'cliente'),
        'template_partner_id': fields.many2one(
            'res.partner', 'Template per cliente',
            domain=[
                ('customer', '=', True),
                ('is_company', '=', True),
                ('is_address', '=', False),
                ]),
        'album_ids': fields.many2many(
            'product.image.album', 'edi_product_album_export_rel',
            'product_id', 'album_id',
            'Album'),

        'partner_id': fields.many2one(
            'res.partner', 'Fornitore',
            domain=[
                ('supplier', '=', True),
                ('is_company', '=', True),
                ('is_address', '=', False),
                ]),
        'default_code': fields.char('Codice parziale', size=30),
        'statistic_category': fields.char(
            'Categoria Statistica (separ.: |)', size=50),
        'inventory_ids': fields.many2many(
            'product.product.inventory.category', 'edi_product_wiz_inv_cat_rel',
            'wizard_id', 'inventory_id',
            'Categorie inventario'),
        'categ_ids': fields.many2many(
            'product.category', 'edi_product_category_status_rel',
            'product_id', 'category_id',
            'Categoria'),
        'catalog_ids': fields.many2many(
            'product.product.catalog', 'edi_product_inventory_rel',
            'product_id', 'catalog_id',
            'Catalogo'),
        'inventory_category_id': fields.many2one(
            'product.product.inventory.category', 'Categoria Inventorio'),
        'select_mode': fields.selection([
            # ('order_present', 'Ordinato (a magazzino)'),
            ('order_all', 'Ordinato (tutto)'),
            ], 'Modalità selezione',
            help='Filtro per elenco prodotti da esportare'),
        'from_date': fields.date('Data riferimento (>=)'),
        'status': fields.selection([
            ('catalog', 'Catalogo'),
            ('out', 'Fuori catalogo'),
            ('stock', 'Stock'),
            ('obsolete', 'Obsoleto'),
            ('sample', 'Campione'),
            ('promo', 'Promo'),
            ('parent', 'Padre'),
            ('todo', 'Da fare'),
        ], 'Gamma'),
        }
