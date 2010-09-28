# -*- coding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2010  Sébastien Beau                                    #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
{
    "name" : "Kettle connector",
    "version" : "1.0",
    "depends" : ['base_scheduler_creator'],
    "author" : "Sébastien Beau",
    "description": """Kettle connector
""",
    "website" : "http://www.akretion.com/",
    "category" : "Customer Modules",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
            "kettle.xml",
            'security/kettle_security.xml',
            'security/ir.model.access.csv',
                    ],
    "active": False,
    "installable": True,

}
