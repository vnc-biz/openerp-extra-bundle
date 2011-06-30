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

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

class create_user_wizard(osv.osv_memory):
    _name = 'training.create.user.wizard'

    _columns = {
        'email_create_user': fields.many2one('poweremail.templates', 'Email', required=True, help='Template Email Create User'),
        'username': fields.char('Username', size=64, readonly=True),
        'password': fields.char('Password', size=64, readonly=True),
        'email': fields.char('Last Name', size=255, readonly=True),
        'first_name': fields.char('First Name', size=255, readonly=True),
        'last_name': fields.char('Last Name', size=255, readonly=True),
        'result': fields.text('Result', readonly=True),
        'state':fields.selection([
            ('first','First'),
            ('done','Done'),
        ],'State'),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }

    def create_user(self, cr, uid, ids, context=None):
        result = ''
        res_values = {}

        form = self.browse(cr, uid, ids[0])

        contact_id = context and context.get('contact_id')
        partner_contact = self.pool.get('res.partner.contact').browse(cr, uid, contact_id)

        if partner_contact.dj_username or partner_contact.dj_email:
            result = _('This Django user exist.')

        if not partner_contact.email:
            result = _('This contact there are not email. Please add new email for this contact')

        if not result:
            #First Name / Last Name
            first_name = partner_contact.first_name or partner_contact.name
            last_name = partner_contact.name
            #firstname / lastname -- Replace accents
            first_name = unicodedata.normalize('NFKD', first_name).encode('ascii','ignore')
            last_name = unicodedata.normalize('NFKD', last_name).encode('ascii','ignore')

            #Username
            username = slugify(unicode(first_name+' '+last_name))
            #exist this username?
            usernames = self.pool.get('res.partner.contact').search(cr, uid, [('dj_username','=',username)])
            if len(usernames) > 0:
                username = username+str(len(usernames)+1)
            #Email
            email = partner_contact.email
            #Password
            char_set = string.ascii_uppercase + string.digits
            password = ''.join(random.sample(char_set,6))

            res = []
            school_ids = self.pool.get('training.school').search(cr, uid, [('django','=',True)])

            if len(school_ids) == 0:
                result = _('Error: Multi School not active')

            for school in self.pool.get('training.school').browse(cr, uid, school_ids):
                values = {
                    'ip': school.django_ip,
                    'port': school.django_port,
                    'username': school.django_username,
                    'password': school.django_password,
                    'key': school.django_key,
                    'ssh_key': school.django_ssh_key,
                    'basepath': school.django_basepath,
                }
                context['command'] = 'sync/user.py -u %s -p %s -o %s -e %s -f "%s" -l "%s"' % (username, password, contact_id, email, first_name, last_name)
                respy = self.pool.get('django.connect').ssh_command(cr, uid, school.id, values, context)
                res.append(_('School: %s Username: %s. %s') % (school.name, username, respy))

            if len(res)>0:
                for r in res:
                    result += r
            
            res_values['username'] = username
            res_values['password'] = password
            res_values['first_name'] = first_name
            res_values['last_name'] = last_name
            res_values['email'] = email

            #write partner dj info
            self.pool.get('res.partner.contact').write(cr, uid, [contact_id], {'dj_username': username, 'dj_email': email})

        res_values['state'] = 'done'
        res_values['result'] = result
        #write result values
        self.write(cr, uid, ids, res_values)
        
        self.pool.get('poweremail.templates').generate_mail(cr, uid, form.email_create_user.id, [form.id])

        return True

create_user_wizard()
