# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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

import time

from report import report_sxw

class module_test_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        print  "module_test_report"
        super(module_test_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_state_msg' : self.get_state_msg,
            'get_check_certi': self.get_check_certi,
        })

    def get_state_msg(self, state, cert_no):
        x = ''
        if state=='done':
            x = '''Congratulations, your module has succesfully succedded our quality tests. Find here the  certificate number of this module: %s

Please note it carefully, we strongly recommend you to even to integrate it into the __terp__.py file of your module  because it may be asked for any help on migration process. \n\n'''%cert_no
        elif state=='failed':
            x = '''Unfortunately, your module didn't succeed our quality tests. Please find below the reasons of this failure. \n\n'''
        return x

    def get_check_certi(self, tech_cert, func_cert):
        x = ''
        if not tech_cert:
            x += '''Please note that, as requested from your side, the certificaiton process was only based on the functional quality tests. Tiny sprl disclaims any liability for failure resulting from a technical bug and for maintenance matters.\n\n'''
        if not func_cert:
            x += '''Please note that, as requested from your side, the certificaiton process was only based on the technical quality tests. Tiny sprl disclaims any liability for failure resulting from a functional bug or error analysis.'''
        return x

report_sxw.report_sxw('report.maintenance.module.test','maintenance.maintenance.module','addons/maintenance_editor/report/module_test.rml',parser=module_test_report,header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: