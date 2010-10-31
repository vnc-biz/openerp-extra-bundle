# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2010-2012 Gnuthink Software Labs Cia. Ltda.
#    Author: Cristian Salamea (cristian.salamea@gntuhink.com)
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name' : 'Taxing properties in product category',
    'version' : '1.0',
    'depends' : ['account', 'product'],
    'author' : 'Gnuthink Software Cia. Ltda.',
    "category": 'Generic Modules/Accounting',
    'description': '''
    This module helps to configure taxes for products in category
    ''',
    'website': 'http://www.gnuthink.com',
    'init_xml': [
                 ],
    'update_xml': [
                   'product_view.xml',
                   ],
    'installable': True,
    'active': False,
}
