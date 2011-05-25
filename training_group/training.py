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

from operator import itemgetter

def check_cycle(self, cr, uid, ids, context=None):
    """ climbs the ``self._table.parent_id`` chains for 100 levels or
    until it can't find any more parent(s)

    Returns true if it runs out of parents (no cycle), false if
    it can recurse 100 times without ending all chains
    """
    level = 100
    while len(ids):
        cr.execute('SELECT DISTINCT parent_id '\
                    'FROM '+self._table+' '\
                    'WHERE id IN %s '\
                    'AND parent_id IS NOT NULL',(tuple(ids),))
        ids = map(itemgetter(0), cr.fetchall())
        if not level:
            return False
        level -= 1
    return True


class training_group(osv.osv):
    _inherit = 'training.group'
    _columns = {
        'parent_id' : fields.many2one('training.group', 'Parent Group'),
        'generate_seances' : fields.boolean('Generate Seances'),
    }
    
    _check_recursion = check_cycle
    _constraints = [
        (_check_recursion, 'Error! You can not create recursive parent group.', ['parent_id']),
    ]

training_group()
