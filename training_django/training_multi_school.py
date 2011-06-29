# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2011 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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

from osv import osv, fields
from tools.translate import _
import re
import unicodedata
import netsvc

class training_multi_school(osv.osv):
    _inherit = 'training.multi.school'

    _columns = {
        'django': fields.boolean('Django App'),
        'django_ip': fields.char('IP', size=255),
        'django_port': fields.char('Port', size=64),
        'django_username': fields.char('Username', size=255),
        'django_password': fields.char('Password', size=255),
        'django_key': fields.boolean('Ssh key'),
        'django_ssh_key': fields.char('Ssh Key', size=255, help='Path ssh key localhost'),
        'django_basepath': fields.char('Base path', size=255, help='Path of Django App. Ex: /var/www/django'),
    }

    def test_connection(self, cr, uid, ids, context):

        """
        Test connection OpenERP -> Django
        """

        res = {}
        logger = netsvc.Logger()

        for school in self.browse(cr, uid, ids):
            values = {
                'ip': school.django_ip,
                'port': school.django_port,
                'username': school.django_username,
                'password': school.django_password,
                'key': school.django_key,
                'ssh_key': school.django_ssh_key,
                'basepath': school.django_basepath,
            }
            context['command'] = 'sync/test.py'
            test = self.pool.get('django.connect').ssh_command(cr, uid, school.id, values, context)

            if test == 'success':
                logger.notifyChannel('Django Connection', netsvc.LOG_INFO, "Connection to server is successfull.")
                raise osv.except_osv(_('Ok!'), _('Connection to server are successfully.'))
                return True
            else:
                logger.notifyChannel('Django Connection', netsvc.LOG_ERROR, "Error connection to server.")
                raise osv.except_osv(_('Error!'), _('Error connection to server.'))
                return False

training_multi_school()
