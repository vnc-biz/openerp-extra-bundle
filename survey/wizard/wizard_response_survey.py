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

_survey_form = '''<?xml version="1.0"?>
<form string="Select a survey Name">
    <separator string="Select a Survey" colspan="4"/>
        <field name="survey_id" />
        <newline/>
        <field name="page_id" domain="[('survey_id','=', survey_id)]"/>
        <newline/>
        <field name="question_id" domain="[('page_id','=', page_id)]" />
 </form>'''

_survey_fields = {
    'survey_id': {'string':'Survey ', 'type':'many2one','relation':'survey'},
    'page_id': {'string':'Page ', 'type':'many2one','relation':'survey.page'},
    'question_id': {'string':'Question ', 'type':'many2one','relation':'survey.question'},
    }

def _open_report(self, cr, uid, data, context={}):
    pool = pooler.get_pool(cr.dbname)
    view_obj = pool.get('ir.ui.view')
    view_id = view_obj.search(cr,uid,[('model','=','report.survey.question'),('type','=','tree')])
    pag_obj = pool.get('survey.page')
    que_id = []
    
    if not data['form']['survey_id']:
        que_obj = pool.get('survey.question')
        for que in que_obj.read(cr,uid,que_obj.search(cr,uid,[])):
            que_id.append(que['id'])
    
    elif not data['form']['page_id']:
        pag_id = pag_obj.search(cr,uid,[('survey_id','=',data['form']['survey_id'])])
        for page in pag_obj.read(cr,uid,pag_id):
            for que in page['question_ids']:
                que_id.append(que)
    
    elif not data['form']['question_id']:
        for page in pag_obj.read(cr,uid,[data['form']['page_id']]):
            for que in page['question_ids']:
                que_id.append(que)
    else:
        que_id.append(data['form']['question_id'])
        
    domain = [('que_id','in',que_id)]
    return {
            'domain': domain,
            'name': 'Survey Responce Report',
            'view_type': 'form',
            'view_mode': 'tree,form,graph',
            'res_model': 'report.survey.question',
            'view_id': view_id,
            'type': 'ir.actions.act_window'
            }

class wiz_resp_survey(wizard.interface):
    
    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch':_survey_form, 'fields':_survey_fields, 'state':[('end','Cancel','gtk-cancel'),('next','Next','gtk-go-forward')]}
                },
        'next': {
            'actions': [],
            'result': {'type': 'action','action':_open_report, 'state': 'end'}
                }
            }
wiz_resp_survey('wizard.response.survey')
