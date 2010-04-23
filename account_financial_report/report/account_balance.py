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
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
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



    def lines(self, form, ids={}, done=None, level=0):
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """
        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done = {}
        if form.has_key('account_list') and form['account_list']:
            account_ids = form['account_list'][0][2]
            del form['account_list']
        res = {}
        result_acc = []
        accounts_levels = {}
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')

        child_ids = account_obj._get_children_and_consol(self.cr, self.uid, account_ids, self.context)
        if child_ids:
            account_ids = child_ids
        
        #
        # Amounts in all fiscal year (end of year balance)
        #
        ctx_allfy = self.context.copy()
        ctx_allfy['fiscalyear'] = form['fiscalyear']
        ctx_allfy['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',form['fiscalyear'])])

        balance_allfy = {}
        for acc in account_obj.read(self.cr, self.uid, account_ids, ['balance'], ctx_allfy):
            balance_allfy[acc['id']] = acc['balance']
        #
        # Amounts in all fiscal year without special periods 
        # (fiscal year debit/credit)
        #
        ctx_allfy_nospecial = self.context.copy()
        ctx_allfy_nospecial['fiscalyear'] = form['fiscalyear']
        ctx_allfy_nospecial['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',form['fiscalyear']),('special','=',False)])

        debit_allfy_nos = {}
        credit_allfy_nos = {}
        balance_allfy_nos = {}
        for acc in account_obj.read(self.cr, self.uid, account_ids, ['debit','credit','balance'], ctx_allfy_nospecial):
            debit_allfy_nos[acc['id']] = acc['debit']
            credit_allfy_nos[acc['id']] = acc['credit']
            balance_allfy_nos[acc['id']] = acc['balance']
        #
        # Amounts in selected period / dates
        #
        ctx_selected = self.context.copy()
        ctx_selected['state'] = form['context'].get('state','all')
        if 'fiscalyear' in form and form['fiscalyear']:
            ctx_selected['fiscalyear'] = form['fiscalyear']
        if form['state'] in ['byperiod', 'all']:
            ctx_selected['periods'] = form['periods'][0][2]
        if form['state'] in ['bydate', 'all']:
            ctx_selected['date_from'] = form['date_from']
            ctx_selected['date_to'] = form['date_to']
        if 'periods' not in ctx_selected:
            ctx_selected['periods'] = []

        for account in account_obj.read(self.cr, self.uid, account_ids, ['type','code','name','debit','credit','balance','parent_id'], ctx_selected):
            account_id = account['id']
            if account_id in done:
                continue

            done[account_id] = 1

            #
            # Calculate the account level
            #
            parent_id = account['parent_id']
            if parent_id:
                if isinstance(parent_id, tuple):
                    parent_id = parent_id[0]
                account_level = accounts_levels.get(parent_id, 0) + 1
            else:
                account_level = level
            accounts_levels[account_id] = account_level

            #
            # Check if we need to include this level
            #
            if not form['display_account_level'] or account_level <= form['display_account_level']:
                #
                # Copy the account values
                #
                res = {
                        'id' : account_id,
                        'type' : account['type'],
                        'code': account['code'],
                        'name': account['name'],
                        'level': account_level,
                        'debit': account['debit'],
                        'credit': account['credit'],
                        'balance': account['balance'],
                        'balanceinit': account['balance']-account['debit']+account['credit'],
                        'debit_fy': debit_allfy_nos[account_id],
                        'credit_fy': credit_allfy_nos[account_id],
                        'balance_fy': balance_allfy_nos[account_id],
                        'balanceinit_fy': balance_allfy_nos[account_id]-debit_allfy_nos[account_id]+credit_allfy_nos[account_id],
                        'parent_id': account['parent_id'],
                        'bal_type': '',
                    }

                #
                # Round the values to zero if needed (-0.000001 ~= 0)
                #
                if abs(res['balance']) < 10**-int(config['price_accuracy']):
                    res['balance'] = 0.0
                if abs(res['balance_fy']) < 10**-int(config['price_accuracy']):
                    res['balance_fy'] = 0.0
                if abs(res['balanceinit']) < 10**-int(config['price_accuracy']):
                    res['balanceinit'] = 0.0
                if abs(res['balanceinit_fy']) < 10**-int(config['price_accuracy']):
                    res['balanceinit_fy'] = 0.0

                #
                # Check whether we must include this line in the report or not
                #
                if form['display_account'] == 'bal_mouvement' and account['parent_id']:
                    # Include accounts with movements
                    if res['credit'] > 0 or res['debit'] > 0 or res['balance'] > 0 :
                        result_acc.append(res)
                elif form['display_account'] == 'bal_solde' and account['parent_id']:
                    # Include accounts with balance
                    if  res['balance'] != 0:
                        result_acc.append(res)
                else:
                    # Include all accounts
                    result_acc.append(res)

        return result_acc

report_sxw.report_sxw('report.account.balance.full', 'account.account', 'addons/account_financial_report/report/account_balance_full.rml', parser=account_balance, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
