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


from osv import osv
from osv import fields


class crm_phonecall(osv.osv):
    _inherit = 'crm.phonecall'
    _name = "crm.phonecall"

    _columns = {
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete='cascade', ),
        'timesheet_ids': fields.one2many('crm.analytic.timesheet', 'res_id', 'Messages', domain=[('model', '=', _name)]),
    }

    def create(self, cr, uid, values, context=None):
        """
        Add model in context for crm_analytic_timesheet object
        """
        if context is None:
            context = {}
        # Add model for crm_timesheet
        context['model'] = self._name
        return super(crm_phonecall, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        """
        Add model in context for crm_analytic_timesheet object
        """
        if context is None:
            context = {}
        # Add model for crm_timesheet
        context['model'] = self._name
        return super(crm_phonecall, self).write(cr, uid, ids, values, context=context)

crm_phonecall()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
