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

class kettle_server(osv.osv):
    _name = 'kettle.server'
    _description = 'kettle server'  
    
    _columns = {
        'name': fields.char('Server Name', size=64, required=True),
        'kettle_dir': fields.char('Kettle Directory', size=255, required=True),
        'transformation': fields.one2many('kettle.transformation', 'server_id', 'Transformation'),
        }
    
kettle_server()

class kettle_transformation(osv.osv):
    _name = 'kettle.transformation'
    _description = 'kettle transformation'
    
    _columns = {
        'name': fields.char('Transformation Name', size=64, required=True),
        'server_id': fields.many2one('kettle.server', 'Server', required=True),
        'file': fields.binary('File'),
        'filename': fields.char('File Name', size=64),
        }
    
    def error_wizard(self, cr, uid, id, context):
        error_description = self.pool.get('ir.attachment').read(cr, uid, id, ['description'], context)['description']
        if error_description and "USER_ERROR" in error_description:
            raise osv.except_osv('USER_ERROR', error_description)
        else:
            raise osv.except_osv('KETTLE ERROR', 'An error occurred, please look in the kettle log')
    
    def execute_transformation(self, cr, uid, id, filter, log_file_name, attachment_id, context):
        transfo = self.browse(cr, uid, id, context)
        kettle_dir = transfo.server_id.kettle_dir
        filename = transfo.filename
        logger = netsvc.Logger()
        transformation_temp = open(kettle_dir + '/transformations/'+ filename, 'w')
        
        file_temp = base64.decodestring(transfo.file)
        for key in filter:
            file_temp = file_temp.replace(key, filter[key])
        transformation_temp.write(file_temp)
        transformation_temp.close()
        
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "start kettle task : kettle log in " + str(kettle_dir) + '/nohup.out')
        cmd = "cd " + kettle_dir + "; nohup sh pan.sh -file=transformations/" + filename + '> "'+ log_file_name + '.log"'
        os_result = os.system(cmd)
        
        if os_result != 0:
            prefixe_log_name = "[ERROR]"
        else:
            note = self.pool.get('ir.attachment').read(cr, uid, attachment_id, ['description'], context)['description']
            if note and 'WARNING' in note:
                prefixe_log_name = "[WARNING]"
            else:
                prefixe_log_name = "[SUCCESS]"
        
        self.pool.get('ir.attachment').write(cr, uid, attachment_id, {'datas': base64.encodestring(open(kettle_dir +"/" + log_file_name + '.log', 'rb').read()), 'datas_fname': log_file_name + '.log', 'name' : prefixe_log_name + ' ' + log_file_name}, context)
        cr.commit()
        os.system('rm "' + kettle_dir +"/" + log_file_name + '.log"')
        if os_result != 0:
            self.error_wizard(cr, uid, attachment_id, context)
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "kettle task finish with success")
     
kettle_transformation()

class kettle_task(osv.osv):
    _name = 'kettle.task'
    _description = 'kettle task'    
    
    _columns = {
        'name': fields.char('Task Name', size=64, required=True),
        'server_id': fields.many2one('kettle.server', 'Server', required=True),
        'transformation_id': fields.many2one('kettle.transformation', 'Transformation', required=True),
        'scheduler': fields.many2one('ir.cron', 'Scheduler', readonly=True),
        'parameters': fields.text('Parameters'),
        'upload_file': fields.boolean('Upload File'),
        'active_python_code' : fields.boolean('Active Python Code'),
        'python_code_before' : fields.text('Python Code Executed Before Transformation'),
        'python_code_after' : fields.text('Python Code Executed After Transformation'),
    }
    
    def attach_file_to_task(self, cr, uid, id, datas_fname, attach_name, delete = False, context = None):
        if not context:
            context = {}
        context.update({'default_res_id' : id, 'default_res_model': 'kettle.task'})
        datas = base64.encodestring(open(datas_fname,'rb').read())
        attachment_id = self.pool.get('ir.attachment').create(cr, uid, {'name': attach_name, 'datas': datas, 'datas_fname': datas_fname.split("/").pop()}, context)
        return attachment_id
    
    def execute_python_code(self, cr, uid, id, position, context):
        logger = netsvc.Logger()
        task = self.read(cr, uid, id, ['active_python_code', 'python_code_' + position], context)
        if task['active_python_code'] and task['python_code_' + position]:
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "execute python code " + position +" kettle task")
            exec(task['python_code_' + position])
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "python code executed")
        return context
        
kettle_task()

class kettle_wizard(osv.osv_memory):
    _name = 'kettle.wizard'
    _description = 'kettle wizard'     

    _columns = {
        'upload_file': fields.boolean("Upload File?"),
        'file': fields.binary('File'),
        'filename': fields.char('Filename', size=64),
    }

    def _get_add_file(self, cr, uid, context):
        return self.pool.get('kettle.task').read(cr, uid, context['active_id'], ['upload_file'])['upload_file']

    _defaults = {
        'upload_file': _get_add_file,
    }

    def start_kettle_task(self, cr, uid, ids, context=None):
        logger = netsvc.Logger()
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        obj_task = self.pool.get('kettle.task')
        for id in ids:
            context.update({'default_res_id' : id, 'default_res_model': 'kettle.task', 'start_date' : time.strftime('%d-%m-%Y %H:%M:%S')})
            log_file_name = 'TASK LOG ' + context['start_date']
            attachment_id = self.pool.get('ir.attachment').create(cr, uid, {'name': log_file_name}, context)
            cr.commit()
            
            filter = {
                      'AUTO_REP_db_erp': str(cr.dbname),
                      'AUTO_REP_user_erp': str(user.login),
                      'AUTO_REP_db_pass_erp': str(user.password),
                      'AUTO_REP_kettle_task_id' : str(id),
                      'AUTO_REP_kettle_task_attachment_id' : str(attachment_id),
                      }
            
            task = obj_task.read(cr, uid, id, ['upload_file', 'parameters', 'transformation_id'], context)
            if task['upload_file']: 
                if not (context and context.get('input_filename',False)):
                    logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "the task " + task['name'] + " can't be executed because the anyone File was uploaded")
                    continue
                else:
                    filter.update({'AUTO_REP_file_in' : str(context['input_filename'])})
            
            context = obj_task.execute_python_code(cr, uid, id, 'before', context)
            
            filter.update(eval('{' + str(task['parameters'] or '')+ '}'))
            self.pool.get('kettle.transformation').execute_transformation(cr, uid, id, filter, log_file_name, attachment_id, context)

            context = obj_task.execute_python_code(cr, uid, id, 'after', context)
            
            if context.get('input_filename',False):
                obj_task.attach_file_to_task(cr, uid, task['transformation_id'][0], context['input_filename'], '[FILE IN] FILE IMPORTED ' + context['start_date'], True, context)
        
        return True

    def _save_file(self, cr, uid, id, vals, context):
        kettle_dir = self.pool.get('kettle.task').browse(cr, uid, context['active_id'], ['server_id'], context).server_id.kettle_dir
        filename = kettle_dir + '/files/' + str(vals['filename'])
        fp = open(filename,'wb+')
        fp.write(base64.decodestring(vals['file']))
        fp.close()
        return filename

    def action_start_task(self, cr, uid, id, context):
        wizard = self.read(cr, uid, id,context=context)[0]
        if wizard['upload_file']:
            if not wizard['file']:
                raise osv.except_osv('Error !', 'You have to select a file before starting the task')
            else:
                context['input_filename'] = self._save_file(cr, uid, id, wizard, context)
        self.start_kettle_task(cr, uid, [context['active_id']], context)
        return {'type': 'ir.actions.act_window_close'}

kettle_wizard()