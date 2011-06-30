# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
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
    'name' : 'Training Multi School Management',
    'version' : '0.5',
    'author' : 'Zikzakmedia SL',
    'website' : 'http://www.zikzakmedia.com',
    "license" : "GPL-3",
    'category' : 'Enterprise Specific Modules/Training',
    'description' : """
Manage training multi schools
""",
    'depends' : [
        'training',
    ],
    'init_xml' : [
    ],
    'demo_xml' : [
    ],
    'update_xml' : [
        'security/training_multi_shool_security.xml',
        'security/ir.model.access.csv',
        'training_multi_school_view.xml',
        'wizard/create_holiday_year.xml',
    ],
    'active' : False,
    'installable' : True,
}
