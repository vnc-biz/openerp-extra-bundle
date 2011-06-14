# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from osv import osv, fields
from tools.translate import _


class training_course_add_wiki_wizard(osv.osv_memory):
    _name = 'training.course.add.wiki.wizard'

    _columns = {
        'keyword': fields.char('Keywords', size=64, required=True, help="Input a keyword to make a search."),
        'course_wiki_pages_wizard_ids': fields.many2many('wiki.wiki', 'training_course_wiki_wizard_rel', 'training_course_id', 'wiki_wiki_id', string = 'Wiki Docs'),
        'state':fields.selection([
            ('first','First'),
            ('second','Second'),
            ('done','Done'),
            ('selected','Selected'),
        ],'State', required=True, readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'first',
    }


    def selectWikis(self, cr, uid, ids, data, context={}):
        """Add wiki doc to training course"""
        add_wikis = self.browse(cr, uid, ids, context = context)
        for add_wiki in add_wikis:
            selected_wikis = self.pool.get('wiki.wiki').search(cr, uid, [('tags', 'ilike', add_wiki.keyword)])
            self.write(cr, uid, ids, {'course_wiki_pages_wizard_ids': [(6, 0, selected_wikis)]}, context = context)
        return self.write(cr, uid, ids, {'state': 'second'}, context = context)

    def addWikis(self, cr, uid, ids, data, context={}):
        """Add wiki doc to training course"""
        training_course = self.pool.get('training.course')
        add_wikis = self.browse(cr, uid, ids, context = context)
        values=[]
        for add_wiki in add_wikis:
            for wiki in add_wiki.course_wiki_pages_wizard_ids:
                values.append(wiki.id)
        training_course.write(cr, uid, data['active_ids'], {'course_wiki_pages_ids': [(6, 0, values)]}, context = context)
        self.write(cr, uid, ids, {'state': 'done'}, context = context)
        return {'type': 'ir.actions.act_window_close'}

training_course_add_wiki_wizard()

