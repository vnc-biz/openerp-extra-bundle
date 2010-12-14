# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
############################################################################################

{
    "name" : "Training Image Gallery",
    "version" : "0.1 ",
    "author" : "Zikzakmedia SL",
    "website" : "http://www.zikzakmedia.com",
    "category" : "Enterprise Specific Modules/Training",
    "depends" : [
        'base',
        'training'
    ],
    "description": """
    This Module implements an Image Gallery for Training.
    You can add images against every offer.

    Code based product_images_olbs module by Sharoon Thomas, Open Labs Business Solutions
    """,
    "init_xml": [],
    "update_xml": [
        'security/ir.model.access.csv',
        'training_images_view.xml',
    ],
    "installable": True,
    "active": False,
}
