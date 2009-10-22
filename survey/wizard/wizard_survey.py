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

import wizard
import time
import pooler
from random import choice
import string
import tools

_survey_form = '''<?xml version="1.0"?>
<form string="Select a Partner Name">
    <field name="partner_ids" nolabel="1" /> 
        <separator colspan="4"/>
    <group cols="4" colspan="4">
    <field name="mail_subject"/>
    <newline/>
    <field name="mail_from"/>
    <newline/>
    <separator string="Message" colspan="4"/>
    <field name="mail" nolabel="1" colspan="4"/>
      </group>
</form>'''


_survey_fields = {
    'partner_ids': {'string': 'Partner', 'type': 'many2many', 'relation': 'res.partner'},
    'mail_subject': {'string':'Subject', 'type':'char', 'default':lambda *a: "New user account.","size":256},
    'mail_from': {'string':'From', 'type':'char',"size":256},
    'mail': {'string':'Body', 'type':'text','default':lambda *a: """ Your login: %(login)s, Your password: %(passwd)s
    \n link :- http://localhost:8080"""},
    }

second_form = '''<?xml version="1.0"?>
<form string="User creation">
    <separator string="Results :" colspan="4"/>
    <field name="note" colspan="4" nolabel="1"/>
</form>'''
second_fields = {
    'note' : {'string':'Log','type':'text'}
    }
def genpasswd():
    chars = string.letters + string.digits
    return ''.join([choice(chars) for i in range(6)])


def send_mail(self, cr, uid, data, context):
    partner_ids = data['form']['partner_ids'][0][2]
    pool= pooler.get_pool(cr.dbname)
    user_ref= pool.get('res.users')
    group_id= pool.get('res.groups').search(cr,uid,[('name','=','Survey / User')])
    act_id = pool.get('ir.actions.act_window')
    act_id = act_id.search(cr,uid,[('name','=','Start to Give Survey Response'),('res_model','=','survey.name.wiz'),('view_type','=','form')])
    out="login,password\n"
    skipped= 0
    existing= ""
    created= ""
    for partner in pool.get('res.partner').browse(cr,uid,partner_ids):
        for addr in partner.address:
            if not addr.email:
                skipped+= 1
                continue
            user = user_ref.search(cr,uid,[('login',"=",addr.email)])

            if user:
                user = user_ref.browse(cr,uid,user[0])
                user_ref.write(cr,uid,user.id,{'survey_id':[[6, 0, data['ids']]]})
                existing+= "- %s (Login: %s,  Password: %s)\n"%(user.name,addr.email,user.password)
                mail= data['form']['mail']%{'login':addr.email, 'passwd':user.password}
#                if data['form']['send_mail_existing']:
#                    if not data['form']['mail_from']: raise wizard.except_wizard('Error !', 'Please provide a "from" email address.')
#                    tools.email_send(data['form']['mail_from'],[addr.email] ,data['form']['mail_subject_existing'] ,mail )
                continue

            passwd= genpasswd()
            out+= addr.email+','+passwd+'\n'
            user = user_ref.create(cr,uid,{'name': addr.name or 'Unknown',
                                    'login': addr.email,
                                    'password': passwd,
                                    'groups_id': [[6,0,group_id]],
                                    'action_id': 101,
                                   })
            user_ref.write(cr,uid,user,{'survey_id':[[6, 0, data['ids']]]})
            mail= data['form']['mail']%{'login':addr.email, 'passwd':passwd}
            if not data['form']['mail_from']: raise wizard.except_wizard('Error !', 'Please provide a "from" email address.')
            tools.email_send(data['form']['mail_from'],[addr.email] ,data['form']['mail_subject'] ,mail )
            created+= "- %s (Login: %s,  Password: %s)\n"%(addr.name or 'Unknown',addr.email,passwd)
        
    note= ""
    if created:
        note+= 'Created users:\n%s\n'%(created)
    if existing:
        note+='Already existing users:\n%s\n'%(existing)
    if skipped:
        note+= "%d contacts where ignored (an email address is missing).\n"%(skipped)
    return {'note': note}
    

class send_mail_wizard(wizard.interface):
    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch':_survey_form, 'fields':_survey_fields, 'state':[('end','Cancel','gtk-cancel'),('send','Send','gtk-go-forward')]}
                },
        'send':{'actions': [send_mail],
               'result': {'type':'form',
                          'arch':second_form,
                          'fields':second_fields,
                          'state':[('end','_Ok')]}
               },
    }
send_mail_wizard('wizard.send.invitation')
