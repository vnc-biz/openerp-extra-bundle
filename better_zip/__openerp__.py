# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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
    'name' : 'Better zip management',
    'version' : '0.1',
    'depends' : [
                 'base',
                 ],
    'author' : 'Camptocamp',
    'description': """This introduce a better zip/npa management system""",
    'website': 'http://www.camptocamp.com',
    'init_xml': ['security/security.xml'],
    'update_xml': [
                    'better_zip_view.xml',
                   ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}