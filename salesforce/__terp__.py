##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Sharoon Thomas
#
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
    "name" : "Sales force integration",
    "author" : "Sharoon Thomas",
    "version" : "0.1",
    "category" : "Integration",
    "depends" : ["base","base_contact","base_external_referentials"],
    "demo_xml" : [],
    "update_xml" : [
            'settings/external.referential.type.csv',
            'settings/external.mapping.template.csv',
            'settings/external.mappinglines.template.csv',
            'salesforce_core_view.xml'
                    ],
    "active": False,
    "installable": True
}

