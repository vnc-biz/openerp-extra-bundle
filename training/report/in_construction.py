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
from report import report_sxw

class training_subscription_cancel_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_subscription_cancel_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.subscription.cancel',
                      'training.subscription',
                      'addons/training/report/training_subscription_cancel.rml',
                      parser=training_subscription_cancel_report,
                      header=True)

class training_subscription_confirm_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_subscription_confirm_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.subscription.confirm',
                      'training.subscription',
                      'addons/training/report/training_subscription_confirm.rml',
                      parser=training_subscription_confirm_report,
                      header=True)

class training_seance_presence_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_seance_presence_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'present':self._present
        })
    def _present(self,id):
            res=[]
            self.cr.execute('select present from training_participation where id =%s',(id,))
            res=self.cr.fetchall()
            if res[0][0]==True:
                return 'Yes'
            return res and res[0][0] or 'No'

report_sxw.report_sxw('report.training.seance.presence',
                      'training.seance',
                      'addons/training/report/training_presence.rml',
                      parser=training_seance_presence_report,
                      header=True)


class training_course_material_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_course_material_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.course.material.report',
                      'training.course',
                      'addons/training/report/training_course.rml',
                      parser=training_course_material_report,
                      header=True)

class training_subscription_presence_certificate_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_subscription_presence_certificate_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.subscription.presence.certificate',
                      'training.subscription',
                      'addons/training/report/training_presence_certificate.rml',
                      parser=training_subscription_presence_certificate_report,
                      header=True)

import tools
class training_seance_support_delivery_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_seance_support_delivery_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'list_seances': self.list_seances,
            'list_pl': self.list_pl,
            'additional_info': self.additional_info,
        })

    def _is_valid(self, product):
        partner = self.localcontext.get('partner', None)
        if not partner:
            # no partner given ? ok, we list all, allowing the report to be usable by normal users
            return True

        return any(seller.name == partner for seller in product.seller_ids)

    def repeatIn(self, lst, name, nodes_parent=False):
        """improved version"""
        for e in lst:
            yield {name: e}

    def list_seances(self):
        seances = self.localcontext['objects']
        for seance in seances:
            if any(self._is_valid(pl.product_id) for pl in seance.purchase_line_ids):
                yield seance

    def list_pl(self, seance):
        for pl in seance.purchase_line_ids:
            if self._is_valid(pl.product_id):
                yield pl

    def additional_info(self, pl):
        r = ''
        attach = pl.attachment_id
        if attach and attch.is_support:
            r = 'Attachment Name: %s' % (attach.name,)
            for component in attach.component_ids:
                if self._is_valid(component.product_id):
                    r += "\n\t%s\t%s" % (component.product_qty, component.product_id.name)

        return r


report_sxw.report_sxw('report.training.seance.support.delivery.report',
                      'training.seance',
                      'addons/training/report/delivery_support.rml',
                      parser=training_seance_support_delivery_report,
                      header=True)

class training_seance_cancel_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_seance_cancel_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.seance.cancel.report',
                      'training.seance',
                      'addons/training/report/training_seance_cancel.rml',
                      parser=training_seance_cancel_report,
                      header=True)

class training_session_cancel_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_session_cancel_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.session.cancel.report',
                      'training.session',
                      'addons/training/report/training_session_cancel.rml',
                      parser=training_session_cancel_report,
                      header=True)

class training_dummy_training_hiring_form_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_dummy_training_hiring_form_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.dummy.training.hiring.form.report',
                      'dummy.support.delivery',
                      'addons/training/report/training_hiring_form.rml',
                      parser=training_dummy_training_hiring_form_report,
                      header=True)



class training_catalog_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_catalog_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'offer_session':self.offer_session,
            'offer_name':self.offer_name
        })
    def offer_session(self):
        res=[]
        result=[]
        self.cr.execute('select distinct(offer_id) from training_session ')
        res = self.cr.fetchall()
        for id in res:
            self.cr.execute('select date,name from training_session where offer_id=%d' %(id[0],))
            result.append(self.cr.dictfetchall())
        return result
    def offer_name(self):
        res=[]
        self.cr.execute('select distinct(offer_id) from training_session ')
        offer_ids = ",".join([str(x) for x in map(lambda x: x[0], self.cr.fetchall()) if x])
        self.cr.execute("select name from training_offer where id in (%s)"%(offer_ids))
        res=self.cr.dictfetchall()
        return res
report_sxw.report_sxw('report.training.catalog.report',
                      'training.catalog',
                      'addons/training/report/training_catalog.rml',
                      parser=training_catalog_report,
                      header=False
                      )


class training_document_price_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_document_price_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.document.price',
                      'ir.attachment',
                      'addons/training/report/document_price.rml',
                      parser=training_document_price_report,
                      header=True)


class training_seance_booking_classroom(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_seance_booking_classroom, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

report_sxw.report_sxw('report.training.seance.booking.classroom.report',
                       'training.seance',
                      'addons/training/report/training_classroom_booking.rml',
                      parser=training_seance_booking_classroom,
                      header=True)


class training_seance_presence_list(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(training_seance_presence_list, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            '_': self._translate,
            'ordered_participants': self.ordered_participants,
            'ordered_participants_noshow': self.ordered_participants_noshow,
            'get_participants_noshow_count': self.get_participants_noshow_count,
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

    def ordered_participants_noshow(self, seance):
        participants = list(seance.participant_ids)
        participants.sort(key=lambda p: (p.contact_id.name, p.contact_id.first_name))
        for participant in participants:
            if not participant.present:
                yield participant

    def get_participants_noshow_count(self, seance):
        return reduce(lambda acc, a: acc + (not a.present and 1 or 0),
                      seance.participant_ids,
                      0)

report_sxw.report_sxw('report.training.seance.presence.report',
                       'training.seance',
                      'addons/training/report/training_presencelist.rml',
                      parser=training_seance_presence_list,
                      header=True)

report_sxw.report_sxw('report.training.seance.presence.noshow',
                       'training.seance',
                      'addons/training/report/training_presence_noshow.rml',
                      parser=training_seance_presence_list,
                      header=True)

class in_construction(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(in_construction, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
        })

reports = [
    ('report.training.seance.booking.support', 'training.seance'),
    ('report.training.course.financial.report', 'training.course')
]

for name, model in reports:
    report_sxw.report_sxw(name, model,
                          'addons/training/report/in_construction.rml',
                          parser=in_construction,
                          header=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

