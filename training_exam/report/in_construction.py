# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu). All Rights Reserved
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

import time
import datetime
import math
from report import report_sxw
import pooler
import netsvc
from osv import osv, fields
from tools import debug

try:
    import cStringIO as StringIO
except:
    import StringIO as StringIO

class training_planned_exam_confirm_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_planned_exam_confirm_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.report.training.planned_exam.report',
                      'training.planned_exam',
                      'addons/training_exam/report/training_exam_confirm.rml',
                      parser=training_planned_exam_confirm_report,
                      header=True)

class training_planned_exam_cancel_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_planned_exam_cancel_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.planned_exam.cancel',
                      'training.planned_exam',
                      'addons/training_exam/report/training_exam_cancel.rml',
                      parser=training_planned_exam_cancel_report,
                      header=True)


class training_participation_exam_sheet(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        if not context:
            context = {}
        self.is_preview = context.get('preview', False)
        self.show_solution = context.get('show_solution', False)
        print("INIT# preview = %s, show_solution: %s" % (self.is_preview, self.show_solution))

        super(training_participation_exam_sheet, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'solution':self.solution,
            'get_image': self.get_image,
            'get_question_type_tips': self.get_question_type_tips,
            'get_question_point': self.get_question_point,
            'checkboxes_position':[], # needed in create_single_pdf
            'checkboxes_context':[], # needed in create_single_pdf
            'preformat': self.preformat,
            'get_plain_lines': self.get_plain_lines,
            'show_solution': self.do_show_solution,
            'get_partner_name': self.get_partner_name,
            'get_contact_name': self.get_contact_name,
            'get_questionnaire': self.get_questionnaire,
            'get_participation_id': self.get_participation_id,
            'get_participation_date': self.get_participation_date,
        })
        self.qcache = {}

    def preformat(self, string):
        lines = []
        for l in string.split('\n'):
            new_l = l.lstrip()
            full_l = u'\xa0' * (len(l) - len(new_l)) + new_l
            lines.append(full_l)
        return '\n'.join(lines)

    def do_show_solution(self):
        return bool(self.show_solution)

    def get_partner_name(self, participation):
        if self.is_preview:
            return 'DEMO PARTNER'
        return participation.partner_id.name

    def get_contact_name(self, participation):
        if self.is_preview:
            return 'John Doe'
        return participation.job_id.contact_id.name_get()[0][1]

    def get_participation_date(self, participation):
        if self.is_preview:
            return datetime.date.today()
        return participation.date

    def get_participation_id(self, participation):
        if self.is_preview:
            return participation # is really the questionnaire id
        return participation.id

    def get_questionnaire(self, participation):
        if self.is_preview:
            # participation is really the questionnaire_id
            if participation in self.qcache:
                return self.qcache[participation]
            b = self.pool.get('training.exam.questionnaire').browse(self.cr, self.uid, participation)
            self.qcache[participation] = b
            return b
        return participation.questionnaire_id

    def solution(self, question, question_type):
        _lt = self.localcontext['translate']
        res = []
        if question_type not in['plain','yesno']:
            self.cr.execute('select name,id,is_solution from training_exam_question_answer where question_id = %s',(question.id,))
            res = self.cr.dictfetchall()
            return res
        elif question_type =='yesno':
            print("RESPONSE YES/NO: %s" % (question.response_yesno))
            return  [{'name': _lt('Yes'), 'id': 0, 'is_solution': question.response_yesno == 'yes' and 'yes' or 'no'},
                     {'name': _lt('No'), 'id': 1, 'is_solution': question.response_yesno == 'no' and 'yes' or 'no'}]
        else: # plain
            return [ dict([('name', x+1),('id',-1)]) for x in range(question.free_lines_count or 10) ]

    def get_image(self, question, position):
        print("GET_IMAGE (%s)" % (position))

        if position != question.question_id.image_position:
            return ''
        print(type(question.question_id.image))
        image_data = question.question_id.image
        print("IMAGE DATA: %s" % (image_data[:215]))
        if image_data:
            return image_data
        return ''

    def get_question_type_tips(self, question_id):
        _lt = self.localcontext['translate']
        type = question_id.type
        if type in ('qcm'):
            return _lt('multiple responses')
        if type in ('qcu'):
            return _lt('one response')
        return ''

    def get_question_point(self, question_id):
        _lt = self.localcontext['translate']
        points = question_id.point
        float_p, int_p = math.modf(points)
        if float_p >= -0.00001 and float_p <= 0.00001:
            str_points = '%.0f' % (points)
        else:
            str_points = '%.2f' % (points)

        if points > 1:
            return _lt(r'%s points') % (str_points)
        else:
            return _lt(r'%s point') % (str_points)

    def get_plain_lines(self, question_id):
        lines = []
        max_chars = 143
        if not question_id.response_plain:
            lines.append('')
            return lines

        for line in question_id.response_plain.split('\n'):
            while len(line) > max_chars:
                for i, c in enumerate(reversed(line[:max_chars])):
                    if c.isspace():
                        lines.append(line[:max_chars-i])
                        line = line[max_chars-i:]
                        break
            lines.append(line)
        return lines

class report_attachment(object):
    def create_with_attachment(self, cr, uid, ids, data, original_doc, context=None):
        import base64
        from report.pyPdf import PdfFileReader, PdfFileWriter
        o = PdfFileWriter()

        pool = pooler.get_pool(cr.dbname)
        quizz_id = ids[0]

        if data.get('model', '') == 'training.participation':
            participation = pool.get('training.participation').browse(cr, uid, data['id'])
            quizz_id = participation.questionnaire_id.id

        quizz_proxy = pool.get('training.exam.questionnaire')
        quizz = quizz_proxy.browse(cr, uid, quizz_id)

        def write_orig_document():
            r = PdfFileReader(StringIO.StringIO(original_doc[0]))
            for p in range(r.getNumPages()):
                o.addPage(r.getPage(p))

        def generate_watermark_pdf(docid, basenum, npages):
            watermark_report = netsvc.LocalService('report.training.participation.watermark.qrcode')
            report_ids = [ '%s-%s%03d' % (docid, basenum, n+1) for n in range(npages) ]
            (result, format) = watermark_report.create(cr, uid, report_ids, {}, context=context)
            return PdfFileReader(StringIO.StringIO(result))

        attach_count = 0
        orig_doc_written = False
        for attach in quizz.attachment_ids:
            if attach.position == 'after' and not orig_doc_written:
                write_orig_document()
                orig_doc_written = True

            # 1 = annex and store
            # 2 = detect qrcode but don't store in the DMS
            basenum = '%1s%02d' % (attach.store_in_dms and 1 or 2, attach_count)

            attach_pdf_data = base64.decodestring(attach.attachment_id.datas)
            attach_pdf = PdfFileReader(StringIO.StringIO(attach_pdf_data))
            waterm_pdf = generate_watermark_pdf(ids[0], basenum, attach_pdf.getNumPages())

            for attach_page in range(attach_pdf.getNumPages()):
                docp = attach_pdf.getPage(attach_page)
                docp_wm = waterm_pdf.getPage(attach_page)
                docp.mergePage(docp_wm)
                o.addPage(docp)

            attach_count += 1
        if not orig_doc_written:
            write_orig_document()

        s = StringIO.StringIO()
        o.write(s)
        return (s.getvalue(), original_doc[1])

class report_and_store_checkboxes_position(report_sxw.report_sxw, report_attachment):
    def __init__(self, *args, **kwargs):
        super(report_and_store_checkboxes_position, self).__init__(*args, **kwargs)
        # FIXME cr is not defined here
        # self.training_scan_result = pooler.get_pool(cr.dbname).get('training.scan.result')

    def create(self, cr, uid, ids, data, context=None):
        if context:
            if 'preview' in context:
                del context['preview']
            if 'show_solution' in context:
                del context['show_solution']
        return super(report_and_store_checkboxes_position, self).create(cr, uid, ids, data, context=context)

    def create_single_pdf(self, cr, uid, ids, data, report_xml, context=None):
        # TODO regroup in context['report_misc_data']
        pool = pooler.get_pool(cr.dbname)
        context['checkboxes_position'] = [] # add a reference in context since it can't be modified during next call
        context['checkboxes_context'] = [] # add a reference in context since it can't be modified during next call
        context['participation_id'] = [] # add a reference in context since it can't be modified during next call

        # before generating document, dynamically assign questionnaire
        t_part_proxy = pool.get('training.participation')
        t_part_proxy.random_questionnaire_assign(cr, uid, ids)

        pdf, report_type = super(report_and_store_checkboxes_position, self).create_single_pdf(cr, uid, ids, data, report_xml, context)
        participation_id = int(context['participation_id'][0])
        training_scan_result = pool.get('position.storage')
        training_scan_result.save_checkboxes_position(cr, uid, 'training.participation', participation_id, context['checkboxes_position'], context['checkboxes_context'])

        # do other things afterward
        t_part_proxy.after_exam_sheet_generation(cr, uid, participation_id, context=context)

        return self.create_with_attachment(cr, uid, ids, data, (pdf, report_type), context=context)

class report_preview(report_sxw.report_sxw, report_attachment):
    def create(self, cr, uid, ids, data, context=None):
        if not context:
            context = {}
        context['preview'] = True
        z = super(report_preview, self).create(cr, uid, ids, data, context=context)
        return self.create_with_attachment(cr, uid, ids, data, z, context=context)

    def getObjects(self, cr, uid, ids, context):
        # for preview we have a fake object
        return ids

class report_preview_with_solution(report_preview):
    def create(self, cr, uid, ids, data, context=None):
        if not context:
            context = {}
        context['show_solution'] = True
        # we dont call create_with_attachment here because it will be done by report_preview.create
        return super(report_preview_with_solution, self).create(cr, uid, ids, data, context=context)

# Preview Original Exam Sheet (with solution)
report_preview_with_solution('report.training.exam.questionnaire.report',
                      'training.exam.questionnaire',
                      'addons/training_exam/report/exam_sheet.rml',
                      parser=training_participation_exam_sheet,
                      header=False)

# Preview Original Exam Sheet
report_preview('report.training.participation.report.preview',
               'training.exam.questionnaire',
               'addons/training_exam/report/exam_sheet.rml',
               parser=training_participation_exam_sheet,
               header=False)

# Exam Sheet Report
report_and_store_checkboxes_position('report.training.participation.report',
                                     'training.participation',
                                     'addons/training_exam/report/exam_sheet.rml',
                                     parser=training_participation_exam_sheet,
                                     header=False)

class training_participation_exam_result(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_participation_exam_result, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'is_partner_firstpage': self.is_partner_firstpage,
        })
        self.partner_firstpage_dict = {}
        self._cr = cr

    def is_partner_firstpage(self, participation):

        p_id = participation.partner_id.id
        if p_id not in self.partner_firstpage_dict:
            self.partner_firstpage_dict[p_id] = participation.id

        if participation.id == self.partner_firstpage_dict[p_id]:
            return True
        return False

class training_participation_exam_result_firstpage(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_participation_exam_result_firstpage, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'is_private_person': self.is_private_person,
        })

    def is_private_person(self, participation):
        state = False # Default, don't change previous behaviour
        if not participation:
            return state
        if not participation.partner_id:
            return state
        if not participation.partner_id.notif_contact_id:
            return state

        partner_name = participation.partner_id.name.split()
        contact = participation.partner_id.notif_contact_id.contact_id
        contact_name = contact.first_name.split() + contact.name.split()
        contact_name_rev = contact.name.split() + contact.first_name.split()

        def compare_names(x, y):
            if len(x) <> len(y):
                return False
            for k in range(len(x)):
                if x[k] <> y[k]:
                    return False
            return True # all identicals

        return compare_names(partner_name, contact_name) or \
               compare_names(partner_name, contact_name_rev)

class report_sxw_exam_result_custom(report_sxw.report_sxw):
    def getObjects(self, cr, uid, ids, context):
        """
        Result ids order by contact.name, contact.first_name for each group of reports
        """
        table_obj = pooler.get_pool(cr.dbname).get(self.table)

        cr.execute("""
            SELECT
                tp.id
            FROM
                res_partner_contact rpc,
                training_participation tp,
                training_subscription_line tsl,
                res_partner_job rpj
            WHERE
                    tp.subscription_line_id = tsl.id
                AND tsl.job_id = rpj.id
                AND rpj.contact_id = rpc.id
                AND tp.id in (%s)
            ORDER BY
                rpc.name, rpc.first_name
        """ % ','.join(map(str, map(int, ids))))
        sorted_ids = [ x[0] for x in cr.fetchall() ]

        return table_obj.browse(cr, uid, sorted_ids, list_class=report_sxw.browse_record_list,
                                context=context, fields_process=report_sxw._fields_process)


#report_sxw.report_sxw('report.training.participation.exam.result',
report_sxw_exam_result_custom('report.training.participation.exam.result',
                      'training.participation',
                      'addons/training_exam/report/training_exam_result.rml',
                      parser=training_participation_exam_result,
                      header=True)


report_sxw.report_sxw('report.training.participation.exam.result.firstpage',
                      'training.participation',
                      'addons/training_exam/report/training_exam_result_firstpage.rml',
                      parser=training_participation_exam_result_firstpage,
                      header=True)


class training_seance_exam_followup_list(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_seance_exam_followup_list, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_': self._translate,
            'ordered_participants': self.ordered_participants,
        })

    def repeatIn(self, lst, name, nodes_parent=False):
        """improved version"""
        for e in lst:
            yield {name: e}

    def ordered_participants(self, seance):
        participants = list(seance.participant_ids)
        participants.sort(key=lambda p: (p.contact_id.name, p.contact_id.first_name))
        for participant in participants:
            yield participant

report_sxw.report_sxw('report.training.seance.exam.followup.list.report',
                       'training.seance',
                      'addons/training_exam/report/training_seance_exam_followup_list.rml',
                      parser=training_seance_exam_followup_list,
                      header=False)

report_sxw.report_sxw('report.training.seance.exam.labels.report',
                      'training.seance',
                      'addons/training_exam/report/training_seance_exam_labels.rml',
                      parser=training_seance_exam_followup_list,
                      header=False)

class report_participation_watermark_qrcode(report_sxw.report_sxw):
    def getObjects(self, cr, uid, ids, context):
        return ids

report_participation_watermark_qrcode('report.training.participation.watermark.qrcode',
                                      'training.participation',
                                      'addons/training_exam/report/watermark_qrcode.rml',
                                      header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

