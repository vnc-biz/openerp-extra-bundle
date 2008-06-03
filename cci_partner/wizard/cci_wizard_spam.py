##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: wizard_spam.py 1005 2005-07-25 08:41:42Z nicoe $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import wizard
import pooler
import tools

email_send_form = '''<?xml version="1.0"?>
<form string="Mass Mailing">
    <field name="from"/>
    <newline/>
    <field name="subject"/>
    <newline/>
    <field name="text"/>
    <newline/>
    <field name="event"/>
</form>'''

email_send_fields = {
    'from': {'string':"Sender's email", 'type':'char', 'size':64, 'required':True},
    'subject': {'string':'Subject', 'type':'char', 'size':64, 'required':True},
    'text': {'string':'Message', 'type':'text_tag', 'required':True},
    'event': {'string':'Open Partners for Event History', 'type':'boolean'},
}

# this sends an email to ALL the addresses of the selected partners.
def _mass_mail_send(self, cr, uid, data, context):
    nbr = 0
    partners = pooler.get_pool(cr.dbname).get('res.partner').browse(cr, uid, data['ids'], context)
    for partner in partners:
        for adr in partner.address:
            if adr.email:
                name = adr.name or partner.name
                to = '%s <%s>' % (name, adr.email)
#TODO: add some tests to check for invalid email addresses
#CHECKME: maybe we should use res.partner/email_send
                tools.email_send(data['form']['from'], [to], data['form']['subject'], data['form']['text'])
                nbr += 1
        pooler.get_pool(cr.dbname).get('res.partner.event').create(cr, uid,
                {'name': 'Email sent through mass mailing',
                 'partner_id': partner.id,
                 'description': data['form']['text'], })

    if data['form']['event']:
        return 'open'
    return 'ok'

class part_email(wizard.interface):
     def _open_partners(self, cr, uid, data, context):
         pool_obj = pooler.get_pool(cr.dbname)
         model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_partner_form')])
         resource_id = pool_obj.get('ir.model.data').read(cr,uid,model_data_ids,fields=['res_id'])[0]['res_id']
         return {
            'domain': "[('id','in', ["+','.join(map(str,data['ids']))+"])]",
            'name': 'Partners',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'views': [(False,'tree'),(resource_id,'form')],
            'type': 'ir.actions.act_window'
        }
     states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch': email_send_form, 'fields': email_send_fields, 'state':[('end','Cancel'), ('send','Send Email')]}
        },
        'send': {
            'actions': [],
            'result' : {'type': 'choice', 'next_state': _mass_mail_send }
        },
        'ok':{
          'actions': [],
          'result': {'type': 'state', 'state':'end'}
              },
        'open': {
            'actions': [],
            'result': {'type':'action', 'action':_open_partners, 'state':'end'}
                }
    }
part_email('res.partner.spam_send_cci')