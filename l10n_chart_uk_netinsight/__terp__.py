# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    (C)Sharoon Thomas, Net Insight e Business Consultancy                            
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
    "name" : "UK-Chart of Accounts",
    "version" : "0.2",
    "depends" : [
                 "account", 
                 "base",
        ],
    "author" : "Net-Insight, Open Labs",
    "description": """
    Chart of Accounts for United Kingdom
    """,
    'website': 'http://www.net-insight.co.uk/',
    'init_xml': [
        ],
    'update_xml': [
        'data/account.account.type.csv',
        'data/account.account.template.csv',
        'data/account.tax.code.template.csv',
        'account_chart.xml',
        'data/account.tax.template.csv',
        'data/res.country.state.csv',
        'l10n_uk_wizard.xml',
        ],
    'demo_xml': [
        ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
