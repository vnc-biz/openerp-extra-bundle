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

import time
import tools
from osv import fields,osv,orm
import pooler

import mx.DateTime
import base64
from tools.translate import _
from launchpadlib.launchpad import Launchpad, STAGING_SERVICE_ROOT
from launchpadlib.credentials import Credentials
from SimpleXMLRPCServer import SimpleXMLRPCServer
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
import os
import threading
import pickle
import time



class lpServer(threading.Thread):

    cachedir = ".launchpad/cache/"
    lp_credential_file = ".launchpad/lp_credential2.txt"
    bugs_pck = 'bugs.pck'
    launchpad = False

    def __init__(self):
        super(lpServer, self).__init__()
        self.launchpad = self.get_lp()

    def get_lp(self):
        launchpad = False
        if not os.path.isdir(self.cachedir):
            try:
                os.makedirs(self.cachedir)
            except:
                raise
        if not os.path.isfile(self.lp_credential_file):
            try:
                launchpad = Launchpad.get_token_and_login('openerp', STAGING_SERVICE_ROOT, self.cachedir)
                launchpad.credentials.save(file(self.lp_credential_file, "w"))
            except:
                print 'Service Unavailable !'
        else:
            credentials = Credentials()
            credentials.load(open(self.lp_credential_file))
            launchpad = Launchpad(credentials, STAGING_SERVICE_ROOT, self.cachedir)
        return launchpad


    def get_lp_bugs(self, projects):

        launchpad = self.launchpad
        res = {}
        if not launchpad:
            return res
        if not isinstance(projects,list):
            projects = [projects]

        bug_status = ['New','Confirmed','In Progress']
        for project in projects:
            result = {}
            r = {}
            lp_project = launchpad.projects[str(project)]
            result['non-series'] = lp_project.searchTasks(status=bug_status)
            if 'series' in lp_project.lp_collections:
                for series in lp_project.series:
                    result[series.name] = series.searchTasks()
                bug_list=[]
                for name, bugs in result.items():
                    for bug in bugs:
                        bug_list.append(bug)
                res[project]=bug_list
        return  res


class crm_case(osv.osv):
    _inherit = "crm.case"

    _columns = {
                'project_id': fields.many2one('project.project', 'Project'),
                'lp_project':fields.char('LP Project',size=64,readonly=True),
                'bug_id': fields.integer('Bug ID',readonly=True)
                }

    def _check_bug(self, cr, uid, ids=False, context={}):
        '''
        Function called by the scheduler to process cases for date actions
        Only works on not done and cancelled cases
        '''
        val={}
        pool=pooler.get_pool(cr.dbname)


        sec_obj = pool.get('crm.case.section')
        sec_id = sec_obj.search(cr, uid, [('code', '=', 'BugSup')])

        case_stage= pool.get('crm.case.stage')

        if sec_id:

            categ_fix_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]),('name','=','Fixed')])
            categ_inv_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]),('name','=','Invalid')])
            categ_future_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]), ('name','=','Future')])
            categ_wfix_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]),('name','=',"Won'tFix")])

            prj = self.pool.get('project.project')
            project_id=prj.search(cr,uid,[])

            for prj_id in prj.browse(cr,uid, project_id):
                project_name=str(prj_id.name)
                if project_name.find('openobject') ==0:
                    lp_server = lpServer()
                    res=lp_server.get_lp_bugs(project_name)
                    for key, bugs in res.items():
                        for bug in bugs:
                            b_id = self.search(cr,uid,[('bug_id','=',bug.bug.id)])
                            val['project_id']=prj_id.id
                            val['lp_project']=key
                            val['bug_id']=bug.bug.id
                            val['name']=bug.bug.title
                            val['section_id']=sec_id[
                                                     0]
                            if bug.importance == 'Wishlist':
                                val['stage_id']=categ_future_id[0]
                                val['priority']='5'
                            elif bug.importance=='High':
                                val['priority']='1'
                            elif bug.importance=='Medium':
                                val['priority']='3'
                            if bug.status in ('Confirmed','Fix Released'):
                                val['stage_id']=categ_fix_id[0]
                            if bug.status =='invaild':
                                val['stage_id']= val['stage_id']=categ_inv_id[0]

                            if not b_id:
                                self.create(cr, uid, val,context=context)
                            if b_id:
                                self.write(cr,uid,b_id,val,context=context)
                            cr.commit()

            return True

crm_case()


