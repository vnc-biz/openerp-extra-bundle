# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
#                       Jesús Martín <jmartin@zikzakmedia.com>
#                       Raimon Esteve <resteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
############################################################################################

{
    "name" : "Ingram Micro Connector",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "http://www.zikzakmedia.com",
    "license" : "AGPL-3",
    "category" : "Added functionality",
    "depends" : [
        "sale",
        "product_trademark",
        "base_csv",
    ],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
        Import IngramMicro Data to OpenERP:
        - Product
        - Category
        - Stock
        - Generate XML Sale Orders
        Download ZIP or CSV dir in addons/product_ingram/temp
    """,
    'update_xml': [
        'security/ir.model.access.csv',
        'ingram_view.xml',
        'csv_file_view.xml',
        'product_view.xml',
        'settings/ingram_data.xml',
        'settings/csv_mapping.xml',
    ],
    'test':[''],
    'installable': True,
    'active': False,
}
