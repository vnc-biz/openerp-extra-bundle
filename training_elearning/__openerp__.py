# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2011 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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
    'name' : 'Training e-learning',
    'version' : '0.1',
    'author' : 'Zikzakmedia SL',
    'website' : 'http://www.zikzakmedia.com',
    "license" : "GPL-3",
    'category' : 'Enterprise Specific Modules/Training',
    'description' : """Training e-learning App. Need Django App""",
    'depends' : [
        'training_doc',
        'training_exam_django',
    ],
    'init_xml' : [
    ],
    'demo_xml' : [
    ],
    'update_xml' : [
        'wiki_view.xml',
    ],
    'active' : False,
    'installable' : True,
}
