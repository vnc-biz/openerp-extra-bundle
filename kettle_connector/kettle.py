# -*- encoding: utf-8 -*-
#########################################################################
#                                                                       #
# Copyright (C) 2010   Sébastien Beau                                   #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################

from osv import fields,osv
import os
import netsvc
import time
import datetime

class kettle_configuration(osv.osv):
    _name = 'kettle.configuration'
    _description = 'kettle configuration'    
    
    _columns = {
        'name': fields.char('Transformation Name', size=64, required=True),
        'kettle_dir': fields.char('Kettle Directory', size=255, required=True),
        'file_name': fields.char('Transformation File Name', size=64, required=True),
        'scheduler': fields.many2one('ir.cron', 'Scheduler', readonly=True),
        'parameters': fields.text('Parameters'),
        'active_python_code' : fields.boolean('Active Python Code'),
        'python_code_before' : fields.text('Python Code Executed Before Transformation'),
        'python_code_after' : fields.text('Python Code Executed After Transformation'),
    }
    
kettle_configuration()

class kettle_wizard(osv.osv_memory):
    _name = 'kettle.wizard'
    _description = 'kettle wizard'
    
    def error_wizard(self, cr, uid, kettle_dir, context):
        error_file = open(kettle_dir+'/nohup.out', 'r')
        error_log = error_file.readlines()
        end_error_log = ''
        for i in range(0,20):
            end_error_log = error_log.pop() + end_error_log
        raise osv.except_osv('Error !', 'You have an error in your kettle transformation, please look at the kettle log in ' + str(kettle_dir) + '/nohup.out' + "\n \n" + str(end_error_log))
        
        
    def start_kettle_tranformation(self, cr, uid, ids, context):
        
        logger = netsvc.Logger()
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        for id in ids:
            transfo = self.pool.get('kettle.configuration').browse(cr, uid, id, context)
            
            if transfo.active_python_code and transfo.python_code_before:
                logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "execute python code before kettle transformation")
                exec(transfo.python_code_before)
                logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "python code executed")
            
            file = transfo.kettle_dir+'/transfo/'+transfo.file_name+'.ktr'
            if not os.path.isfile(file):
                raise osv.except_osv('Error !', 'The tranformastion file or the kettle directory is invalid')
            csv_file = open(transfo.kettle_dir+'/transfo/'+transfo.file_name+'.ktr', 'r')
            csv_temp = open(transfo.kettle_dir+'/transfo/'+transfo.file_name+'_temp.ktr', 'w')
            
            filter = eval('{' + str(transfo.parameters or '')+ '}')
            filter.update({'db_erp': str(cr.dbname), 'user_erp': str(user.login), 'db_pass_erp': str(user.password)})
            for line in csv_file.readlines():
                for key in filter:
                    line = line.replace(key, filter[key])
                csv_temp.write(line)
            csv_temp.close()
            
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "start kettle transformation : kettle log in " + str(transfo.kettle_dir) + '/nohup.out')
            cmd = "cd " + transfo.kettle_dir + "; nohup sh pan.sh -rep=my_repo -trans=" + transfo.file_name + '_temp'
            
            if os.system(cmd) != 0:
                self.error_wizard(cr, uid, transfo.kettle_dir, context)
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "kettle transformation finish with success")
            
            if transfo.active_python_code and transfo.python_code_after:
                logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "execute python code after kettle transformation")
                exec(transfo.python_code_after)
                logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "python code executed")
        return True

    def action_start_tranformation(self, cr, uid, id, context=None):
        self.start_kettle_tranformation(cr, uid, context['active_ids'], context)
        return {'type': 'ir.actions.act_window_close'}

kettle_wizard()
