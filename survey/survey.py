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

question_no = 0

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
                'state' : fields.selection([('draft','Draft'),('open','Open'),('close','Close'),('cancel','Cancel')],'Status',readonly = True),
                'responsible_id' : fields.many2one('res.users','Responsible'),
    }
    _defaults = {
        'state' : lambda *a: "draft"
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
                'survey_id' : fields.many2one('survey', 'Survey'),
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
    def _calc_response(self,cr,uid,ids,field_name,arg,context):
        val = {}
        for rec in self.browse(cr,uid,ids,[]):
            cr.execute("select count(question_id) from survey_response where question_id = " + str(rec.id))
            val[rec.id] = cr.fetchall()[0][0]
        return val
    _columns = {
                'page_id' : fields.many2one('survey.page','Survey Page'),
                'question' :  fields.char('Question', size = 128,required=1),
                'answer_choice_ids' : fields.one2many('survey.answer','question_id','Answer'),
                'response_ids' : fields.one2many('survey.response','question_id','Response',readonly=1),
                'is_require_answer' : fields.boolean('Required Answer'),
                'allow_comment' : fields.boolean('Allow Comment Field'),
                'sequence' : fields.integer('Sequence'),
                'tot_resp' : fields.function(_calc_response,method =True, string ="Total Response"),
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
    def _calc_response_avg(self,cr,uid,ids,field_name,arg,context):
        val = {}
        for rec in self.browse(cr,uid,ids,[]):
            cr.execute("select count(question_id) from survey_response where question_id = " + str(rec.question_id.id))
            tot = cr.fetchone()[0]
            cr.execute("select count(answer_id) from survey_response_answer sra  where sra.answer_id = "+str(rec.id))
            res = cr.fetchone()[0]
            if res:
                avg = res * 100 /tot
            else:
                avg = 0.0
            val[rec.id] = {
                'response': res,
                'average': avg,
            }                
        return val
    _columns = {
                'question_id' : fields.many2one('survey.question', 'Question'),
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
    _rec_name = 'date_start'
    _columns = {
                'date_create' : fields.datetime('Create Date',required=1),
                'date_modify' : fields.datetime('Modify Date'),
                'state' : fields.selection([('draft', 'Draft'),('done', 'Done'), ('skip',' Skip')], 'Status', readonly = True),
                'response_id' : fields.many2one('res.users', 'Responsibal User'),
                'question_id' : fields.many2one('survey.question', 'Question'),
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
                'response_id' : fields.many2one('survey.response','Response'),
                'answer_id' : fields.many2one('survey.answer','Answer',required=1),
                'comment' : fields.text('Notes'),                
    }

survey_response_answer()


class survey_name_wiz(osv.osv_memory):
    _name = 'survey.name.wiz'
    _columns = {
        'survey_id': fields.many2one('survey',"Survey",required = "1"),
    }
    
    def action_next(self, cr, uid, ids, context=None):
        global question_no
        question_no = 0
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
         }
survey_name_wiz()

class survey_question_wiz(osv.osv_memory):
    _name = 'survey.question.wiz'
    _columns = {
        'name': fields.text('statistics'),
    }
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        result = super(survey_question_wiz, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
        global question_no
        survey_name_obj = self.pool.get('survey.name.wiz')
        surv_id = survey_name_obj.search(cr,uid,[])
        survey_id = survey_name_obj.read(cr,uid,surv_id[int(len(surv_id) -1)],[])[0]['survey_id']
        sur_rec = self.pool.get('survey').read(cr,uid,survey_id,[])
        page_obj = self.pool.get('survey.page')
        que_obj = self.pool.get('survey.question')
        ans_obj = self.pool.get('survey.answer')
        p_id = page_obj.search(cr,uid,[])
        if len(p_id) > question_no:
            p_id = p_id[question_no]
            question_no += 1
            xml = '''<?xml version="1.0" encoding="utf-8"?> <form string="Select a survey Name">'''
            fields = {}
            pag_rec = page_obj.read(cr,uid,p_id)
            xml += '''<separator string="'''+ str(question_no)+"." + str(pag_rec['title']) + '''" colspan="4"/>'''
            xml += '''<label string="'''+ str(pag_rec['note']) + '''"/> <newline/> <newline/><newline/>'''
            que_ids = pag_rec['question_ids']
            qu_no = 0
            for que in que_ids:
                qu_no += 1
                que_rec = que_obj.read(cr,uid,que)
                xml += '''<separator string="''' + str(qu_no) + "."  + str(que_rec['question']) + '''"  colspan="4"/> <newline/> '''
                ans_ids = ans_obj.read(cr,uid,que_rec['answer_choice_ids'],[])
                for ans in ans_ids:
                    xml += '''<field  name="'''+ str(que) + "_" + ans['answer'] +"_" + str(ans['id']) +  '''"/> '''
                    fields[str(que) + "_" + ans['answer'] +"_" + str(ans['id']) ] = {'type':'boolean','string':ans['answer'],'views':{}}
                if que_rec['allow_comment']:
                    xml += '''<newline/> <field  colspan="4"  name="'''+ str(que) + "_other" '''"/> '''
                    fields[str(que) + "_other"] = {'type':'text','string':"Comment",'views':{}}
            xml += '''
            <separator colspan="4" />
            <group col="4" colspan="4">
                <button colspan="2" icon="gtk-cancel" readonly="0" special="cancel" string="Cancel"/>
                <button icon="gtk-go-forward" name="action_next" string="Next" type="object"/>
            </group>
            </form>'''
            result['arch'] = xml
            result['fields']=fields
        else:
            xml_form ='''<?xml version="1.0"?>
                        <form string="Complete Survey Response">
                            <separator string="Complete Survey" colspan="4"/>
                                <label string = "Thanks for your response" />
                                <newline/>
                                <button colspan="2" icon="gtk-go-forward" readonly="0" special="cancel" string="OK"/>
                         </form>'''
            question_no = 0
            result['arch'] = xml_form
            result['fields']={}
            return result
        return result
    
    def create(self, cr, uid, vals, context=None):
        resp_obj = self.pool.get('survey.response')
        res_ans_obj = self.pool.get('survey.response.answer')
        que_obj = self.pool.get('survey.question')
        que_li = []
        for key,val in vals.items():
            que_id = key.split('_')[0]
            if que_id not in que_li:
                ans = False
                que_li.append(que_id)
                que_rec = que_obj.read(cr,uid,que_id,['is_require_answer'])
                resp_id = resp_obj.create(cr,uid,{'response_id':uid,'question_id':que_id,'date_create':datetime.datetime.now(),'response_type':'link'})
                for key1,val1 in vals.items():
                    if val1 and key1.split('_')[1] =="other":
                        resp_obj.write(cr,uid,resp_id,{'comment':val1})
                        ans = True
                    elif val1 and que_id == key1.split('_')[0]:
                        ans_id_len = key1.split('_')
                        res_ans_obj.create(cr,uid,{'response_id':resp_id,'answer_id':ans_id_len[len(ans_id_len) -1]})
                        ans = True
                if que_rec[0]['is_require_answer'] and not ans:
                    raise osv.except_osv(_('Error !'),_('This question requires an answer.'))
        return True
    def action_next(self, cr, uid, ids, context=None):
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'survey.question.wiz',
                'type': 'ir.actions.act_window',
                'target': 'new',
                }
            
survey_question_wiz()

class report_survey_question(osv.osv):
    _name = "report.survey.question"
    _description = "Survey Question Report"
    _auto = False
    def _calc_response_avg(self,cr,uid,ids,field_name,arg,context):
        val = {}
        for rec in self.browse(cr,uid,ids):
            if rec.res_que_count:
                val[rec.id] = rec.res_ans_count *100 / rec.res_que_count
            else:
                val[rec.id] = 0  
        return val
    _columns = {
        'que_id': fields.many2one('survey.question','Question'),
        'ans_id': fields.many2one('survey.answer','Answer'),
        'res_ans_count': fields.integer('Response Answer Count'),
        'res_que_count': fields.integer('Response Question Count'),
        'res_avg' : fields.function(_calc_response_avg,method =True, string ="Response Average(%)")
    }
    def init(self, cr):
        cr.execute("""
                create or replace view report_survey_question as (
                select 
                    sa.id as id,
                    sq.id as que_id, 
                    sa.id as ans_id, 
                    (select count(answer_id) from survey_response_answer sra where sa.id = sra.answer_id) as res_ans_count ,
                    (select count(question_id) from survey_response where question_id = sa.question_id   group by question_id) as res_que_count
                from 
                    survey_question sq, survey_answer sa 
                where sq.id = sa.question_id )
                """)

report_survey_question()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: