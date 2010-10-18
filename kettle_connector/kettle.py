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
from terminator_install import installer
import tools

class kettle_server(osv.osv):
    _name = 'kettle.server'
    _description = 'kettle server'
    
    def button_install(self, cr, uid, ids, context=None):
        inst = installer()
        inst.install(self.read(cr, uid, ids, ['kettle_dir'])[0]['kettle_dir'].replace('data-integration', ''))
        return True
    
    _columns = {
        'name': fields.char('Server Name', size=64, required=True),
        'kettle_dir': fields.char('Kettle Directory', size=255, required=True),
        'transformation': fields.one2many('kettle.transformation', 'server_id', 'Transformation'),
        }
    
    _defaults = {
        'kettle_dir': lambda *a: tools.config['addons_path'].replace('/addons', '/data-integration'),
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
    
    def execute_transformation(self, cr, uid, id, log_file_name, attachment_id, context):
        transfo = self.browse(cr, uid, id, context)
        kettle_dir = transfo.server_id.kettle_dir
        filename = transfo.filename
        logger = netsvc.Logger()
        transformation_temp = open(kettle_dir + '/openerp_tmp/'+ filename, 'w')
        
        file_temp = base64.decodestring(transfo.file)
        if context.get('filter', False):
            for key in context['filter']:
                file_temp = file_temp.replace(key, context['filter'][key])
        transformation_temp.write(file_temp)
        transformation_temp.close()
        
        logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "start kettle task : open kettle log with tail -f " + kettle_dir +'/"' + log_file_name + '.log"')
        cmd = "cd " + kettle_dir + "; nohup sh pan.sh -file=openerp_tmp/" + filename + '> "'+ log_file_name + '.log"'
        os_result = os.system(cmd)
        
        if os_result != 0:
            prefixe_log_name = "[ERROR]"
        else:
            note = self.pool.get('ir.attachment').read(cr, uid, attachment_id, ['description'], context)['description']
            if note and 'WARNING' in note:
                prefixe_log_name = "[WARNING]"
            else:
                prefixe_log_name = "[SUCCESS]"
        
        self.pool.get('ir.attachment').write(cr, uid, [attachment_id], {'datas': base64.encodestring(open(kettle_dir +"/" + log_file_name + '.log', 'rb').read()), 'datas_fname': log_file_name + '.log', 'name' : prefixe_log_name + ' ' + log_file_name}, context)
        cr.commit()
        os.remove(kettle_dir +"/" + log_file_name + '.log')
        os.remove(kettle_dir + '/openerp_tmp/'+ filename)
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
        'output_file' : fields.boolean('Output File'),
        'active_python_code' : fields.boolean('Active Python Code'),
        'python_code_before' : fields.text('Python Code Executed Before Transformation'),
        'python_code_after' : fields.text('Python Code Executed After Transformation'),
        'last_date' : fields.datetime('Last Execution'),
    }
        
    def attach_file_to_task(self, cr, uid, id, datas_fname, attach_name, delete = False, context = None):
        if not context:
            context = {}
        context.update({'default_res_id' : id, 'default_res_model': 'kettle.task'})
        datas = base64.encodestring(open(context['kettle_dir'] + '/' + datas_fname,'rb').read())
        os.remove(context['kettle_dir'] + '/' + datas_fname)
        attachment_id = self.pool.get('ir.attachment').create(cr, uid, {'name': attach_name, 'datas': datas, 'datas_fname': datas_fname.split("/").pop()}, context)
        return attachment_id
    
    def attach_output_file_to_task(self, cr, uid, id, datas_fname, attach_name, delete = False, context = None):
        filename_completed = False
        filename = datas_fname.split('/').pop()
        dir = context['kettle_dir']+'/openerp_tmp'
        files = os.listdir(dir)
        for file in files:
            if filename in file:
                filename_completed = file
        if filename_completed:
            self.attach_file_to_task(cr, uid, id, 'openerp_tmp/'+  filename_completed, attach_name, delete, context)
        else:
            raise osv.except_osv('USER ERROR', 'the output file was not found, are you sure that you transformation will give you an output file?')
        
    def execute_python_code(self, cr, uid, id, position, context):
        logger = netsvc.Logger()
        task = self.read(cr, uid, id, ['active_python_code', 'python_code_' + position], context)
        if task['active_python_code'] and task['python_code_' + position]:
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "execute python code " + position +" kettle task")
            exec(task['python_code_' + position])
            logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "python code executed")
        return context
    
    def start_kettle_task(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        logger = netsvc.Logger()
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        for id in ids:
            context.update({'default_res_id' : id, 'default_res_model': 'kettle.task', 'start_date' : time.strftime('%Y-%m-%d %H:%M:%S')})
            log_file_name = 'TASK LOG ' + context['start_date']
            attachment_id = self.pool.get('ir.attachment').create(cr, uid, {'name': log_file_name}, context)
            cr.commit()
            
            context['filter'] = {
                      'AUTO_REP_db_erp': str(cr.dbname),
                      'AUTO_REP_user_erp': str(user.login),
                      'AUTO_REP_db_pass_erp': str(user.password),
                      'AUTO_REP_kettle_task_id' : str(id),
                      'AUTO_REP_kettle_task_attachment_id' : str(attachment_id),
                      }
            task = self.read(cr, uid, id, ['upload_file', 'parameters', 'transformation_id', 'output_file', 'name', 'server_id', 'last_date'], context)
            context['kettle_dir'] = self.pool.get('kettle.server').read(cr, uid, task['server_id'][0], ['kettle_dir'], context)['kettle_dir']
            
            if task['last_date']:
                context['filter']['AUTO_REP_last_date'] = task['last_date']
                
            if task['output_file']:
                context['filter'].update({'AUTO_REP_file_out' : str('openerp_tmp/output_'+ task['name'] + context['start_date'])})
                
            if task['upload_file']: 
                if not (context and context.get('input_filename',False)):
                    logger.notifyChannel('kettle-connector', netsvc.LOG_INFO, "the task " + task['name'] + " can't be executed because the anyone File was uploaded")
                    continue
                else:
                    context['filter'].update({'AUTO_REP_file_in' : str(context['input_filename']), 'AUTO_REP_file_in_name' : str(context['input_filename'])})
            
            context = self.execute_python_code(cr, uid, id, 'before', context)
            
            context['filter'].update(eval('{' + str(task['parameters'] or '')+ '}'))
            self.pool.get('kettle.transformation').execute_transformation(cr, uid, task['transformation_id'][0], log_file_name, attachment_id, context)

            context = self.execute_python_code(cr, uid, id, 'after', context)
            
            if context.get('input_filename',False):
                self.attach_file_to_task(cr, uid, id, context['input_filename'], '[FILE IN] FILE IMPORTED ' + context['start_date'], True, context)
        
            if task['output_file']:
                self.attach_output_file_to_task(cr, uid, id, context['filter']['AUTO_REP_file_out'], '[FILE OUT] FILE IMPORTED ' + context['start_date'], True, context)            
            
            self.write(cr, uid, [id], {'last_date' : context['start_date']})
        return True
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

    def _save_file(self, cr, uid, id, vals, context):
        kettle_dir = self.pool.get('kettle.task').browse(cr, uid, context['active_id'], ['server_id'], context).server_id.kettle_dir
        filename = kettle_dir + '/openerp_tmp/' + str(vals['filename'])
        fp = open(filename,'wb+')
        fp.write(base64.decodestring(vals['file']))
        fp.close()
        return 'openerp_tmp/' + vals['filename']

    def action_start_task(self, cr, uid, id, context):
        wizard = self.read(cr, uid, id,context=context)[0]
        if wizard['upload_file']:
            if not wizard['file']:
                raise osv.except_osv('Error !', 'You have to select a file before starting the task')
            else:
                context['input_filename'] = self._save_file(cr, uid, id, wizard, context)
        self.pool.get('kettle.task').start_kettle_task(cr, uid, [context['active_id']], context)
        return {'type': 'ir.actions.act_window_close'}

kettle_wizard()
