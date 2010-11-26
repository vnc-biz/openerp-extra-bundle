# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
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

from osv import osv, fields

class groups(osv.osv):
    _inherit = 'res.groups'

    def _user_belongs_to(self, cr, uid, group):
        if uid == 1:
            return True
        if '.' not in group:
            return False

        module, group = group.split('.', 1)
        cr.execute("""SELECT count(1)
                        FROM res_groups_users_rel gur INNER JOIN ir_model_data imd ON (imd.res_id = gur.gid AND imd.model = 'res.groups')
                       WHERE imd.module = %s
                         AND imd.name = %s
                         AND gur.uid = %s
                   """, (module, group, uid))
        return bool(cr.fetchone()[0])

groups()

