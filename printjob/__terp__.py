# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
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
##############################################################################
{
	"name" : "PrintJob",
	"author" : "Pegueroles SCP",
	"version" : "1.0",
        "website" : "http://www.pegueroles.com",
        "category" : "Vertical Modules/Parametrization",
	"depends" : ["base"],
	"description": """This module updates OpenERP printig
        The new features are :
        * Enables batch printing 
        * Correct memory leack when printing crashes
        * Permits repriting lost PDFs
        * Possibilty to send jobs to a prrinter attached to the server 
        """,
	"init_xml" : [],
	"update_xml" : [
                    "printjob_view.xml",                    
                    "printjob_data.xml",                    
                    "security/printjob_security.xml",
                    ],
	"category" : "base/printjob",
	"active": False,
	"installable": True
}
