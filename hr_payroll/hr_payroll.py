#!/usr/bin/env python
#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
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

import time
import netsvc

from osv import osv
from osv import fields
from tools import config
from tools.translate import _

class hr_passport(osv.osv):
    '''
    Passport Detail
    '''
    _name = 'hr.passport'
    _description = 'Passport Detail'
    
    _columns = {
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
        'name':fields.char('Passport No', size=64, required=True, readonly=False),
        'country_id':fields.many2one('res.country', 'Country of Issue', required=True),
        'date_issue': fields.date('Passport Issue Date'),
        'date_expire': fields.date('Passport Expire Date'),
        'contracts_ids':fields.one2many('hr.contract', 'passport_id', 'Contracts', required=False, readonly=True),
    }
hr_passport()

class hr_employee_grade(osv.osv):
    _name = 'hr.employee.grade'
    _description = 'Function of the Employee'
    _inherits = {
        'res.partner.function': 'function_id',
    }
    _columns = {
        'function_id':fields.many2one('res.partner.function', 'Function', required=False),
        'line_ids':fields.one2many('hr.payslip.line', 'function_id', 'Salary Structure', required=False),
        'account_id':fields.many2one('account.analytic.account', 'Analytic Account', required=False),
    }
hr_employee_grade()

class hr_contract(osv.osv):

    _inherit = 'hr.contract'
    _description = 'Employee Contract'
    
    _columns = {
        'permit_no':fields.char('Work Permit No', size=256, required=False, readonly=False),
        'passport_id':fields.many2one('hr.passport', 'Passport', required=False),
        'visa_no':fields.char('Visa No', size=64, required=False, readonly=False),
        'visa_expire': fields.date('Visa Expire Date'),
        'function' : fields.many2one('hr.employee.grade', 'Function'),
        'working_days_per_week': fields.integer('Working Days / Week')
    }
    _defaults = {
        'working_days_per_week': lambda *args: 5
    }
hr_contract()

class payroll_register(osv.osv):
    '''
    Payroll Register
    '''
    _name = 'hr.payroll.register'
    _description = 'Payroll Register'
    
    def _calculate(self, cr, uid, ids, field_names, arg, context):
        res = {}
        allounce = 0.0
        deduction = 0.0
        net = 0.0
        grows = 0.0
        for register in self.browse(cr, uid, ids, context):
            for slip in register.line_ids:
                allounce += slip.allounce
                deduction += slip.deduction
                net += slip.net
                grows += slip.grows
                
            res[register.id] = {
                'allounce':allounce,
                'deduction':deduction,
                'net':net,
                'grows':grows
            }
        return res
        
    _columns = {
        'name':fields.char('Name', size=64, required=True, readonly=False),
        'date': fields.date('Date', required=True),
        'number':fields.char('Number', size=64, required=False, readonly=True),
        'line_ids':fields.one2many('hr.payslip', 'register_id', 'Payslips', required=False),
        'state':fields.selection([
            ('new','New Slip'),
            ('draft','Wating for Verification'),
            ('hr_check','Wating for HR Verification'),
            ('accont_check','Wating for Account Verification'),
            ('confirm','Confirm Sheet'),
            ('done','Paid Salary'),
            ('cancel','Reject'),
        ],'State', select=True, readonly=True),
        'journal_id': fields.many2one('account.journal', 'Expanse Journal', required=True),
        'bank_journal_id': fields.many2one('account.journal', 'Bank Journal', required=True),
        'active':fields.boolean('Active', required=False),
#        'advice_ids':fields.one2many('hr.payroll.advice', 'register_id', 'Bank Advice'),
        'company_id':fields.many2one('res.company', 'Company', required=False),
        'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], help="Keep empty to use the period of the validation(Payslip) date."),
        'grows': fields.function(_calculate, method=True, store=True, multi='dc', string='Gross Salary', type='float', digits=(16, int(config['price_accuracy']))),
        'net': fields.function(_calculate, method=True, store=True, multi='dc', string='Net Salary', digits=(16, int(config['price_accuracy']))),
        'allounce': fields.function(_calculate, method=True, store=True, multi='dc', string='Allowance', digits=(16, int(config['price_accuracy']))),
        'deduction': fields.function(_calculate, method=True, store=True, multi='dc', string='Deduction', digits=(16, int(config['price_accuracy']))),        
    }
    
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'new',
        'active': lambda *a: True
    }
    
    def compute_sheet(self, cr, uid, ids, context={}):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        func_pool = self.pool.get('hr.employee.grade')
        slip_line_pool = self.pool.get('hr.payslip.line')
        wf_service = netsvc.LocalService("workflow")
        
        vals = self.read(cr, uid, ids)[0]
        
        emp_ids = emp_pool.search(cr, uid, [])
        
        for emp in emp_pool.browse(cr, uid, emp_ids):
            old_slips = slip_pool.search(cr, uid, [('employee_id','=',emp.id), ('date','=',vals['date'])])
            if old_slips:
                slip_pool.write(cr, uid, old_slips, {'register_id':ids[0]})
                for sid in old_slips:
                    wf_service.trg_validate(uid, 'hr.payslip', sid, 'compute_sheet', cr)
                continue
            
            sql_req= '''
                SELECT c.wage as wage, function as function
                FROM hr_contract c
                  LEFT JOIN hr_employee emp on (c.employee_id=emp.id)
                  LEFT JOIN hr_contract_wage_type cwt on (cwt.id = c.wage_type_id)
                  LEFT JOIN hr_contract_wage_type_period p on (cwt.period_id = p.id)
                WHERE
                  (emp.id=%s) AND
                  (date_start <= %s) AND
                  (date_end IS NULL OR date_end >= %s)
                LIMIT 1
                '''
            cr.execute(sql_req, (emp.id, vals['date'], vals['date']))
            contract_info = cr.dictfetchone()

            if not contract_info:
                continue
            
            function = contract_info['function']
            lines = []
            if function:
                func = func_pool.read(cr, uid, function, ['line_ids'])
                lines = slip_line_pool.browse(cr, uid, func['line_ids'])
            
            res = {
                'employee_id':emp.id,
                'basic':contract_info['wage'],
                'register_id':ids[0],
                'name':vals['name'],
                'date':vals['date'],
                'journal_id':vals['journal_id'][0],
                'bank_journal_id':vals['bank_journal_id'][0]
            }
            slip_id = slip_pool.create(cr, uid, res)

            old_slip_id = slip_line_pool.search(cr, uid, [('slip_id','=',slip_id)])
            slip_line_pool.unlink(cr, uid, old_slip_id)
            
            for line in lines:
                slip_line_pool.copy(cr, uid, line.id, {'slip_id':slip_id, 'employee_id':False, 'function_id':False}, {})
            
            for line in emp.line_ids:
                slip_line_pool.copy(cr, uid, line.id, {'slip_id':slip_id, 'employee_id':False, 'function_id':False}, {})
                
            wf_service.trg_validate(uid, 'hr.payslip', slip_id, 'compute_sheet', cr)
        
        number = self.pool.get('ir.sequence').get(cr, uid, 'salary.register')
        self.write(cr, uid, ids, {'state':'draft', 'number':number})
        return True

    def verify_sheet(self, cr, uid, ids, context={}):
        slip_pool = self.pool.get('hr.payslip')
        
        for id in ids:
            sids = slip_pool.search(cr, uid, [('register_id','=',id)])
            wf_service = netsvc.LocalService("workflow")
            for sid in sids:
                wf_service.trg_validate(uid, 'hr.payslip', sid, 'verify_sheet', cr)
        
        self.write(cr, uid, ids, {'state':'hr_check'})
        return True
    
    def verify_twice_sheet(self, cr, uid, ids, context={}):
        slip_pool = self.pool.get('hr.payslip')
        
        for id in ids:
            sids = slip_pool.search(cr, uid, [('register_id','=',id), ('state','=','hr_check')])
            wf_service = netsvc.LocalService("workflow")
            for sid in sids:
                wf_service.trg_validate(uid, 'hr.payslip', sid, 'verify_twice_sheet', cr)
        
        self.write(cr, uid, ids, {'state':'accont_check'})
        return True
    
    def final_verify_sheet(self, cr, uid, ids, context={}):
        slip_pool = self.pool.get('hr.payslip')
        advice_pool = self.pool.get('hr.payroll.advice')
        advice_line_pool = self.pool.get('hr.payroll.advice.line')
        
        for id in ids:
            sids = slip_pool.search(cr, uid, [('register_id','=',id), ('state','=','accont_check')])
            wf_service = netsvc.LocalService("workflow")
            for sid in sids:
                wf_service.trg_validate(uid, 'hr.payslip', sid, 'final_verify_sheet', cr)

        
        for reg in self.browse(cr, uid, ids):
            accs = {}
            for slip in reg.line_ids:
                pid = False
                if accs.get(slip.employee_id.property_bank_account.code, False) == False:
                    advice = {
                        'name': 'Payment Advice from %s / Bank Account %s' % (self.pool.get('res.users').browse(cr, uid, uid).company_id.name, slip.employee_id.property_bank_account.name),
                        'number': self.pool.get('ir.sequence').get(cr, uid, 'payment.advice'),
                        'register_id':reg.id,
                        'account_id':slip.employee_id.property_bank_account.id
                    }
                    pid = advice_pool.create(cr, uid, advice)
                    accs[slip.employee_id.property_bank_account.code] = pid
                else:
                    pid = accs[slip.employee_id.property_bank_account.code]
                
                pline = {
                    'advice_id':pid,
                    'name':slip.employee_id.otherid,
                    'employee_id':slip.employee_id.id,
                    'amount':slip.other_pay + slip.net,
                    'bysal':slip.net
                }
                id = advice_line_pool.create(cr, uid, pline)
        
        
        #, 'advice_ids':[(6, 0, [pid])]
        self.write(cr, uid, ids, {'state':'confirm'})
        return True

    def process_sheet(self, cr, uid, ids, context={}):
        slip_pool = self.pool.get('hr.payslip')
        for id in ids:
            sids = slip_pool.search(cr, uid, [('register_id','=',id), ('state','=','confirm')])
            wf_service = netsvc.LocalService("workflow")
            for sid in sids:
                wf_service.trg_validate(uid, 'hr.payslip', sid, 'process_sheet', cr)
        
        self.write(cr, uid, ids, {'state':'done'})
        return True

payroll_register()

class payroll_advice(osv.osv):
    '''
    Bank Advice Note
    '''
    _name = 'hr.payroll.advice'
    _description = 'Bank Advice Note'
    
    _columns = {
        'register_id':fields.many2one('hr.payroll.register', 'Payroll Register', required=False),
        'name':fields.char('Name', size=2048, required=True, readonly=False),
        'note': fields.text('Description'),
        'date': fields.date('Date'),
        'state':fields.selection([
            ('draft','Draft Sheet'),
            ('confirm','Confirm Sheet'),
            ('cancel','Reject'),
        ],'State', select=True, readonly=True),
        'number':fields.char('Number', size=64, required=False, readonly=True),
        'line_ids':fields.one2many('hr.payroll.advice.line', 'advice_id', 'Employee Salary', required=False),
        'chaque_nos':fields.char('Chaque Nos', size=256, required=False, readonly=False),
        'account_id': fields.many2one('account.account', 'Account', required=True),
    }
    
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft'
    }
    
    def confirm_sheet(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'confirm'})
        return True
        
    def set_to_draft(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'draft'})
        return True

    def cancel_sheet(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True

payroll_advice()

from datetime import date, datetime, timedelta
def prev_bounds(cdate=False):
    when = datetime.fromtimestamp(time.mktime(time.strptime(cdate,"%Y-%m-%d")))
    this_first = date(when.year, when.month, 1)
    month = when.month + 1
    year = when.year
    if month > 12:
        month = 1
        year += 1
    next_month = date(year, month, 1)
    prev_end = next_month - timedelta(days=1)
    return this_first, prev_end

class payroll_advice_line(osv.osv):
    '''
    Bank Advice Lines
    '''
    _name = 'hr.payroll.advice.line'
    _description = 'Bank Advice Lines'
    
    _columns = {
        'advice_id':fields.many2one('hr.payroll.advice', 'Bank Advice', required=False),
        'name':fields.char('Bank Account A/C', size=64, required=True, readonly=False),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
        'amount': fields.float('Amount', digits=(16, int(config['price_accuracy']))),
        'bysal': fields.float('By Salary', digits=(16, int(config['price_accuracy']))),
        'flag':fields.char('D/C', size=8, required=True, readonly=False),
    }
    _defaults = {
        'flag': lambda *a: 'C',
    }
    
    def onchange_employee_id(self, cr, uid, ids, ddate, employee_id, context={}):
        
        vals = {}
        slip_pool = self.pool.get('hr.payslip')        
        if employee_id:
            dates = prev_bounds(ddate)
            sids = False
            sids = slip_pool.search(cr, uid, [('paid','=',False),('state','=','confirm'),('date','>=',dates[0]), ('employee_id','=',employee_id), ('date','<=',dates[1])])
            if sids:
                slip = slip_pool.browse(cr, uid, sids[0])
                vals['name'] = slip.employee_id.otherid
                vals['amount'] = slip.net + slip.other_pay
                vals['bysal'] = slip.net
        return {
            'value':vals
        }
payroll_advice_line()

class payment_category(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'hr.allounce.deduction.categoty'
    _description = 'Allowance Deduction Categoty'
    
    _columns = {
        'name':fields.char('Categoty Name', size=64, required=True, readonly=False),
        'code':fields.char('Categoty Code', size=64, required=True, readonly=False),
        'type':fields.selection([
            ('allow','Allowance'),
            ('deduct','Deduction'),
            ('other','Others'),
        ],'Type', select=True),
        'contribute':fields.boolean('Contribe by Company ?'),
        'include_in_salary':fields.boolean('Included in Salary ?'),
        'based_on':fields.selection([
            ('basic','Basic Salary'),
            ('work','On Attendance'),
            ('fixed','Fided Value'),
        ],'State', select=True),
        'gratuity':fields.boolean('Use for Gratuity ?', required=False),
        'line_ids':fields.one2many('hr.allounce.deduction.categoty.line', 'category_id', 'Calculations', required=False),
        'base':fields.char('Based on', size=64, required=False, readonly=False),
        'condition':fields.char('Condition', size=64, required=False, readonly=False),
        'sequence': fields.integer('Sequence'),
    }
    _defaults = {
        'condition': lambda *a: 'True',
        'base': lambda *a:'object.basic'
    }
payment_category()

class payment_category_line(osv.osv):
    '''
    Allowance Deduction Categoty
    '''
    _name = 'hr.allounce.deduction.categoty.line'
    _description = 'Allowance Deduction Categoty'
    
    _columns = {
        'category_id':fields.many2one('hr.allounce.deduction.categoty', 'Category', required=False),
        'name':fields.char('Name', size=64, required=False, readonly=False),
        'umo_id':fields.many2one('product.uom', 'Unite', required=False),
        'from': fields.float('From', digits=(16, int(config['price_accuracy']))),
        'to': fields.float('To', digits=(16, int(config['price_accuracy']))),
        'amount_type':fields.selection([
            ('per','Percentage (%)'),
            ('fix','Fixed Amount'),
        ],'Amount Type', select=True),
        'value': fields.float('Value', digits=(16, int(config['price_accuracy']))),
    }
payment_category_line()

class hr_holidays_status(osv.osv):
    _inherit = "hr.holidays.status"
    
    _columns = {
        'type':fields.selection([
            ('paid','Paid Holiday'), 
            ('unpaid','Un-Paid Holiday'), 
            ('halfpaid','Half-Pay Holiday')
            ], string='Payment'),
        'account_id': fields.many2one('account.account', 'Account', required=True),
        'analytic_account_id':fields.many2one('account.analytic.account', 'Analytic Account', required=False),
        'head_id': fields.many2one('hr.allounce.deduction.categoty', 'Payroll Head', domain=[('type','=','other')]),
        'code':fields.char('Code', size=64, required=True, readonly=False),
    }
    _defaults = {
        'type': lambda *args: 'unpaid'
    }
hr_holidays_status()

class hr_expense_expense(osv.osv):
    _inherit = "hr.expense.expense"
    _description = "Expense"
    _columns = {
        'category_id':fields.many2one('hr.allounce.deduction.categoty', 'Payroll Head', domain=[('type','=','other')]),
    }
hr_expense_expense()

class hr_payslip(osv.osv):
    '''
    Pay Slip
    '''
    _name = 'hr.payslip'
    _description = 'Pay Slip'
    
    def _calculate(self, cr, uid, ids, field_names, arg, context):
        res = {}
        for rs in self.browse(cr, uid, ids, context):
            allow = 0.0
            deduct = 0.0
            others = 0.0
            obj = {'basic':rs.basic}
            
            for line in rs.line_ids:
                amount = 0.0
                
                if line.amount_type == 'per':
                    amount = line.amount * eval(line.category_id.base, obj)
                elif line.amount_type == 'fix':
                    amount = line.amount

                cd = line.category_id.code.lower()
                obj[cd] = amount
                
                self.pool.get('hr.payslip.line').write(cr, uid, [line.id], {'total':amount})
                
                if line.type == 'allounce':
                    allow += amount
                elif line.type == 'deduction':
                    deduct += amount
                elif line.type == 'advance':
                    others += amount
                elif line.type == 'loan':
                    others += amount
                elif line.type == 'otherpay':
                    others += amount
                
            record = {
                'allounce':allow,
                'deduction':deduct,
                'grows':rs.basic + allow,
                'net':rs.basic + allow - deduct,
                'other_pay':others,
                'total_pay': rs.basic + allow - deduct + others
            }
            res[rs.id] = record
        
        return res
    
    _columns = {
        'deg_id':fields.many2one('hr.employee.grade', 'Designation', required=False),
        'register_id':fields.many2one('hr.payroll.register', 'Register', required=False),
        'journal_id': fields.many2one('account.journal', 'Expanse Journal', required=True),
        'bank_journal_id': fields.many2one('account.journal', 'Bank Journal', required=True),
        'payment_id': fields.many2one('account.move', 'Payment Entries', readonly=True),
        
        'name':fields.char('Name', size=64, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'number':fields.char('Number', size=64, required=False, readonly=True),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
        'date': fields.date('Date'),
        'state':fields.selection([
            ('new','New Slip'),
            ('draft','Wating for Verification'),
            ('hr_check','Wating for HR Verification'),
            ('accont_check','Wating for Account Verification'),
            ('confirm','Confirm Sheet'),
            ('done','Paid Salary'),
            ('cancel','Reject'),
        ],'State', select=True, readonly=True),
        'basic_before_leaves': fields.float('Basic Salary', readonly=True,  digits=(16, int(config['price_accuracy']))),
        'leaves': fields.float('Leaved Deduction', readonly=True,  digits=(16, int(config['price_accuracy']))),
        'basic': fields.float('Basic Salary - Leaves', readonly=True,  digits=(16, int(config['price_accuracy']))),
        'grows': fields.function(_calculate, method=True, store=True, multi='dc', string='Gross Salary', type='float', digits=(16, int(config['price_accuracy']))),
        'net': fields.function(_calculate, method=True, store=True, multi='dc', string='Net Salary', digits=(16, int(config['price_accuracy']))),
        'allounce': fields.function(_calculate, method=True, store=True, multi='dc', string='Allowance', digits=(16, int(config['price_accuracy']))),
        'deduction': fields.function(_calculate, method=True, store=True, multi='dc', string='Deduction', digits=(16, int(config['price_accuracy']))),
        'other_pay': fields.function(_calculate, method=True, store=True, multi='dc', string='Others', digits=(16, int(config['price_accuracy']))),
        'total_pay': fields.function(_calculate, method=True, store=True, multi='dc', string='Total Payment', digits=(16, int(config['price_accuracy']))),
        'line_ids':fields.one2many('hr.payslip.line', 'slip_id', 'Payslip Line', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'move_id':fields.many2one('account.move', 'Expanse Entries', required=False, readonly=True),
        'move_line_ids':fields.many2many('account.move.line', 'payslip_lines_rel', 'slip_id', 'line_id', 'Accounting Lines', readonly=True),
        'move_payment_ids':fields.many2many('account.move.line', 'payslip_payment_rel', 'slip_id', 'payment_id', 'Payment Lines', readonly=True),
        'company_id':fields.many2one('res.company', 'Company', required=False),
        'period_id': fields.many2one('account.period', 'Force Period', domain=[('state','<>','done')], help="Keep empty to use the period of the validation(Payslip) date."),
        'holiday_days': fields.integer('No of Leaves', readonly=True),
        'worked_days': fields.integer('Worked Day', readonly=True),
        'working_days': fields.integer('Working Days', readonly=True),
        'paid':fields.boolean('Paid ? ', required=False),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'new'
    }
    
    def set_to_draft(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def cancel_sheet(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    
    def process_sheet(self, cr, uid, ids, context={}):
        move_pool = self.pool.get('account.move')
        movel_pool = self.pool.get('account.move.line')
        
        for slip in self.browse(cr,uid,ids):
            
            line_ids = []
            partner = False
            partner_id = False
            
            partner = slip.employee_id.address_home_id.partner_id
            partner_id = partner.id
            
            period_id = self.pool.get('account.period').search(cr,uid,[('date_start','<=',slip.date),('date_stop','>=',slip.date)])[0]
            move = {
                #'name': "Payment of Salary to %s" % (slip.employee_id.name), 
                'journal_id': slip.bank_journal_id.id,
                'period_id': period_id, 
                'date': slip.date,
                'type':'bank_pay_voucher',
                'ref':slip.number,
                'narration': 'Payment of Salary to %s' % (slip.employee_id.name)
            }
            move_id = move_pool.create(cr, uid, move)
            
            name = "To %s account" % (slip.employee_id.name)
            ded_rec = {
                'move_id':move_id,
                'name': name,
                #'partner_id': partner_id,
                'date': slip.date, 
                'account_id': slip.employee_id.property_bank_account.id, 
                'debit': 0.0,
                'credit' : slip.net,
                'journal_id' : slip.journal_id.id,
                'period_id' :period_id
            }
            line_ids += [movel_pool.create(cr, uid, ded_rec)]
            name = "By %s account" % (slip.employee_id.property_bank_account.name)
            cre_rec = {
                'move_id':move_id,
                'name': name,
                'partner_id': partner_id,
                'date': slip.date,
                'account_id': partner.property_account_payable.id,
                'debit':  slip.net,
                'credit' : 0.0,
                'journal_id' : slip.journal_id.id,
                'period_id' :period_id
            }
            line_ids += [movel_pool.create(cr, uid, cre_rec)]
            
            rec = {
                'state':'done',
                'payment_id':move_id,
                'move_payment_ids':[(6, 0, line_ids)],
                'paid':True
            }
            self.write(cr, uid, [slip.id], rec)
            
            invoice_pool = self.pool.get('account.invoice')
            for line in slip.line_ids:
                if line.type == 'otherpay' and line.expanse_id.invoice_id:
                    if not line.expanse_id.invoice_id.move_id:
                        raise osv.except_osv(_('Warning !'), _('Please Confirm all Expanse Invoice appear for Reimbursement'))
                    invids = [line.expanse_id.invoice_id.id]
                    amount = line.total
                    acc_id = slip.bank_journal_id.default_credit_account_id and slip.bank_journal_id.default_credit_account_id.id
                    period_id = slip.period_id.id
                    journal_id = slip.bank_journal_id.id
                    invoice_pool.pay_and_reconcile(cr, uid, invids, amount, acc_id, period_id, journal_id, False, period_id, False, context, line.name)
            
        return True
    
    def account_check_sheet(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'accont_check'})
        return True
    
    def hr_check_sheet(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state':'hr_check'})
        return True
    
    def verify_sheet(self, cr, uid, ids, context={}):
        
        move_pool = self.pool.get('account.move')
        movel_pool = self.pool.get('account.move.line')
        exp_pool = self.pool.get('hr.expense.expense')
        
        for slip in self.browse(cr,uid,ids):
            total_deduct = 0.0
            
            line_ids = []
            partner = False
            partner_id = False
            
            if not slip.employee_id.address_home_id:
                raise osv.except_osv(_('Integrity Error !'), _('Please defined the Employee Home Address Along with Partners !!'))
            
            if not slip.employee_id.address_home_id.partner_id:
                raise osv.except_osv(_('Integrity Error !'), _('Please defined the Partner in Home Address !!'))
            
            partner = slip.employee_id.address_home_id.partner_id
            partner_id = slip.employee_id.address_home_id.partner_id.id
            
            period_id = False
            
            if slip.period_id:
                period_id = slip.period_id.id
            else:
                period_id = self.pool.get('account.period').search(cr,uid,[('date_start','<=',slip.date),('date_stop','>=',slip.date)])[0]
            
            move = {
                #'name': slip.name, 
                'journal_id': slip.journal_id.id,
                'period_id': period_id, 
                'date': slip.date,
                'ref':slip.number,
                'narration': slip.name
            }
            move_id = move_pool.create(cr, uid, move)
            
            line = {
                'move_id':move_id,
                'name': "By Basic Salary / " + slip.employee_id.name,
                'date': slip.date,
                'account_id': slip.employee_id.salary_account.id, 
                'debit': slip.basic,
                'credit': 0.0,
                'quantity':slip.working_days,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
                'analytic_account_id': False,
                'ref':slip.number
            }
            
            #Setting Analysis Account for Basic Salary
            if slip.employee_id.analytic_account:
                line['analytic_account_id'] = slip.employee_id.analytic_account.id
            
            move_line_id = movel_pool.create(cr, uid, line)
            line_ids += [move_line_id]
            
            line = {
                'move_id':move_id,
                'name': "To Basic Paysble Salary / " + slip.employee_id.name,
                'partner_id': partner_id,
                'date': slip.date, 
                'account_id': slip.employee_id.employee_account.id, 
                'debit': 0.0,
                'quantity':slip.working_days,
                'credit': slip.basic,
                'journal_id': slip.journal_id.id,
                'period_id': period_id
            }
            line_ids += [movel_pool.create(cr, uid, line)]
            
            for line in slip.line_ids:
                name = "[%s] - %s / %s" % (line.code, line.name, slip.employee_id.name)
                amount = 0.0
                if line.amount_type == 'per':
                    amount= (line.slip_id.basic * line.amount)
                elif line.amount_type == 'fix':
                    amount = line.amount
                
                if line.type == 'leaves':
                    continue
                
                rec = {
                    'move_id':move_id,
                    'name': name,
                    'date': slip.date, 
                    'account_id': line.account_id.id, 
                    'debit': 0.0,
                    'credit' : 0.0,
                    'journal_id' : slip.journal_id.id,
                    'period_id' :period_id,
                    'analytic_account_id':False,
                    'ref':slip.number,
                    'quantity':1
                }
                
                #Setting Analysis Account for Salary Slip Lines
                if line.analytic_account_id:
                    rec['analytic_account_id'] = line.analytic_account_id.id
                else: 
                    rec['analytic_account_id'] = slip.deg_id.account_id.id
                    
                if line.type == 'allounce' or line.type == 'otherpay':
                    rec['debit'] = amount
                    ded_rec = {
                        'move_id':move_id,
                        'name': name,
                        'partner_id': partner_id,
                        'date': slip.date, 
                        'account_id': partner.property_account_payable.id, 
                        'debit': 0.0,
                        'quantity':1,
                        'credit' : amount,
                        'journal_id' : slip.journal_id.id,
                        'period_id' :period_id
                    }
                    line_ids += [movel_pool.create(cr, uid, ded_rec)]
                elif line.type == 'deduction' or line.type == 'otherdeduct':
                    rec['credit'] = amount
                    total_deduct += amount
                    ded_rec = {
                        'move_id':move_id,
                        'name': name,
                        'partner_id': partner_id,
                        'date': slip.date, 
                        'quantity':1,
                        'account_id': partner.property_account_receivable.id, 
                        'debit': amount,
                        'credit' : 0.0,
                        'journal_id' : slip.journal_id.id,
                        'period_id' :period_id
                    }
                    line_ids += [movel_pool.create(cr, uid, ded_rec)]
                
                line_ids += [movel_pool.create(cr, uid, rec)]
                
            if total_deduct > 0:
                move = {
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'date': slip.date,
                    'ref':slip.number,
                    'narration': 'Adjustment : %s' % (slip.name)
                }
                adj_move_id = move_pool.create(cr, uid, move)
                name = "Adjustment Entry - %s" % (slip.employee_id.name)
                ded_rec = {
                    'move_id':adj_move_id,
                    'name': name,
                    'partner_id': partner_id,
                    'date': slip.date, 
                    'account_id': partner.property_account_receivable.id, 
                    'debit': 0.0,
                    'quantity':1,
                    'credit' : total_deduct,
                    'journal_id' : slip.journal_id.id,
                    'period_id' :period_id
                }
                line_ids += [movel_pool.create(cr, uid, ded_rec)]
                cre_rec = {
                    'move_id':adj_move_id,
                    'name': name,
                    'partner_id': partner_id,
                    'date': slip.date,
                    'account_id': partner.property_account_payable.id, 
                    'debit': total_deduct,
                    'quantity':1,
                    'credit' : 0.0,
                    'journal_id' : slip.journal_id.id,
                    'period_id' :period_id
                }
                line_ids += [movel_pool.create(cr, uid, cre_rec)]

            rec = {
                'state':'confirm',
                'move_id':move_id, 
                'move_line_ids':[(6, 0,line_ids)],
            }
            if not slip.period_id:
                rec['period_id'] = period_id
            
            dates = prev_bounds(slip.date)
            exp_ids = exp_pool.search(cr, uid, [('date_valid','>=',dates[0]), ('date_valid','<=',dates[1]), ('state','=','invoiced')])
            if exp_ids:
                acc = self.pool.get('ir.property').get(cr, uid, 'property_account_expense_categ', 'product.category')
                for exp in exp_pool.browse(cr, uid, exp_ids):
                    exp_res = {
                        'name':exp.name,
                        'amount_type':'fix',
                        'type':'otherpay',
                        'category_id':exp.category_id.id,
                        'amount':exp.amount,
                        'slip_id':slip.id,
                        'expanse_id':exp.id,
                        'account_id':acc
                    }
                    self.pool.get('hr.payslip.line').create(cr, uid, exp_res)
            
            self.write(cr, uid, [slip.id], rec)
            
        return True
    
    def compute_sheet(self, cr, uid, ids, context={}):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        func_pool = self.pool.get('hr.employee.grade')
        slip_line_pool = self.pool.get('hr.payslip.line')
        holiday_pool = self.pool.get('hr.holidays')
        
        vals = self.read(cr, uid, ids)[0]
        emp_ids = ids
        
        for slip in self.browse(cr, uid, ids):
            allow = 0.0
            #for emp in emp_pool.browse(cr, uid, [vals['employee_id'][0]]):
            emp = slip.employee_id
            sql_req= '''
                SELECT c.id as id, c.wage as wage, function as function
                FROM hr_contract c
                  LEFT JOIN hr_employee emp on (c.employee_id=emp.id)
                  LEFT JOIN hr_contract_wage_type cwt on (cwt.id = c.wage_type_id)
                  LEFT JOIN hr_contract_wage_type_period p on (cwt.period_id = p.id)
                WHERE
                  (emp.id=%s) AND
                  (date_start <= %s) AND
                  (date_end IS NULL OR date_end >= %s)
                LIMIT 1
                '''
            cr.execute(sql_req, (emp.id, vals['date'], vals['date']))
            contract_id = cr.dictfetchone()
            
            if not contract_id:
                continue
            
            contract = self.pool.get('hr.contract').browse(cr, uid, contract_id['id'])
            
            sal_type = contract.wage_type_id.type
            
            function = contract.function.id
            
            lines = []
            if function:
                func = func_pool.read(cr, uid, function, ['line_ids'])
                lines = slip_line_pool.browse(cr, uid, func['line_ids'])

            old_slip_id = slip_line_pool.search(cr, uid, [('slip_id','=',slip.id)])
            slip_line_pool.unlink(cr, uid, old_slip_id)
            
            ad = []
            lns = {}
            all_per = 0.0
            ded_per = 0.0
            all_fix = 0.0
            ded_fix = 0.0
            
            obj = {'basic':0.0}
            for line in lines:
                cd = line.code.lower()
                obj[cd] = line.amount
            
            for line in lines:
                if line.category_id.code in ad:
                    continue
                ad.append(line.category_id.code)
                
                cd = line.category_id.code.lower()
                #obj[cd] = line.amount
                
                if sal_type == 'net':
                    if line.amount_type == 'per':
                        exp = line.category_id.base
                        try:
                            amt = eval(exp, obj)
                        except Exception, e:
                            raise osv.except_osv(_('Variable Error !'), _('Variable Error : %s ' % (e)))
                        if amt <= 0:
                            amt =line.amount
                        else:
                            amt =  line.amount + (amt * line.amount)
                        if line.type == 'allounce':
                            all_per += amt
                        elif line.type == 'deduction':
                            ded_per += amt
                    elif line.amount_type == 'fix':
                        if line.type == 'allounce':
                            all_fix += line.amount
                        elif line.type == 'deduction':
                            ded_fix += line.amount
                slip_line_pool.copy(cr, uid, line.id, {'slip_id':slip.id, 'employee_id':False, 'function_id':False}, {})

            for line in emp.line_ids:
                if line.category_id.code in ad:
                    continue
                ad.append(line.category_id.code)
                
                if sal_type == 'net':
                    if line.amount_type == 'per':
                        exp = line.category_id.base
                        try:
                            amt = eval(exp, obj)
                        except Exception, e:
                            raise osv.except_osv(_('Variable Error !'), _('Variable Error : %s ' % (e)))
                        if amt <= 0:
                            amt =line.amount
                        else:
                            amt =  line.amount + (amt * line.amount)
                        if line.type == 'allounce':
                            all_per += amt
                        elif line.type == 'deduction':
                            ded_per += amt
                    elif line.amount_type == 'fix':
                        if line.type == 'allounce':
                            all_fix += line.amount
                        elif line.type == 'deduction':
                            ded_fix += line.amount
                slip_line_pool.copy(cr, uid, line.id, {'slip_id':slip.id, 'employee_id':False, 'function_id':False}, {})

            if sal_type == 'net':
                sal = contract.wage
                sal += ded_fix
                sal -= all_fix
                per = (all_per - ded_per)
                if per <=0 :
                    per *= -1
                final = (per * 100) + 100
                basic = (sal * 100) / final
            else:
                basic = contract.wage

            basic_before_leaves = basic

            #Check for the Holidays
            def get_days(start, end, month, year, calc_day):
                count = 0
                for day in range(start, end):
                    if date(year, month, day).weekday() == calc_day:
                        count += 1
                return count
            
            dates = prev_bounds(slip.date)
            sql = '''select id from hr_holidays
                        where date_from >= '%s' and date_to <= '%s' 
                        and employee_id = %s 
                        and state = 'validate' ''' % (dates[0], dates[1], slip.employee_id.id)
            cr.execute(sql)
            res = cr.fetchall()
            
            working_day = 0
            saturday = get_days(1, dates[1].day, dates[1].month, dates[1].year, 5)
            sunday = get_days(1, dates[1].day, dates[1].month, dates[1].year, 6)
            total_off = saturday + sunday
            working_day = dates[1].day - total_off
            perday = basic / working_day
            total = 0.0
            leave = 0.0
            if res:
                holi_ids = [x[0] for x in res]
                total_leave = 0.0
                paid_leave = 0.0
                for hday in holiday_pool.browse(cr, uid, holi_ids):
                    res = {
                        'slip_id':slip.id,
                        'name':hday.holiday_status.name + '-%s' % (hday.number_of_days),
                        'code':hday.holiday_status.code,
                        'amount_type':'fix',
                        'category_id':hday.holiday_status.head_id.id,
                        'account_id':hday.holiday_status.account_id.id,
                        'analytic_account_id':hday.holiday_status.analytic_account_id.id
                    }
                    total_leave += hday.number_of_days
                    if hday.holiday_status.type == 'paid':
                        paid_leave += hday.number_of_days
                        continue
                    elif hday.holiday_status.type == 'halfpaid':
                        paid_leave += (hday.number_of_days / 2)
                        res['name'] = hday.holiday_status.name + '-%s/2' % (hday.number_of_days)
                        res['amount'] = perday * (hday.number_of_days/2)
                        total += perday * (hday.number_of_days/2)
                        leave += hday.number_of_days / 2
                        res['type'] = 'leaves'
                    else:
                        res['name'] = hday.holiday_status.name + '-%s' % (hday.number_of_days)
                        res['amount'] = perday * hday.number_of_days
                        res['type'] = 'leaves'
                        leave += hday.number_of_days
                        total += perday * hday.number_of_days
                    
                    slip_line_pool.create(cr, uid, res)
                basic = basic - total
                leaves = total
            
            number = self.pool.get('ir.sequence').get(cr, uid, 'salary.slip')
            ttyme = datetime.fromtimestamp(time.mktime(time.strptime(slip.date,"%Y-%m-%d")))

            updt = {
                'deg_id':function,
                'number':number, 
                'basic':basic,
                'basic_before_leaves':basic_before_leaves,
                'name':'Salary Slip of %s for %s' % (emp.name, ttyme.strftime('%B-%Y')), 
                'state':'draft',
                'leaves':total,
                'holiday_days':leave,
                'worked_days':working_day - leave,
                'working_days':working_day
            }
            self.write(cr, uid, [slip.id], updt)
            
        return True
        
hr_payslip()

class hr_payslip_line(osv.osv):
    '''
    Payslip Line
    '''
    _name = 'hr.payslip.line'
    _description = 'Payslip Line'
    
#    def _calculate(self, cr, uid, ids, field_names, arg, context):
#        res = {}
#        amount = 0
#        obj = {'basic':0.0}
#        
#        for line in self.browse(cr, uid, ids, context):
#            obj['basic'] = line.slip_id.basic
#            obj[line.category_id.code.lower()] = line.amount
#            print 'XXXXXXXXXXXXXXXXXXXXXXXXXX : ', obj
#            if line.amount_type == 'per':
#                amount = line.amount * eval(line.category_id.base, obj)
#            elif line.amount_type == 'fix':
#                amount = line.amount

#            res[line.id] = amount
#        
#        return res

    def onchange_category(self, cr, uid, ids, category_id):
        seq = 0
        if category_id:
            seq = self.pool.get('hr.allounce.deduction.categoty').browse(cr, uid, category_id).sequence
            
        return {'value':{'sequence':seq}}

    _columns = {
        'slip_id':fields.many2one('hr.payslip', 'Pay Slip', required=False),
        'function_id':fields.many2one('hr.employee.grade', 'Function', required=False),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=False),
        'name':fields.char('Name', size=256, required=True, readonly=False),
        'code':fields.char('Code', size=64, required=False, readonly=False),
        'type':fields.selection([
            ('allounce','Allowance'),
            ('deduction','Deduction'),
            ('leaves','Leaves'),
            ('advance','Advance'),
            ('loan','Loan'),
            ('installment','Loan Installment'),
            ('otherpay','Other Payment'),
            ('otherdeduct','Other Deduction'),
        ],'Type', select=True, required=True),
        'category_id':fields.many2one('hr.allounce.deduction.categoty', 'Category', required=True),
        'amount_type':fields.selection([
            ('per','Percentage (%)'),
            ('fix','Fixed Amount'),
        ],'Amount Type', select=True),
        'amount': fields.float('Amount / Percentage', digits=(16, int(config['price_accuracy']))),
        'analytic_account_id':fields.many2one('account.analytic.account', 'Analytic Account', required=False),
        'account_id':fields.many2one('account.account', 'General Account', required=True),
        'total': fields.float('Sub Total', digits=(16, int(config['price_accuracy']))),
        'expanse_id': fields.many2one('hr.expense.expense', 'Expense'),
        'sequence': fields.integer('Sequence'),
    }
    _order = 'sequence'
hr_payslip_line()

class hr_employee(osv.osv):
    '''
    Employee
    '''
    _inherit = 'hr.employee'
    _description = 'Employee'
    
    _columns = {
        'pan_no':fields.char('PAN No', size=64, required=False, readonly=False),
        'esp_account':fields.char('EPS Account', size=64, required=False, readonly=False),
        'pf_account':fields.char('PF Account', size=64, required=False, readonly=False),
        'pg_joining': fields.date('PF Join Date'),
        'esi_account':fields.char('ESI Account', size=64, required=False, readonly=False),
        'hospital_id':fields.many2one('res.partner.address', 'ESI Hospital', required=False),
        'passport_id':fields.many2one('hr.passport', 'Passport', required=False),
        'otherid':fields.char('Bank Account', size=64, required=False),
        'line_ids':fields.one2many('hr.payslip.line', 'employee_id', 'Salary Structure', required=False),
        'slip_ids':fields.one2many('hr.payslip', 'employee_id', 'Payslips', required=False, readonly=True),
        'property_bank_account': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Bank Account",
            method=True,
            view_load=True,
            help="Select Bank Account from where Salary Expanse will be Paid",
            required=True),
        'salary_account':fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Salary Account",
            method=True,
            view_load=True,
            help="Expanse account when Salary Expanse will be recorded",
            required=True),
        'employee_account':fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Employee Account",
            method=True,
            view_load=True,
            help="Employee Payable Account",
            required=True),
        'analytic_account':fields.property(
            'account.analytic.account',
            type='many2one',
            relation='account.analytic.account',
            string="Analytic Account",
            method=True,
            view_load=True,
            help="Analytic Account for Salary Analysis",
            required=False),
    }
hr_employee()

