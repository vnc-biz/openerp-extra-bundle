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
import base64

class kettle_transformation(osv.osv):
    _name = 'kettle.transformation'
    _description = 'kettle transformation'    
    
    _columns = {
        'name': fields.char('Transformation Name', size=64, required=True),
        'kettle_dir': fields.char('Kettle Directory', size=255, required=True),
        'file_name': fields.char('Transformation File Name', size=64, required=True),
        'scheduler': fields.many2one('ir.cron', 'Scheduler', readonly=True),
        'parameters': fields.text('Parameters'),
        'upload_file': fields.boolean('Upload File'),
        'file_name': fields.char('Internal File Name', size=255),
        'active_python_code' : fields.boolean('Active Python Code'),
        'python_code_before' : fields.text('Python Code Executed Before Transformation'),
        'python_code_after' : fields.text('Python Code Executed After Transformation'),
    }
    
    def execute_python_code(self, cr, uid, id, position, context):
        logger = netsvc.Logger()
        transfo = self.read(cr, uid, id, ['active_python_code', 'python_code_' + position], context)
        if transfo['active_python_code'] and transfo['python_code_' + position]:
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "execute python code " + position +" kettle transformation")
            exec(transfo['python_code_' + position])
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "python code executed")
        return context
    
    def error_wizard(self, cr, uid, kettle_dir, context):
        error_file = open(kettle_dir+'/nohup.out', 'r')
        error_log = error_file.readlines()
        end_error_log = ''
        for i in range(0,20):
            end_error_log = error_log.pop() + end_error_log
        raise osv.except_osv('Error !', 'You have an error in your kettle transformation, please look at the kettle log in ' + str(kettle_dir) + '/nohup.out' + "\n \n" + str(end_error_log))
          
    def execute_transformation(self, cr, uid, id, filter, context):
        transfo = self.read(cr, uid, id, ['kettle_dir','file_name'], context)
        logger = netsvc.Logger()
        file = transfo['kettle_dir']+'/transformations/'+transfo['file_name']
        if not os.path.isfile(file + '.ktr'):
            raise osv.except_osv('Error !', 'The transformation file or the kettle directory is invalid')
        csv_file = open(file +'.ktr', 'r')
        csv_temp = open(file +'_temp.ktr', 'w')

        for line in csv_file.readlines():
            for key in filter:
                line = line.replace(key, filter[key])
            csv_temp.write(line)
        csv_temp.close()
        
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "start kettle transformation : kettle log in " + str(transfo['kettle_dir']) + '/nohup.out')
        cmd = "cd " + transfo['kettle_dir'] + "; rm nohup.out ; nohup sh pan.sh -file=transformations/" + transfo['file_name'] + '_temp.ktr'
        
        if os.system(cmd) != 0:
            self.error_wizard(cr, uid, transfo['kettle_dir'], context)
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "kettle transformation finish with success")
   
kettle_transformation()

class kettle_wizard(osv.osv_memory):
    _name = 'kettle.wizard'
    _description = 'kettle wizard'     

    _columns = {
        'upload_file': fields.boolean("Upload File?"),
        'file': fields.binary('File'),
        'filename': fields.char('Filename', size=64),
    }

    def _get_add_file(self, cr, uid, context):
        return self.pool.get('kettle.transformation').read(cr, uid, context['active_id'], ['upload_file'])['upload_file']

    _defaults = {
        'upload_file': _get_add_file,
    }

    def start_kettle_tranformation(self, cr, uid, ids, context=None):
        logger = netsvc.Logger()
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        obj_transfo = self.pool.get('kettle.transformation')
        for id in ids:
            filter = {'AUTO_REP_db_erp': str(cr.dbname), 'AUTO_REP_user_erp': str(user.login), 'AUTO_REP_db_pass_erp': str(user.password)}
            transfo = obj_transfo.read(cr, uid, id, ['upload_file', 'parameters'], context)
            if transfo['upload_file']: 
                if not (context and context.get('input_filename',False)):
                    logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "the transformation " + transfo.name + " can't be executed because the anyone File was uploaded")
                    continue
                else:
                    filter.update({'AUTO_REP_file_in' : str(context['input_filename'])})
            
            context = obj_transfo.execute_python_code(cr, uid, id, 'before', context)
            
            filter.update(eval('{' + str(transfo['parameters'] or '')+ '}'))
            obj_transfo.execute_transformation(cr, uid, id, filter, context)

            context = obj_transfo.execute_python_code(cr, uid, id, 'after', context)
                
        return True


    def _save_file(self, cr, uid, id, vals, context):
        kettle_dir = self.pool.get('kettle.transformation').read(cr, uid, context['active_id'], ['kettle_dir'], context)['kettle_dir']
        filename = kettle_dir + '/files/' + str(vals['filename'])
        fp = file(filename,'wb+')
        fp.write(base64.decodestring(vals['file']))
        fp.close()
        return filename

    def action_start_tranformation(self, cr, uid, id, context):
        wizard = self.read(cr, uid, id,context=context)[0]
        if wizard['upload_file']:
            if not wizard['file']:
                raise osv.except_osv('Error !', 'You have to select a file before starting the transformation')
            else:
                context['input_filename'] = self._save_file(cr, uid, id, wizard, context)
        self.start_kettle_tranformation(cr, uid, [context['active_id']], context)
        return {'type': 'ir.actions.act_window_close'}

kettle_wizard()
