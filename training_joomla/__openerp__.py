# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
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
    'name' : 'Training Joomla',
    'version' : '0.1',
    'author' : 'Zikzakmedia SL',
    'website' : 'http://www.zikzakmedia.com',
    'category' : 'Enterprise Specific Modules/Training',
    'description' : """Synchronizes Training objects to Joomla! MySQL tables""",
    'depends' : [
        'training',
        'training_images',
    ],
    'init_xml' : [
    ],
    'demo_xml' : [
    ],
    'update_xml' : [
        'security/ir.model.access.csv',
        'training_view.xml',
        'training_wizard.xml',
        'training_sequence.xml',
        'wizard/wizard_training_joomla_configuration.xml',
        'wizard/wizard_training_joomla_course.xml',
        'wizard/wizard_training_joomla_offer.xml',
        'wizard/wizard_training_joomla_session.xml',
        'wizard/wizard_training_joomla_images.xml',
    ],
    'active' : False,
    'installable' : True,
}
