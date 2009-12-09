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
from launchpadlib.launchpad import Launchpad, EDGE_SERVICE_ROOT
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
        cachedir = os.path.expanduser('~/.launchpadlib/cache')
        if not os.path.exists(cachedir):
                os.makedirs(cachedir,0700)
        credfile = os.path.expanduser('~/.launchpadlib/credentials')
        try:
                credentials = Credentials()
                credentials.load(open(credfile))
                launchpad = Launchpad(credentials, EDGE_SERVICE_ROOT, cachedir)
        except:
                launchpad = Launchpad.get_token_and_login(sys.argv[0], EDGE_SERVICE_ROOT, cachedir)
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

    def getProject(self, project):
        project = launchpad.projects[project]
        return project
    
    def getSeries(self, project):
        lp_project =  launchpad.projects[project]
        if 'series' in lp_project.lp_collections:
                return lp_project.series.entries
        else:
            return None
        
    def getMilestones(self, project, ml):
        lp_project =  launchpad.projects[project]
        if 'all_milestones' in lp_project.lp_collections:
                temp = lp_project.all_milestones.entries 
                res = [item for item in temp if item['series_target_link'] == ml]
                return res 
        else:
            return None

class project_project(osv.osv):
    _inherit = "project.project"
    _columns = {
                'bugs_target': fields.char('Bugs Target', size=300),
                } 
    def onchange_project_name(self, cr, uid, ids, project_name):
         val={}
         val['bugs_target'] = "https://api.staging.launchpad.net/beta/" + project_name
         return {'value' : val}   
project_project()        

class lp_project(osv.osv):
    _name="lp.project"
    _description= "LP Projects"
    _columns={
        'name': fields.char("Project Name", size=200, required=True, help="The name of the project"),
        'title': fields.char("Project Title", size=200, required=True, help="The project title. Should be just a few words."),
        'summary': fields.char("Project Summary", size=100, help="The summary should be a single short paragraph."),
        'series_ids' : fields.one2many('lp.series', 'name', 'LP Series'),
        'milestone_ids' : fields.one2many('lp.project.milestone', 'name', 'LP Series'),
            }
lp_project()

class lp_series(osv.osv):
    _name="lp.series"
    _description="LP Series"
    _columns={
              'name':fields.char("Series Name",size=200, required=True, help="The name of the series"),
              'status': fields.char("Status", size=100),
              'summary': fields.char("Summary", size=1000, help="The summary should be a single short paragraph."),
              'project_id': fields.many2one('lp.project', 'LP Project')  
              }
lp_series()   

class lp_project_milestone(osv.osv):
    _name="lp.project.milestone"
    _description= "LP milestone"
    _columns={
        'name':fields.char('Version', size=100,required=True),
        'series_id':fields.many2one('lp.series', 'Series', readonly=True),
        'project_id': fields.many2one('lp.project', 'Project', readonly=True),
        'expect_date': fields.datetime('Expected Date', readonly=True),
        }

lp_project_milestone()

class crm_case(osv.osv):
    _inherit = "crm.case"

    _columns = {
                'project_id': fields.many2one('project.project', 'Project'),
                'lp_project':fields.many2one('lp.project','LP Project'),
                'bug_id': fields.integer('Bug ID',readonly=True),
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
            lp_server = lpServer()
            crm_case_obj = self.pool.get('crm.case')
            crm_ids=crm_case_obj.search(cr,uid,[('bug_id','=',False),('section_id','=',sec_id[0]),('project_id','!=',False)])
            launchpad = lp_server.launchpad
            for case in crm_case_obj.browse(cr,uid, crm_ids):
                title = case.name
                target = case.project_id.bugs_target
                description=case.description
                b=launchpad.bugs.createBug(title=title, target=target, description=description)
                self.write(cr,uid,case.id,{'bug_id' : b.id},context=None)
            categ_fix_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]),('name','=','Fixed')])
            categ_inv_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]),('name','=','Invalid')])
            categ_future_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]), ('name','=','Future')])
            categ_wfix_id=case_stage.search(cr, uid, [('section_id','=',sec_id[0]),('name','=',"Won'tFix")])

            prj = self.pool.get('project.project')
            project_id=prj.search(cr,uid,[])
            
            for prj_id in prj.browse(cr,uid, project_id):
                project_name=str(prj_id.name)
                if project_name.find('openobject') == 0:
                    prjs=lp_server.get_lp_bugs(project_name)
                    for key, bugs in prjs.items():
                        for bug in bugs:
                            b_id = self.search(cr,uid,[('bug_id','=',bug.bug.id)])
                            val['project_id']=prj_id.id
                            project = str(bug.target).split('/')[-1]
                            lp_prj = pool.get('lp.project')
                            lp_project_ids=lp_prj.search(cr,uid,[('name','=',project)])
                            lp_project = lp_server.getProject(project)
                            res={}
                            res['name'] = lp_project.name
                            res['title'] = lp_project.title
                            res['summary'] = lp_project.summary
                            if not lp_project_ids:
                                lp_project_id=lp_prj.create(cr, uid, res,context=context) 
                                all_series = lp_server.getSeries(lp_project)
                                if all_series:
                                    series_ids=[]
                                    prj_milestone_ids=[]
                                    lp_series = pool.get('lp.series')
                                    for series in all_series:
                                         s={}
                                         s['name'] = series['name']
                                         s['status'] = series['status']
                                         s['summary'] = series['summary']
                                         s['project_id'] = lp_project_id
                                         lp_series_id=lp_series.create(cr, uid, s,context=context)
                                         cr.commit()
                                         series_ids.append(lp_series_id)
                                         
                                         ml = series['all_milestones_collection_link'].rsplit('/',1)[0]
                                         all_milestones = lp_server.getMilestones(lp_project, ml)
                                         if all_milestones:
                                            milestone_ids=[]
                                            lp_milestones = pool.get('lp.project.milestone')
                                            for ms in all_milestones:
                                                 s={}
                                                 s['name'] = ms['name']
                                                 s['series_id'] = lp_series_id
                                                 s['project_id'] = lp_project_id
                                                 if ms['date_targeted']:
                                                     s['expect_date'] = ms['date_targeted']
                                                 lp_milestones_id=lp_milestones.create(cr, uid, s,context=context)
                                                 cr.commit()
                                                 milestone_ids.append(lp_milestones_id)
                                                 prj_milestone_ids.append(lp_milestones_id)
                            else:
                                lp_project_id = lp_project_ids[0]
                                lp_prj.write(cr, uid, lp_project_id, res, context=context)
                                
                                
                            cr.commit()
                            val['lp_project']=lp_project_id
                            val['bug_id']=bug.bug.id
                            val['name']=bug.bug.title
                            val['section_id']=sec_id[0]
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
