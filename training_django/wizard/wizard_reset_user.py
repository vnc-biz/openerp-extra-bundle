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

from osv import fields,osv
from tools.translate import _

import re
import unicodedata
import random
import string

class reset_user_wizard(osv.osv_memory):
    _name = 'training.reset.user.wizard'

    _columns = {
        'email_reset_user': fields.many2one('poweremail.templates', 'Email', required=True, help='Template Email Reset User'),
        'username': fields.char('Username', size=64, readonly=True),
        'password': fields.char('Password', size=64, readonly=True),
        'result': fields.text('Result', readonly=True),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def reset_user(self, cr, uid, ids, context=None):
        result = ''
        res_values = {}

        form = self.browse(cr, uid, ids[0])

        contact_id = context and context.get('contact_id')
        partner_contact = self.pool.get('res.partner.contact').browse(cr, uid, contact_id)

        if partner_contact.dj_username or partner_contact.dj_email:
            #Password
            char_set = string.ascii_uppercase + string.digits
            password = ''.join(random.sample(char_set,6))

            res = []
            school_ids = self.pool.get('training.multi.school').search(cr, uid, [('django','=',True)])
            if len(school_ids) == 0:
                result = _('Error: Multi School not active')

            for school in self.pool.get('training.multi.school').browse(cr, uid, school_ids):
                values = {
                    'ip': school.django_ip,
                    'port': school.django_port,
                    'username': school.django_username,
                    'password': school.django_password,
                    'key': school.django_key,
                    'ssh_key': school.django_ssh_key,
                    'basepath': school.django_basepath,
                }
                context['command'] = 'sync/user_reset.py -u %s -p %s' % (partner_contact.dj_username, password)
                respy = self.pool.get('django.connect').ssh_command(cr, uid, school.id, values, context)
                res.append(_('School: %s Username: %s. %s') % (school.name, partner_contact.dj_username, respy))

            if len(res)>0:
                for r in res:
                    result += r
            
            res_values['username'] = partner_contact.dj_username
            res_values['password'] = password

        res_values['state'] = 'done'
        res_values['result'] = result
        #write result values
        self.write(cr, uid, ids, res_values)
        
        self.pool.get('poweremail.templates').generate_mail(cr, uid, form.email_reset_user.id, [form.id])

        return True

reset_user_wizard()
