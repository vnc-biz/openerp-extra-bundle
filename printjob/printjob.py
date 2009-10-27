# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 Ferran Pegueroles <ferran@pegueroles.com>
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

import tools
import time 
import datetime 
from osv import fields,osv

import base64, os, string
from tempfile import mkstemp
import netsvc
import pooler, ir, tools
from service import security
import logging

import threading, thread
import time
import base64
import addons

#
#  Printers
#
class printjob_printer(osv.osv):
    _name = "printjob.printer"
    _description = "Printer"

    _columns = {
        'name' : fields.char('Name',size=64,required=True,select="1"),
        'system_name': fields.char('System Name',size=64,required=True,select="1"),
        'is_default':fields.boolean('Default Printer',required=True,readonly=True),
    }
    _order = "name"
    
    _defaults = {
        'is_default': lambda *a: False,
    }

    def set_default(self, cr, uid, ids, context):
        if not ids:
            return
        default_ids= self.search(cr, uid,[('is_default','=',True)])
        self.write(cr, uid, default_ids, {'is_default':False}, context)
        self.write(cr, uid, ids[0], {'is_default':True}, context)
        return {}
    
    def get_default(self,cr,uid,context):
        printer_ids = self.search(cr, uid,[('is_default','=',True)])
        if printer_ids:
            return printer_ids[0]
        return None

printjob_printer()


# 
#  Printjobs
#
import re
rxcountpages=re.compile(r"$\s*/Type\s*/Page[/\s]", re.MULTILINE|re.DOTALL)

class printjob_job(osv.osv):
    _name = "printjob.job"
    _description = "Print Job"

    def _doc_pages(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for d in self.browse(cr, uid, ids):
            if d.result:
                data = base64.decodestring(d.result)
                res[d.id] = len(rxcountpages.findall(data))
            else:
                res[d.id] = 0
        return res

    _columns = {
        'name' : fields.char('Name',size=64,required=True,select="1"),
        'format' : fields.char('Format',size=64,readonly=True),
        'state': fields.selection([('draft','In Progress'),
                                ('ready','Processed'), 
                                ('error','Error'), 
                                ('done','Done')], 'State', required=True, select="1"),
        'report' : fields.char('Report',size=256,required=True,select="1"),
        'result': fields.text('Document'),
        'ids': fields.text('Ids'),
        'data': fields.text('Param. Data'),
        'context': fields.text('Context Data'),
        'batch':fields.boolean('Processed in Batch'),
        'keep':fields.boolean('Keep the document',help="A job marked with keep will not be deleted by the cron job"),
        'pages': fields.function(_doc_pages, method=True, string='Number of Pages', type='integer'),


        'create_date': fields.datetime('Created' ,readonly=True),
        'create_uid': fields.many2one('res.users', 'Created By',readonly=True),
    }
    _order = "id desc"
    
    _defaults = {
        'state': lambda *a: 'draft',
        'keep': lambda *a: False,
    }

    def _clean_old(self, cr, uid, ids=False, context={}):
        """
          Function called by the cron to delete old entries
        """
        limit = datetime.datetime.now() - datetime.timedelta(days=2)
        cr.execute('select id from printjob_job \
                where create_date<%s and not keep',
            (limit.strftime('%Y-%m-%d %H:%M:%S'),))
        ids2 = map(lambda x: x[0], cr.fetchall() or [])
        if ids2:
            logger = netsvc.Logger()
            logger.notifyChannel("report", netsvc.LOG_INFO,
                 "Deleted old completed reports '%s'." % str(ids2))
            self.unlink(cr, uid, ids2, context)
        return True

printjob_job()


class except_print(Exception):
    def __init__(self, name, value, exc_type='warning'):
        self.name = name
        self.exc_type = exc_type
        self.value = value
        self.args = (exc_type, name)
        self.message = "\n".join([" -- ".join( (exc_type , name ) ) , '' , value])

#
#

class report_spool(netsvc.Service):
    def __init__(self, name='report'):
        netsvc.Service.__init__(self, name)
        self.joinGroup('web-services')
        self.exportMethod(self.report)
        self.exportMethod(self.report_get)
        self._reports = {}
        self.id = 0
        self.id_protect = threading.Semaphore()

    def report(self, db, uid, passwd, object, ids, datas=None, context=None):

        logger = netsvc.Logger()
        if not datas:
            datas={}
        if not context:
            context={}

        security.check(db, uid, passwd)
        logger.notifyChannel("report", netsvc.LOG_INFO,"request report '%s'" % str(object))
        # Reprint a printed job
        if object == 'printjob.reprint':
            return ids[0]
        
        # detect if this is a batch printing 
        batch = False
        if 'print_batch' in context:
            batch = context['print_batch']
        if 'print_batch' in datas:
            batch = datas['print_batch']
        if 'form' in datas:
            if 'print_batch' in datas['form']:
                batch = datas['form']['print_batch']

        #
        # Buscar la impressora per defecte
        #
        cr = pooler.get_db(db).cursor()
        pool = pooler.get_pool(cr.dbname)
        
        printer = False
        if batch:
            if 'printer' in context:
                printer = context['printer']
            if 'printer' in datas:
                printer = datas['printer']
            if 'form' in datas:
                if 'printer' in datas['form']:
                    printer = datas['form']['printer']
            printers_obj = pool.get('printjob.printers')
            system_printer=False
            if printer:
                printer_ids = printers_obj.read(cr, uid, [printer],['system_name'])
                if printer_ids:
                    system_printer= printer_ids[0]['system_name']
            else:
                printer_id = printers_obj.get_default(cr,uid,context)
                if printer_id:
                    system_printer = printers_obj.browse(cr,uid,printer_id).system_name

        report_obj = pool.get('ir.actions.report.xml')
        report = report_obj.search(cr,uid,[('report_name','=',object)])
        if report:
            name=report_obj.browse(cr,uid,report[0]).name
        else:
            name=object

        # 
        # Create new printjob.job
        #
        job = {
            'name':name,
            'report':object,
            'ids':str(ids),
            'data':str(datas),
            'context':str(context),
            'result':False,
            'batch':batch,
        }
        job_id = pool.get("printjob.job").create(cr,uid,job)
        cr.commit()
        cr.close()
        
        def go(id, uid, ids, datas, context, system_printer):
            logger.notifyChannel("report", netsvc.LOG_DEBUG,
                 "Printing thread started")
            cr = pooler.get_db(db).cursor()
            obj = netsvc.LocalService('report.'+object)
            (result, format) = obj.create(cr, uid, ids, datas, context)
            pool = pooler.get_pool(cr.dbname)
            job = {
                'result':base64.encodestring(result),
                'format':format,
                'state':'ready',
            }
            if system_printer:
                self.print_direct(result,system_printer,format)
            pool.get("printjob.job").write(cr,uid,id,job)
            cr.commit()
            cr.close()
            return True
        thread.start_new_thread(go, (job_id, uid, ids, datas, context, batch and system_printer))
        return job_id

    def print_direct(self,result,system_printer,format):
        logger = netsvc.Logger()
        tmpfile=mkstemp()
        os.write(tmpfile[0],result)
        if format == 'raw':
            # -l is the same as -o raw
            cmd = "lpr -l -P %s %s" % (system_printer,tmpfile[1])
        else:
            cmd = "lpr -P %s %s" % (system_printer,tmpfile[1])
        logger.notifyChannel("report", netsvc.LOG_INFO,"Printing job : '%s'" % cmd)
        os.system(cmd)

    def report_get(self, db, uid, passwd, report_id):
        security.check(db, uid, passwd)

        cr = pooler.get_db(db).cursor()
        pool = pooler.get_pool(cr.dbname)
        report = pool.get('printjob.job').read(cr,uid,report_id)

        if report and report_id == report['id']:
            if report['create_uid'][0] != uid:
                cr.close()
                raise Exception, 'AccessDenied'
        else:
            cr.close()
            raise Exception, 'ReportNotFound'
      
        res = {'state': report['state'] in ('ready','done')}
        if res['state']:
            res['result'] = report['result']
            res['format'] = report['format']
            if report['state'] == 'ready':
                job = {'state':'done'}
                pool.get('printjob.job').write(cr,uid,report_id,job)
                cr.commit()
        cr.close()
        #if report['batch'] and not res['state']:
        if True:
            raise except_print(_('Report generated in background'),
                               _("""This report is generated in background.
In some minutes look at your print jobs.
"""))
        return res

report_spool()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
