# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Joel Grand-guillaume (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from mx import DateTime
import netsvc
from osv import fields
from osv import osv
import decimal_precision as dp


####################################################################################
#  HR Timesheet analytic
####################################################################################
class hr_analytic_timesheet(osv.osv):
    _inherit = "hr.analytic.timesheet"
    
    # Infos mapping with project_task_work :
        # Taks Work             Hr analytic TS      Comments
        # 'name':               name
        # 'date':               date
        # 'hours':              unit_amount         Warning, here in a specific UoM
        # 'user_id':            user_id
        # 'company_id':         company_id
    
    def _compute_proj_unit(self, cr, uid, product_uom_id, unit_amount, context=None):
        """Compute the unit_amount entred by the user in project default unit if not the same.
        Store the value in 'hours' field like it was before with project_task_work"""
        default_uom = self.pool.get('res.users').browse(cr, uid, uid).company_id.project_time_mode_id.id
        uom_obj = self.pool.get('product.uom')
        res = 0.00
        if product_uom_id != default_uom:
            res = uom_obj._compute_qty(cr, uid, product_uom_id, unit_amount, default_uom)
        else:
            res = unit_amount
        return res

    _columns={
        'task_id':fields.many2one('project.task','Task', ondelete='set null'),
        # This field will always be computed regarding the project default UoM info's
        # I don't make a function field because OpenERP SA didn't do it in project timesheet
        # module, so I keep the same philosophy (but IMHO it is not good...).
        'hours': fields.float('Time Spent', readonly=True),
    }

    def on_change_unit_amount(self, cr, uid, id, prod_id, unit_amount, company_id, unit=False, journal_id=False, task_id=False,context=None):
        res = super(hr_analytic_timesheet,self).on_change_unit_amount(cr, uid, id, prod_id, unit_amount, company_id, unit, journal_id, context)
        if 'value' in res and task_id:
            aa = self.pool.get('project.task').browse(cr,uid,task_id).project_id.analytic_account_id
            res['value']['account_id'] = aa.id
            if aa.to_invoice:
                res['value']['to_invoice'] = aa.to_invoice.id
        return res
    
    def on_change_account_id(self, cr, uid, ids, account_id,context=None):
        """If project has only one open task, we choose it ! """
        # TODO: Could be improved for the user, for
        # example, we can make something like : if user has already made timesheet lines on a task
        # we suggest this one
        res = super(hr_analytic_timesheet,self).on_change_account_id(cr,uid,ids,account_id)
        if account_id:
            task_obj = self.pool.get('project.task')
            proj_obj = self.pool.get('project.project')
            proj_ids = proj_obj.search(cr,uid,[('analytic_account_id','=',account_id)])
            task_ids = task_obj.search(cr,uid,[('project_id','=',proj_ids),('state','=','open')])
            if len(task_ids) == 1:
                res['value']['task_id'] = task_ids[0]
        return res

    # I'm not sure about this way to do this, but OpenERP SA do it this way for project_timesheet
    # so I keep the same philosophy
    def create(self, cr, uid, vals, *args, **kwargs):
        context = kwargs.get('context', {})
        task_pool = self.pool.get('project.task')
        value = 0.0
        if 'unit_amount' in vals and (not vals['unit_amount']):
            vals['unit_amount'] = 0.00
        # In any possible case update the hours vals
        if 'product_uom_id' in vals and vals['product_uom_id'] and 'unit_amount' in vals:
            # We need to update the work done and the hours field
            value = self._compute_proj_unit(cr,uid,vals['product_uom_id'],vals['unit_amount'])
            vals['hours'] = value
        # If possible update the remaining hours in related task
        if 'task_id' in vals and vals['task_id']:
            task_remaining_hours = task_pool.read(cr, uid, vals['task_id'],
                                                  ['remaining_hours'],
                                                  context=context)['remaining_hours']
            task_pool.write(cr, uid,
                            vals['task_id'],
                            {'remaining_hours': task_remaining_hours - value},
                            context=context)
        return super(hr_analytic_timesheet,self).create(cr, uid, vals, *args, **kwargs)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if 'unit_amount' in vals and (not vals['unit_amount']):
            vals['unit_amount'] = 0.00
        task_pool = self.pool.get('project.task')
        for line in self.browse(cr, uid, ids, context=context):
            # Re-compute hours field and write it
            unit_amount = vals.get('unit_amount', line.unit_amount)
            uom = vals.get('product_uom_id', line.product_uom_id.id)
            new_value = self._compute_proj_unit(cr, uid, uom, unit_amount)
            vals['hours'] = new_value
            # If task id exists => update the remaining_hours fields of the related task
            if line.task_id:
                task_pool.write(cr, uid, line.task_id.id,
                                {'remaining_hours': line.task_id.remaining_hours - new_value + line.hours},
                                context=context)
        return super(hr_analytic_timesheet,self).write(cr, uid, ids, vals, context)

    def unlink(self, cr, uid, ids, *args, **kwargs):
        context = kwargs.get('context', {})
        task_pool = self.pool.get('project.task')
        for line in self.browse(cr, uid, ids):
            if line.task_id:
                new_value = self._compute_proj_unit(cr,uid,line.product_uom_id.id,line.unit_amount)
                task_pool.write(cr, uid, line.task_id.id,
                                {'remaining_hours': line.task_id.remaining_hours + new_value},
                                context=context)
        return super(hr_analytic_timesheet,self).unlink(cr, uid, ids,*args, **kwargs)

hr_analytic_timesheet()

