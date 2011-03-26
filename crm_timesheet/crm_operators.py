# -*- coding: utf-8 -*-
##############################################################################
#
#    crm_timesheet module for OpenERP, CRM Timesheet
#    Copyright (C) 2011 SYLEAM Info Services (<http://www.Syleam.fr/>) 
#              Sebastien LANGE <sebastien.lange@syleam.fr>
#
#    This file is a part of crm_timesheet
#
#    crm_timesheet is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    crm_timesheet is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


def duration_calc(self, cr, uid, ids, field_name, arg, context=None):
    res = {}
    for crm in self.browse(cr, uid, ids, context=context):
        res[crm.id] = 0.0
        for line in crm.timesheet_ids:
            res[crm.id] += line.hours
    return res

def get_crm(self, cr, uid, ids, context=None):
    result = {}
    for line in self.pool.get('crm.analytic.timesheet').browse(cr, uid, ids, context=context):
        result[line.res_id] = True
    return result.keys()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
