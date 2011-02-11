# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
##############################################################################
{
    "name" : "Internet Domain",
    "author" : "Zikzakmedia",
    "website" : "http://www.zikzakmedia.com",
    "description" : """
Organize your domains and services
Tools -> Domain
* Domains
* Renewals
* Products/Services
* Network
* Send email expiration domain with Schuddle Action and Power Email
* Invoice renewal domain
    """,
    "version" : "0.1",
    "depends" : ["base","product","account","network","poweremail-v6"],
    "init_xml" : [],
    "update_xml" : [
        "security/internetdomain_security.xml",
        "security/ir.model.access.csv",
        "internetdomain_view.xml",
        "internetdomain_report.xml",
        "internetdomain_wizard.xml",
        "internetdomain_data.xml",
        "company_view.xml",
    ],
    "category" : "Product",
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

