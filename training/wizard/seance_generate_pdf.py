# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (C) 2010-2011 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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

from zipfile import PyZipFile, ZIP_DEFLATED
from cStringIO import StringIO

import os
import time
import netsvc
import re
import base64
import time
import tools

def get_zip_from_directory(directory, b64enc=True):
    RE_exclude = re.compile('(?:^\..+\.swp$)|(?:\.py[oc]$)|(?:\.bak$)|(?:\.~.~$)', re.I)

    def _zippy(archive, path):
        path = os.path.abspath(path)
        base = os.path.basename(path)
        for f in tools.osutil.listdir(path, True):
            bf = os.path.basename(f)
            if not RE_exclude.search(bf):
                archive.write(os.path.join(path, f), os.path.join(base, f))

    archname = StringIO()
    archive = PyZipFile(archname, "w", ZIP_DEFLATED)
    archive.writepy(directory)
    _zippy(archive, directory)
    archive.close()
    val = archname.getvalue()
    archname.close()

    if b64enc:
        val = base64.encodestring(val)

    return val


class training_seance_generate_pdf_wizard(osv.osv_memory):
    _name = 'training.seance.generate.zip.wizard'

    _columns = {
        'presence_list_report' : fields.boolean('Presence List Report',
                                                help="If you select this option you will print the report for the presence list. " \
                                                "The file format is Presence_List_DATEOFSEANCE_SEANCEID.pdf."),
        'remuneration_form_report' : fields.boolean('Remuneration Form',
                                                    help="If you select this option, you will print the report for the remuneration " \
                                                    "forms of all contacts. The file format is Request_REQUESTNAME_Invoice_INVOICEID.pdf."),
        'zip_file' : fields.binary('Zip File', readonly=True),
        'zip_file_name' : fields.char('File name', readonly=True, size=64),
        'state' : fields.selection( [ ('selection', 'Selection'), ('result', 'Result') ], 'State', readonly=True, required=True),
    }

    _defaults = {
        'presence_list_report' : lambda *a: 0,
        'remuneration_form_report' : lambda *a: 0,
        'state' : lambda *a: 'selection',
    }

    def action_close(self, cr, uid, ids, context=None):
        return { 'type' : 'ir.actions.act_window.close' }

    def action_generate_zip(self, cr, uid, ids, context=None):
        try:
            import tempfile
            parent_directory = tempfile.mkdtemp(prefix='openerp_', suffix='_reports')
            directory = os.path.join(parent_directory, 'Reports')
            os.mkdir(directory)
            self.add_selections(cr, uid, ids, directory, context=context)
            result = get_zip_from_directory(directory, True)
            fp = file(os.path.join(parent_directory, 'output.zip'), 'w')
            fp.write(result)
            fp.close()

            active_id = context and context.get('active_id')
            seance = self.pool.get('training.seance').browse(cr, uid, active_id, context=context)
            ts = time.strptime(seance.date, '%Y-%m-%d %H:%M:%S')
            date = time.strftime('%Y%m%d', ts)

            values = {
                'state' : 'result',
                'zip_file' : result,
                'zip_file_name' : 'Seance_Reports_%s_%06d.zip' % (date, seance.id),
            }
        finally:
            import shutil
            shutil.rmtree(parent_directory)
        return self.write(cr, uid, ids, values, context=context)

    def _get_report(self, cr, uid, oid, reportname, context=None):
        srv = netsvc.LocalService(reportname)
        pdf, _ = srv.create(cr, uid, [oid], {}, context=context)
        return pdf

    def add_selections(self, cr, uid, ids, directory, context=None):
        active_id = context and context.get('active_id')
        seance = self.pool.get('training.seance').browse(cr, uid, active_id, context=context)
        ts = time.strptime(seance.date, '%Y-%m-%d %H:%M:%S')
        date = time.strftime('%Y%m%d', ts)
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.presence_list_report:
                res = self._get_report(cr, uid, active_id, 'report.training.seance.presence.report', context=context)
                filename = os.path.join(directory, 'Presence_List_%s_%06d.pdf' % (date, seance.id,))
                fp = file(filename, 'w')
                fp.write(res)
                fp.close()

            if obj.remuneration_form_report:
                for contact in seance.contact_ids:
                    if not contact.request_id:
                        raise osv.except_osv(_('Error'),
                                             _('The stakeholder %s %s has not a request') % (contact.job_id.fist_name, contact.job_id.name) )

                    if not contact.request_id.purchase_order_id:
                        raise osv.except_osv(_('Error'),
                                             _('There is no Purchase Order for a request'))

                    if not contact.request_id.purchase_order_id.invoice_id:
                        raise osv.except_osv(_('Error'),
                                             _('There is no Invoice for the Purchase Order for this request'))

                    res = self._get_report(cr, uid, contact.request_id.purchase_order_id.invoice_id.id, 'report.account.invoice', context=context)
                    filename = os.path.join(directory, 'Request_%s_Invoice_%06d.pdf' % (re.sub('/|-', '_', contact.request_id.reference),
                                                                                        contact.request_id.purchase_order_id.invoice_id.id))
                    fp = file(filename, 'w')
                    fp.write(res)
                    fp.close()

training_seance_generate_pdf_wizard()

