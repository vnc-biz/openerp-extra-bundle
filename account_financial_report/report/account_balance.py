# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

import xml
import copy
from operator import itemgetter
import time
import datetime
from report import report_sxw
from tools import config


class account_balance(report_sxw.rml_parse):
    _name = 'report.account.account.balance'

    def set_context(self, objects, data, ids, report_type = None):
        self.get_context_date_period(data['form'])
        super(account_balance, self).set_context(objects, data, ids, report_type)


    def __init__(self, cr, uid, name, context):
        super(account_balance, self).__init__(cr, uid, name, context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.sum_balance = 0.00
        self.sum_debit_fy = 0.00
        self.sum_credit_fy = 0.00
        self.sum_balance_fy = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.ctx = {}      # Context for given date or period
        self.ctxfy = {}    # Context from the date start or first period of the fiscal year
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sum_debit': self._sum_debit,
            'sum_credit': self._sum_credit,
            'sum_balance': self._sum_balance,
            'sum_balanceinit': self._sum_balanceinit,
            'sum_debit_fy': self._sum_debit_fy,
            'sum_credit_fy': self._sum_credit_fy,
            'sum_balance_fy': self._sum_balance_fy,
            'sum_balanceinit_fy': self._sum_balanceinit_fy,
            'get_fiscalyear':self.get_fiscalyear,
            'get_periods':self.get_periods,
        })
        self.context = context


    def get_fiscalyear(self, form):
        res=[]
        if form.has_key('fiscalyear'):
            fisc_id = form['fiscalyear']
            if not (fisc_id):
                return ''
            self.cr.execute("SELECT name FROM account_fiscalyear WHERE id = %s" , (int(fisc_id),))
            res=self.cr.fetchone()
        return res and res[0] or ''


    def get_periods(self, form):
        result=''
        if form.has_key('periods') and form['periods'][0][2]:
            period_ids = ",".join([str(x) for x in form['periods'][0][2] if x])
            self.cr.execute("SELECT name FROM account_period WHERE id in (%s)" % (period_ids))
            res = self.cr.fetchall()
            len_res = len(res) 
            for r in res:
                if (r == res[len_res-1]):
                    result+=r[0]+". "
                else:
                    result+=r[0]+", "
        elif form.has_key('date_from') and form.has_key('date_to'):
            result = self.formatLang(form['date_from'], date=True) + ' - ' + self.formatLang(form['date_to'], date=True) + ' '
        else:
            fy_obj = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,form['fiscalyear'])
            res = fy_obj.period_ids
            len_res = len(res)
            for r in res:
                if r == res[len_res-1]:
                    result+=r.name+". "
                else:
                    result+=r.name+", "
            
        return str(result and result[:-1]) or ''


    def get_context_date_period(self, form):
        # ctx: Context for the given date or period
        ctx = self.context.copy()
        ctx['state'] = form['context'].get('state','all')
        if 'fiscalyear' in form and form['fiscalyear']:
            ctx['fiscalyear'] = form['fiscalyear']
        if form['state'] in ['byperiod', 'all']:
            ctx['periods'] = form['periods'][0][2]
        if form['state'] in ['bydate', 'all']:
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = form['date_to']
        if 'periods' not in ctx:
            ctx['periods'] = []
        self.ctx = ctx

        # ctxfy: Context from the date start / first period of the fiscal year
        ctxfy = ctx.copy()
        ctxfy['periods'] = ctx['periods'][:]

        if form['state'] in ['byperiod', 'all'] and len(ctx['periods']):
            self.cr.execute("""SELECT id, date_start, fiscalyear_id
                FROM account_period
                WHERE date_start = (SELECT min(date_start) FROM account_period WHERE id in (%s))"""
                % (','.join([str(x) for x in ctx['periods']])))
            res = self.cr.dictfetchone()
            self.cr.execute("""SELECT id
                FROM account_period
                WHERE fiscalyear_id in (%s) AND special=FALSE AND date_start < '%s'"""
                % (res['fiscalyear_id'], res['date_start']))
            ids = filter(None, map(lambda x:x[0], self.cr.fetchall()))
            ctxfy['periods'].extend(ids)

        if form['state'] in ['bydate', 'all']:
            self.cr.execute("""SELECT date_start
                FROM account_fiscalyear
                WHERE '%s' BETWEEN date_start AND date_stop""" % (ctx['date_from']))
            res = self.cr.dictfetchone()
            ctxfy['date_from'] = res['date_start']

        if form['state'] == 'none' or (form['state'] == 'byperiod' and not len(ctx['periods'])):
            if 'fiscalyear' in form and form['fiscalyear']:
                sql = """SELECT id, date_start
                    FROM account_period
                    WHERE fiscalyear_id in (%s) AND special=FALSE
                    ORDER BY date_start""" % (ctx['fiscalyear'])
            else:
                sql = """SELECT id, date_start
                    FROM account_period
                    WHERE fiscalyear_id in (SELECT id FROM account_fiscalyear WHERE state='draft') AND special=FALSE
                    ORDER BY date_start"""
            self.cr.execute(sql)
            res = self.cr.dictfetchall()
            ids = filter(None, map(lambda x:x['id'], res))
            ctxfy['periods'] = ids
        self.ctxfy = ctxfy
#        print "ctx=", self.ctx
#        print "ctxfy=", self.ctxfy



    def lines(self, form, ids={}, done=None, level=1):
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done={}
        if form.has_key('Account_list') and form['Account_list']:
            ids = form['Account_list'][0][2]
            del form['Account_list']
        res={}
        result_acc=[]
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')

        ctx_allfy = self.context.copy()
        ctx_allfy['fiscalyear'] = form['fiscalyear']
        ctx_allfy['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',form['fiscalyear'])])

        ctx_allfy_nospecial = self.context.copy()
        ctx_allfy_nospecial['fiscalyear'] = form['fiscalyear']
        ctx_allfy_nospecial['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',form['fiscalyear']),('special','=',False)])

#            accounts = account_obj.browse(self.cr, self.uid, ids, self.ctx)
#            def cmp_code(x, y):
#                return cmp(x.code, y.code)
#            accounts.sort(cmp_code)
        child_ids = account_obj._get_children_and_consol(self.cr, self.uid, ids, self.ctx)
        if child_ids:
            ids = child_ids
        # Amounts in period or date
        accounts = account_obj.read(self.cr, self.uid, ids, ['type','code','name','debit','credit','balance','parent_id'], self.ctx)
        # Amounts from the date start / first period of the fiscal year
        balance_fy = {}
        for acc in account_obj.read(self.cr, self.uid, ids, ['balance'], self.ctxfy):
            balance_fy[acc['id']] = acc['balance']
        # Amounts in all fiscal year
        balance_allfy = {}
        for acc in account_obj.read(self.cr, self.uid, ids, ['balance'], ctx_allfy):
            balance_allfy[acc['id']] = acc['balance']
        # Amounts in all fiscal year without special periods
        debit_allfy_nos = {}
        credit_allfy_nos = {}
        for acc in account_obj.read(self.cr, self.uid, ids, ['debit','credit'], ctx_allfy_nospecial):
            debit_allfy_nos[acc['id']] = acc['debit']
            credit_allfy_nos[acc['id']] = acc['credit']

        for account in accounts:
            account_id = account['id']
            if account_id in done:
                continue
            done[account_id] = 1
            res = {
                    'id' : account_id,
                    'type' : account['type'],
                    'code': account['code'],
                    'name': account['name'],
                    'level': level,
                    'debit': account['debit'],
                    'credit': account['credit'],
                    'balance': balance_fy[account_id],
                    'balanceinit': round(balance_fy[account_id]-account['debit']+account['credit'], int(config['price_accuracy'])),
                    'debit_fy': debit_allfy_nos[account_id],
                    'credit_fy': credit_allfy_nos[account_id],
                    'balance_fy': balance_allfy[account_id],
                    'balanceinit_fy': round(balance_allfy[account_id]-debit_allfy_nos[account_id]+credit_allfy_nos[account_id], int(config['price_accuracy'])),
                   # 'leef': not bool(account['child_id']),
                    'parent_id':account['parent_id'],
                    'bal_type':'',
                }
            if abs(res['balanceinit']) < 10**-int(config['price_accuracy']):
                res['balanceinit'] = 0
            if abs(res['balanceinit_fy']) < 10**-int(config['price_accuracy']):
                res['balanceinit_fy'] = 0
            self.sum_debit += account['debit']
            self.sum_credit += account['credit']
            self.sum_balance += balance_fy[account_id]
            self.sum_debit_fy += debit_allfy_nos[account_id]
            self.sum_credit_fy += credit_allfy_nos[account_id]
            self.sum_balance_fy += balance_allfy[account_id]
#                if account.child_id:
#                    def _check_rec(account):
#                        if not account.child_id:
#                            return bool(account.credit or account.debit)
#                        for c in account.child_id:
#                            if not _check_rec(c) or _check_rec(c):
#                                return True
#                        return False
#                    if not _check_rec(account) :
#                        continue
            if account['parent_id']:
#                    acc = account_obj.read(self.cr, self.uid, [ account['parent_id'][0] ] ,['name'], self.ctx)
                for r in result_acc:
                    if r['id'] == account['parent_id'][0]:
                        res['level'] = r['level'] + 1
                        break
            if form['display_account'] == 'bal_mouvement':
                if res['credit'] > 0 or res['debit'] > 0 or res['balance'] > 0 :
                    result_acc.append(res)
            elif form['display_account'] == 'bal_solde':
                if  res['balance'] != 0:
                    result_acc.append(res)
            else:
                result_acc.append(res)
#                if account.child_id:
#                    acc_id = [acc.id for acc in account.child_id]
#                    lst_string = ''
#                    lst_string = '\'' + '\',\''.join(map(str,acc_id)) + '\''
#                    self.cr.execute("select code,id from account_account where id IN (%s)"%(lst_string))
#                    a_id = self.cr.fetchall()
#                    a_id.sort()
#                    ids2 = [x[1] for x in a_id]
#
#                    result_acc += self.lines(form, ids2, done, level+1)
        self.sum_balanceinit = round(self.sum_balance - self.sum_debit + self.sum_credit, int(config['price_accuracy']))
        self.sum_balanceinit_fy = round(self.sum_balance_fy - self.sum_debit_fy + self.sum_credit_fy, int(config['price_accuracy']))
        return result_acc
    
    def _sum_credit(self):
        return self.sum_credit

    def _sum_debit(self):
        return self.sum_debit

    def _sum_balance(self):
        return self.sum_balance

    def _sum_balanceinit(self):
        return self.sum_balanceinit
    
    def _sum_credit_fy(self):
        return self.sum_credit_fy

    def _sum_debit_fy(self):
        return self.sum_debit_fy

    def _sum_balance_fy(self):
        return self.sum_balance_fy

    def _sum_balanceinit_fy(self):
        return self.sum_balanceinit_fy

report_sxw.report_sxw('report.account.balance.full', 'account.account', 'addons/account_financial_report/report/account_balance_full.rml', parser=account_balance, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
