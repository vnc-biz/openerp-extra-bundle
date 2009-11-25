# -*- coding: utf-8 -*-
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

import time
import tools
import wizard
import os
import mx.DateTime
import base64
import pooler
import vobject

# COMMENTED FIELDS NEED ATTENTION FOR IMPLEMENTATION
ICS_TAGS = {
        'CREATED' : 'datetime', 
        'DTSTART' : 'datetime', 
        'LAST-MODIFIED' : 'datetime', 
#        'PRIORITY' : 'integer',
        'SEQ' : 'integer', 
        'LOCATION' : 'object:res.partner.address', 
        'ATTACH' : 'object:ir.attachment', 
        'ATTENDEE' : 'object:res.partner', 
        'CATEGORIES' : 'object:crm.case.categ', 
#        'comment' : '',
#        'CONTACT' : 'user_id.address_id',
#        'exdate' : 'Needs new field for defining exceptional dates',
##        'exrule' : '',
#        'rstatus' : '',
#        'related' : '',
#        'resources' : '',
#        'rdate' : '',
#        'rrule' : 'Needs a new object or a wizard to get rule data',
#        'x-prop' : '-',
        'DURATION' : 'integer', 
        'DTEND' : 'datetime', 
            }

ICS_MAPPING = {
#        'CREATED' : 'create_date',
        'DESCRIPTION' : 'name', 
        'DTSTART' : 'date', 
#        'GEO' : '',
#        'LAST-MODIFIED' : 'write_date',
        'LOCATION' : 'partner_address_id', 
        'ORGANIZER' : 'user_id', 
        'PRIORITY' : 'priority', 
#        'DTSTAMP' : '-',
        'SEQ' : 'id', 
#        'status' : 'state/ map state to values',
        'SUMMARY' : 'desription', 
#        'transp' : '-',
#        'uid' : 'Random-text',
#        'url' : '',
#        'recurid' : '',
        'ATTACH' : '', 
        'ATTENDEE' : 'partner_id+partner email', 
        'CATEGORIES' : 'categ_id', 
#        'comment' : '',
        'CONTACT' : 'user_id.address_id', 
#        'exdate' : 'Needs new field for defining exceptional dates',
##        'exrule' : '',
#        'rstatus' : '',
#        'related' : '',
#        'resources' : '',
#        'rdate' : '',
#        'rrule' : 'Needs a new object or a wizard to get rule data',
#        'x-prop' : '-',
        'DURATION' : 'duration', 
        'DTEND' : 'date_closed', 
            }

class crm_cal_import_wizard(wizard.interface):
    form1 = '''<?xml version="1.0"?>
    <form string="Import ICS">
        <separator string="Select ICS file"/>
        <field name="file_path" colspan="4" width="300" nolabel="1"/>
    </form>'''
    
    form1_fields = {
            'file_path': {
                'string': 'Select ICS file', 
                'type': 'binary', 
                'required' : True, 
                'filters' : '*.ics'
                }
            }
    
    def _process_import_ics(self, cr, uid, data, context=None):
#        print 'WWWWWWWWWWWWWWWWWWWWWWWWWWW'
        case_obj = pooler.get_pool(cr.dbname).get('crm.case')
        case_obj.import_cal(cr, uid, data['ids'], data, context)
#        parsedCal = vobject.readOne(file_content)
#        for child in parsedCal.getChildren():
#            if not child.name == 'VEVENT':
#                continue
#            result = {}
#            for event in child.getChildren():
#                if event.name in ICS_MAPPING:
#                    if ICS_TAGS.get(event.name, False) and ICS_TAGS.get(event.name) == 'datetime':
#                        result[ICS_MAPPING[event.name]] = event.value.strftime('%Y-%m-%d %H:%M:%S')
#                    elif ICS_TAGS.get(event.name, False) and ICS_TAGS.get(event.name) == 'integer':
#                        result[ICS_MAPPING[event.name]] = int(event.value)
#                    elif ICS_TAGS.get(event.name, False) and ICS_TAGS.get(event.name).startswith('object'):
#                        val = ICS_TAGS.get(event.name)
#                        #TODO: Need to map with related object
#                    else:
#                        result[ICS_MAPPING[event.name]] = event.value
#        case_obj = pooler.get_pool(cr.dbname).get('crm.case')
#        section_id = pooler.get_pool(cr.dbname).get('crm.case.section').search(cr, uid, [('name','like','Meet%')])[0]
#        result.update({'section_id' : section_id})
#        new_id = case_obj.create(cr, uid, result)
        return {}
    
    states = {
        'init': {
            'actions': [], 
            'result': {'type': 'form', 'arch':form1, 'fields':form1_fields, 'state': [('end', '_Cancel', 'gtk-cancel'), ('open', '_Import', 'gtk-ok')]}
        }, 
        'open': {
            'actions': [], 
            'result': {'type': 'action', 'action':_process_import_ics, 'state':'end'}
        }
    }
    
crm_cal_import_wizard('caldav.crm.import')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: