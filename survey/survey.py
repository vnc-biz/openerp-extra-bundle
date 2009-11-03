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

from osv import fields, osv
import datetime
from time import strftime
import copy

class survey(osv.osv):
    _name = 'survey'
    _description = 'Survey'
    _rec_name = 'title'
    _columns = {  
        'title' : fields.char('Survey Title', size=128, required=1),
        'page_ids' : fields.one2many('survey.page','survey_id','Page'),
        'date_open' : fields.datetime('Survey Open Date', readonly=1),
        'date_close' : fields.datetime('Survey Close Date', readonly=1),
        'max_response_limit' : fields.integer('Maximum Response Limit'),
        'state' : fields.selection([('draft','Draft'),('open','Open'),('close','Closed'),('cancel','Cancelled')],'Status',readonly = True),
        'responsible_id' : fields.many2one('res.users','Responsible'),
        'tot_start_survey' : fields.integer("Total Started Survey", readonly = 1),
        'tot_comp_survey' : fields.integer("Total Completed Survey", readonly = 1),
        'note' : fields.text('Description', size=128),
    }
    _defaults = {
        'state' : lambda *a: "draft",
        'tot_start_survey' : lambda *a: 0,
        'tot_comp_survey' : lambda *a: 0
    }
    
    def survey_draft(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'draft'})
        return True
     
    def survey_open(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'open','date_open':strftime("%Y-%m-%d %H:%M:%S")})
        return True
     
    def survey_close(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'close', 'date_close':strftime("%Y-%m-%d %H:%M:%S") })
        return True
     
    def survey_cancel(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'cancel' })
        return True
    
survey()

class survey_page(osv.osv):
    _name = 'survey.page'
    _description = 'Survey Pages'
    _rec_name =  'title'
    _order = 'sequence'
    _columns = {
        'title' : fields.char('Page Title', size = 128,required=1),
        'survey_id' : fields.many2one('survey', 'Survey', ondelete='cascade'),
        'question_ids' : fields.one2many('survey.question','page_id','Question'),
        'sequence' : fields.integer('Sequence'),
        'note' : fields.text('Description'),
    }
    _defaults = {
         'sequence' : lambda *a: 5
    }

survey_page()

class survey_question(osv.osv):
    _name = 'survey.question'
    _description = 'Survey Question'
    _rec_name = 'question'
    _order = 'sequence'
    def _calc_response(self, cr, uid, ids, field_name, arg, context):
        val = {}
        cr.execute("select question_id, count(id) as Total_response from survey_response where question_id in (%s) group by question_id" % ",".join(map(str,map(int,ids))))
        ids1 = copy.deepcopy(ids)
        for rec in  cr.fetchall():
            ids1.remove(rec[0])
            val[rec[0]] = int(rec[1])
        for id in ids1:
            val[id] = 0
        return val

    _columns = {
        'page_id' : fields.many2one('survey.page','Survey Page', ondelete='cascade'),
        'question' :  fields.char('Question', size = 128,required=1),
        'answer_choice_ids' : fields.one2many('survey.answer','question_id','Answer'),
        'response_ids' : fields.one2many('survey.response','question_id','Response', readonly=1),
        'is_require_answer' : fields.boolean('Required Answer'),
        'allow_comment' : fields.boolean('Allow Comment Field'),
        'sequence' : fields.integer('Sequence'),
        'tot_resp' : fields.function(_calc_response,method = True, string ="Total Response"),
        'survey':fields.related('page_id','survey_id',type='many2one', relation='survey', string='Survey'),        
    }
    _defaults = {
         'sequence' : lambda *a: 5
    }

    
survey_question()

class survey_answer(osv.osv):
    _name = 'survey.answer'
    _description = 'Survey Answer'
    _rec_name = 'answer'
    _order = 'sequence'
    def _calc_response_avg(self, cr, uid, ids, field_name, arg, context):
        val = {}
        for rec in self.browse(cr, uid, ids):
            cr.execute("select count(question_id) ,(select count(answer_id) from survey_response_answer sra  where sra.answer_id = %d group by sra.answer_id)  from survey_response where question_id = %d" % (rec.id, rec.question_id.id))
            res = cr.fetchone()
            if res[1]:
                avg = float(res[1]) * 100 /res[0]
            else:
                avg = 0.0
            val[rec.id] = {
                'response': res[1],
                'average': round(avg,2),
            }
        return val
    _columns = {
        'question_id' : fields.many2one('survey.question', 'Question',ondelete='cascade'),
        'answer' : fields.char('Answer', size = 128,required=1),
        'sequence' : fields.integer('Sequence'),
        'response' : fields.function(_calc_response_avg,method =True, string ="#Response",multi='sums'),
        'average' : fields.function(_calc_response_avg,method =True, string ="#Avg",multi='sums')                
    }
    _defaults = {
         'sequence' : lambda *a: 5
    }

survey_answer()

class survey_response(osv.osv):
    _name = 'survey.response'
    _description = 'Survey Response'
    _rec_name = 'date_create'
    _columns = {
        'date_create' : fields.datetime('Create Date', required=1),
        'date_modify' : fields.datetime('Modify Date'),
        'state' : fields.selection([('draft', 'Draft'),('done', 'Done'), ('skip','Skip')], 'Status', readonly = True),
        'response_id' : fields.many2one('res.users', 'User'),
        'question_id' : fields.many2one('survey.question', 'Question', ondelete='cascade'),
        'response_type' : fields.selection([('manually','Manually'),('link','Link')],'Response Type'),
        'response_answer_ids' : fields.one2many('survey.response.answer', 'response_id', 'Response Answer'),
        'comment' : fields.text('Notes'),                
    }
    _defaults = {
        'state' : lambda *a: "draft"
    }
    
    def response_draft(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'draft' })
        return True
     
    def response_done(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'done' })
        return True
     
    def response_skip(self, cr, uid, ids, arg):
        self.write(cr, uid, ids, { 'state' : 'skip' })
        return True

survey_response()

class survey_response_answer(osv.osv):
    _name = 'survey.response.answer'
    _description = 'Survey Response Answer'
    _rec_name = 'response_id'
    _columns = {
        'response_id' : fields.many2one('survey.response', 'Response', ondelete='cascade'),
        'answer_id' : fields.many2one('survey.answer', 'Answer', required=1, ondelete='cascade'),
        'comment' : fields.text('Notes'),                
    }

survey_response_answer()


class survey_name_wiz(osv.osv_memory):
    _name = 'survey.name.wiz'

    def _get_survey(self, cr, uid, context=None):
        surv_obj = self.pool.get("survey")
        result = []
        group_id = self.pool.get('res.groups').search(cr, uid, [('name', '=', 'Survey / Manager')])
        user_obj = self.pool.get('res.users')
        user_rec = user_obj.read(cr, uid, uid)
        for sur in surv_obj.browse(cr, uid, surv_obj.search(cr, uid, [])):
            if sur.state == 'open':
                if group_id[0]  in user_rec['groups_id']:
                    result.append((sur.id, sur.title))
                elif sur.id in user_rec['survey_id']:
                    result.append((sur.id, sur.title))
        return result

    _columns = {
        'survey_id': fields.selection(_get_survey, "Survey", required = "1"),
        'page_no' : fields.integer('Page Number'),
        'note' : fields.text("Description"),
    }
    _defaults = {
        'page_no' : lambda *a: 0
    }

    def action_next(self, cr, uid, ids, context=None):
        sur_id = self.read(cr, uid, ids, [])[0]
        context.update({'survey_id' : sur_id['survey_id'], 'sur_name_id' : sur_id['id']})
        return {
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'survey.question.wiz',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context' : context
         }

    def on_change_survey(self, cr, uid, ids, survey_id, context=None):
        notes = self.pool.get('survey').read(cr, uid, survey_id, ['note'])['note']
        return {'value': {'note' : notes}}

survey_name_wiz()

class survey_question_wiz(osv.osv_memory):
    page = True

    _name = 'survey.question.wiz'
    _columns = {
        'name': fields.integer('Number'),
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        result = super(survey_question_wiz, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
        surv_name_wiz = self.pool.get('survey.name.wiz')
        sur_name_rec = surv_name_wiz.read(cr, uid, context['sur_name_id'])[0]
        survey_id = context['survey_id']
        survey_obj = self.pool.get('survey')
        sur_rec = survey_obj.read(cr, uid, survey_id, [])
        page_obj = self.pool.get('survey.page')
        que_obj = self.pool.get('survey.question')
        ans_obj = self.pool.get('survey.answer')
        p_id = sur_rec['page_ids']
        if self.page or not sur_name_rec['page_no'] :
            self.page = False
            if len(p_id) > sur_name_rec['page_no']:
                
                if not sur_name_rec['page_no']:
                    survey_obj.write(cr, uid, survey_id, {'tot_start_survey' : sur_rec['tot_start_survey'] + 1})                
                if sur_rec['max_response_limit'] and sur_rec['max_response_limit'] <= sur_rec['tot_start_survey'] + 1 and not sur_name_rec['page_no']:
                    survey_obj.write(cr, uid, survey_id, {'state':'close', 'date_close':strftime("%Y-%m-%d %H:%M:%S")})
                p_id = p_id[sur_name_rec['page_no']]
                surv_name_wiz.write(cr, uid, [context['sur_name_id']], {'page_no' : sur_name_rec['page_no'] + 1})
                fields = {}
                pag_rec = page_obj.read(cr, uid, p_id)
                xml = '''<?xml version="1.0" encoding="utf-8"?> <form string="''' + str(pag_rec['title']) + '''">'''
                xml += '''<label string="'''+ str(pag_rec['note'] or '') + '''"/> <newline/> <newline/><newline/>'''
                que_ids = pag_rec['question_ids']
                qu_no = 0
                for que in que_ids:
                    qu_no += 1
                    que_rec = que_obj.read(cr, uid, que)
                    xml += '''<separator string="''' + str(qu_no) + "."  + str(que_rec['question']) + '''"  colspan="4"/> <newline/> '''
                    ans_ids = ans_obj.read(cr, uid, que_rec['answer_choice_ids'], [])
                    for ans in ans_ids:
                        xml += '''<field  name="'''+ str(que) + "_" +  str(ans['id']) + '''"/> '''
                        fields[str(que) + "_" +  str(ans['id'])] = {'type':'boolean','string':ans['answer'],'views':{}}
                    if que_rec['allow_comment']:
                        xml += '''<newline/><label string="Add Coment"  colspan="4"/> '''                    
                        xml += '''<field nolabel="1"  colspan="4"  name="''' + str(que) + "_other" '''"/> '''
                        fields[str(que) + "_other"] = {'type':'text', 'string':"Comment", 'views':{}}
                xml += '''
                <separator colspan="4" />
                    <label align="0.0" colspan="2" string=""/>    
                    <button colspan="1" icon="gtk-cancel"  special="cancel" string="Cancel"/>
                    <button colspan="1" icon="gtk-go-forward" name="action_next" string="Next" type="object"/>
                </form>'''
                result['arch'] = xml
                result['fields'] = fields
            else:
                survey_obj.write(cr, uid, survey_id, {'tot_comp_survey' : sur_rec['tot_comp_survey'] + 1})
                xml_form ='''<?xml version="1.0"?>
                            <form string="Complete Survey Response">
                                <separator string="Complete Survey" colspan="4"/>
                                    <label string = "Thanks for your response" />
                                    <newline/>
                                    <button colspan="2" icon="gtk-go-forward"  special="cancel" string="OK"/>
                             </form>'''
                result['arch'] = xml_form
                result['fields'] = {}
        return result
    
    def create(self, cr, uid, vals, context=None):
        resp_obj = self.pool.get('survey.response')
        res_ans_obj = self.pool.get('survey.response.answer')
        que_obj = self.pool.get('survey.question')
        que_li = []
        for key, val in vals.items():
            que_id = key.split('_')[0]
            if que_id not in que_li:
                ans = False
                que_li.append(que_id)
                que_rec = que_obj.read(cr, uid ,[que_id], ['is_require_answer','question'])
                resp_id = resp_obj.create(cr, uid, {'response_id':uid, 'question_id':que_id, 'date_create':datetime.datetime.now(), 'response_type':'link'})
                for key1, val1 in vals.items():
                    if val1 and key1.split('_')[1] =="other" and key1.split('_')[0] == que_id:
                        resp_obj.write(cr, uid, resp_id, {'comment':val1})
                        ans = True
                    elif val1 and que_id == key1.split('_')[0]:
                        ans_id_len = key1.split('_')
                        res_ans_obj.create(cr,uid,{'response_id':resp_id, 'answer_id' : ans_id_len[len(ans_id_len) -1]})
                        ans = True
                if que_rec[0]['is_require_answer'] and not ans:
                    raise osv.except_osv(_('Error !'),_("'" + que_rec[0]['question'] + "' This question requires an answer."))
        return True
    def action_next(self, cr, uid, ids, context=None):
        self.page = True
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': context
                }
            
survey_question_wiz()

class res_users(osv.osv):
    _inherit = "res.users"
    _name = "res.users"
    _columns = {
        'survey_id': fields.many2many('survey', 'survey_users_rel', 'uid', 'sid', 'Groups'),
    }
res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: