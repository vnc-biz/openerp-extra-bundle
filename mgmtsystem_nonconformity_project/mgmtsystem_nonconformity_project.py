# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Savoir-faire Linux (<http://www.savoirfairelinux.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from osv import fields, osv
from project.project import project

class mgmtsystem_nonconformity_project(osv.osv):
    _inherit = "mgmtsystem.nonconformity"
    _columns = {
        'corrective_type': fields.selection((('task','Task'), ('project','Project')),'Corrective Action Type'),
        'corrective_project_id': fields.many2one('project.project', 'Corrective Project'),
        'preventive_type': fields.selection((('task','Task'), ('project','Project')),'Preventive Action Type'),
        'preventive_project_id': fields.many2one('project.project', 'Preventive Project'),
    }

mgmtsystem_nonconformity_project()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
