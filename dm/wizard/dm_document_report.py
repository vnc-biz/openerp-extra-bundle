# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import wizard
import pooler


class wizard_document_report(wizard.interface):

    report_list_form1 = '''<?xml version="1.0"?>
    <form string="Select Report">
        <field name="report" colspan="4"/>
        <field name="address_id" colspan="4" />
    </form>'''

    report_list_form2 = '''<?xml version="1.0"?>
    <form string="Select Report">
        <field name="segment_id" colspan="4"/>
    </form>'''

    def execute(self, db, uid, data, state='init', context=None):
        self.dm_wiz_data = data
        return super(wizard_document_report, self).execute( db, uid, data, state, context)

    def _print_report(self, cr, uid, data, context):
        report = pooler.get_pool(cr.dbname).get('ir.actions.report.xml').browse(cr, uid, data['form']['report'])
        self.states['print_report']['result']['report'] = report.report_name
        return {}

    def _send_report(self, cr, uid, data, context):
        doc = pooler.get_pool(cr.dbname).get('dm.offer.document').browse(cr, uid, self.dm_wiz_data['id'])
        vals = {
            'address_id': data['form']['address_id'],
            'segment_id': data['form']['segment_id'],
            'step_id': doc.step_id.id,
            'is_preview': True,
        }
        pooler.get_pool(cr.dbname).get('dm.workitem').create(cr, uid, vals)
        return {}

    def _get_reports(self, cr, uid, context):
        document_id = self.dm_wiz_data['id']
        pool = pooler.get_pool(cr.dbname)
        group_obj = pool.get('ir.actions.report.xml')
        ids = group_obj.search(cr, uid, [('document_id', '=', document_id)])
        res = [(group.id, group.name) for group in
                                            group_obj.browse(cr, uid, ids)]
        res.sort(lambda x, y: cmp(x[1], y[1]))
        return res

    def _set_segment(self, cr, uid, data, context):
        address = data['form']['address_id']

        domain = []
        if address:
            pool = pooler.get_pool(cr.dbname)
            wi_obj = pool.get('dm.workitem')
            workitem_ids = wi_obj.search(cr, uid, [('address_id', '=', address)])
            segment_ids = list(set([wi.segment_id.id for wi in wi_obj.browse(cr, uid, workitem_ids) if wi.segment_id.id]))
            domain = [('id', 'in', tuple(segment_ids))]

        self.states['init2']['result']['fields']['segment_id']['domain'] = domain

        return {}

    report_list_fields1 = {
        'report': {
            'string': 'Select Report',
            'type': 'selection',
            'selection': _get_reports,
        },
        'address_id': {
            'string': 'Select Customer Address',
            'type': 'many2one',
            'relation': 'res.partner.address',
            'selection': _get_reports,
            'domain': [('partner_id.category_id', '=', 'DTP Preview Customers')],
        },
    }

    report_list_fields2 = {
        'segment_id': {
            'string': 'Select Segment',
            'type': 'many2one',
            'relation': 'dm.campaign.proposition.segment',
        }
    }

    report_send_fields = {
        'mail_service_id': {
            'string': 'Select Mail Service',
            'type': 'many2one',
            'relation': 'dm.mail_service',
        },
    }

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': report_list_form1,
                'fields': report_list_fields1,
                'state': [('end', 'Cancel'),
                          ('init2', 'Select Segment'),],
            }
        },
        'init2': {
            'actions': [_set_segment],
            'result': {
                'type': 'form',
                'arch': report_list_form2,
                'fields': report_list_fields2,
                'state': [('end', 'Cancel'),
                          ('print_report', 'Print Report'),
                          ('send_report', 'Send Report'),],
            }
        },
        'print_report': {
            'actions': [_print_report],
            'result': {
                'type': 'print',
                'report': '',
                'state': 'end',
            }
        },
        'send_report': {
            'actions': [_send_report],
            'result': {
                'type': 'state',
                'state': 'end'
            }
        },
    }

wizard_document_report("wizard_document_report")

