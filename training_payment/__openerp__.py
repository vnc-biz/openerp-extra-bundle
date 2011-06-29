# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Raimon Esteve <resteve@zikzakmedia.com>
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
    "name" : "Training Payment",
    "author" : "Zikzakmedia SL",
    "website" : "http://www.zikzakmedia.com",
    "license" : "GPL-3",
    "description" : """
Mapping Training e-sale payments to OpenERP payments
    """,
    "version" : "0.1",
    "depends" : [
        "base",
        "training",
        "account_payment_extension",
    ],
    "init_xml" : [],
    "update_xml" : [
        "security/ir.model.access.csv",
        "training_view.xml",
        "training_payment_view.xml",
    ],
    "category" : "Enterprise Specific Modules/Training",
    "active": False,
    "installable": True
}
