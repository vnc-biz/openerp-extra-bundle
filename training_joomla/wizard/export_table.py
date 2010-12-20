# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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

import netsvc
import pooler
import time
import urllib
import base64
from osv import osv
from tools.translate import _

def export_table(self, cr, uid, data, context, server, username, password, table, fields, filter = [], filterphp = ''):
    """Export (synchronize) the fields of the table to Joomla PHP server.
       Only the records matching the filter are exported.
       filterphp is the same filter in SQL notation to used in the PHP code.
       New records are inserted, existing records are updated and removed records are deleted"""

    logger = netsvc.Logger()
    pool = pooler.get_pool(cr.dbname)
    obj = table
    tbl = table.replace(".","_")
    new = 0
    update = 0

    try:
        server.openerp.resetTable(username, password, tbl)
    except:
        raise osv.except_osv(_('Error!'), _('No Joomla! connection or username not valid!\nTry again.'))

    elem_ids = pool.get(obj).search(cr, uid, filter)

    for elem in pool.get(obj).browse(cr, uid, elem_ids, context):
        vals = {}
        for field in fields:
            if field[-3:] == "_id":
                vals[field] = getattr(elem, field).id
            elif field[-4:] == "_ids":
                if field[-7:-4] == "_id":
                    # Special case: one2many used to access a many2many. E.g. course_course_id_ids => access to course_ids.course_id.id
                    words = field.split('_')
                    field2 = words[-3]+'_'+words[-2]
                    field = ('_'.join(words[:-3]))+'_ids'
                    vals[field] = [eval('c.'+field2+'.id') for c in getattr(elem, field)]
                else:
                    vals[field] = [c.id for c in getattr(elem, field)]
            else:
                vals[field] = getattr(elem, field)

        attach_ids = pool.get('ir.attachment').search(cr, uid, [('res_model','=',obj), ('res_id', '=',elem.id)])
        cont = 0
        for data in pool.get('ir.attachment').browse(cr, uid, attach_ids, context):
            s = data['datas_fname'].split('.')
            extension = s[-1].lower()
            s.pop()
            name = ".".join(s)
            #print name + " " + extension
            if extension in ['jpeg', 'jpe', 'jpg', 'gif', 'png']:
                if extension in ['jpeg', 'jpe', 'jpg']:
                    extension='jpeg'
                if not data['link']:
                    vals['picture'+str(cont)] = data['datas']
                else:
                    try:
                        vals['picture'+str(cont)] = base64.encodestring(urllib.urlopen(data['link']).read())
                    except:
                        continue
                vals['fname'+str(cont)] = name + '.' + extension
                cont = cont + 1
        logger.notifyChannel(_("Training Joomla"), netsvc.LOG_INFO, _("Table:%s,Value:%s") % (tbl, vals))
        try:
            if server.openerp.setTable(username, password, tbl, vals):
                new += 1
            else:
                update += 1
        except:
            raise osv.except_osv(_('Error!'), _('No Joomla! connection or username not valid!\nTry again.'))

    try:
        delete = server.openerp.deleteTable(username, password, tbl, filterphp)
    except:
        raise osv.except_osv(_('Error!'), _('No Joomla! connection or username not valid!\nTry again.'))

    return (new, update, delete)


def export_write(self, cr, uid, server, table, ids, vals, context):
    """Synchronize the fields defined in vals of the table to Joomla PHP server.
       Only the records with ids are exported.
       New records are inserted, existing records are updated"""
    pool = pooler.get_pool(cr.dbname)
    obj = table
    tbl = table.replace(".","_")
    new = 0
    update = 0
    for field in vals.keys():
        if field[-4:] == "_ids":
            vals[field] = vals[field][0][2]
    for id in ids:
        vals['id'] = id

        attach_ids = pool.get('ir.attachment').search(cr, uid, [('res_model','=',obj), ('res_id', '=',id)])
        cont = 0
        for data in pool.get('ir.attachment').browse(cr, uid, attach_ids, context):
            s = data['datas_fname'].split('.')
            extension = s[-1].lower()
            s.pop()
            name = ".".join(s)
            #print name + " " + extension
            if extension in ['jpeg', 'jpe', 'jpg', 'gif', 'png']:
                if extension in ['jpeg', 'jpe', 'jpg']:
                    extension='jpeg'
                if not data['link']:
                    vals['picture'+str(cont)] = data['datas']
                else:
                    try:
                        vals['picture'+str(cont)] = base64.encodestring(urllib.urlopen(data['link']).read())
                    except:
                        continue
                vals['fname'+str(cont)] = name + '.' + extension
                cont = cont + 1
        #print vals

        if server.openerp.setTable(username, password, tbl, vals):
            new += 1
        else:
            update += 1

    return (new, update)


def export_ulink(self, cr, uid, server, table, ids, table_rel=None, field_rel=None):
    """Synchronize the table to Joomla PHP server.
       Only the records with ids are deleted.
       If table_rel and field_rel are defined, also deletes the records in the table_rel"""
    tbl = table.replace(".","_")
    delete = server.openerp.deleteItems(username, password, tbl, ids, "id")
    if table_rel != None:
        tbl = table_rel.replace(".","_")
        server.openerp.deleteItems(username, password, tbl, ids, field_rel)
    return delete
