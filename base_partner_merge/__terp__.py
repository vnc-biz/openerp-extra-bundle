# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
    'name': 'Partner Merger',
    'version': '1.0',
    'category': 'Generic Modules/Base',
    'description': """

    This Module creates two wizard on:
    1. partners\configuration\merge partners => It merge two partners and create new third partner, and deactivate old two partners
    2. partners\configuration\merge addresses => It merge two partner addresses and create new third address, and deactivate old two addresses

    """,
    'author': 'Tiny',
    'website': 'http://www.openerp.com',
    'depends': ['base'],
    'init_xml': [],
    'update_xml': [
                    "wizard/base_partner_merge_view.xml", 
                    "wizard/base_partner_merge_address_view.xml"
                   ],
    'demo_xml': [],
    'installable': True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
