# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
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

from osv import osv
import netsvc

class validate_courses(osv.osv_memory):
    _name = 'validate.courses'

    def validate_courses(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        workflow = netsvc.LocalService('workflow')
        course_obj = self.pool.get('training.course')
        for course in course_obj.browse(cr, uid, context.get('active_ids',[]), context=context):
            if course.state_course in ('pending','draft'):
                workflow.trg_validate(uid, 'training.course', course.id, 'signal_validate', cr)
        return {}

validate_courses()
