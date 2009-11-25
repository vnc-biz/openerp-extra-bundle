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

from osv import fields, osv
from time import strftime
import time
import base64
import vobject
from dateutil.rrule import *
from dateutil import parser
from datetime import datetime
from time import strftime

# O-1	Optional and can come only once
# O-n	Optional and can come more than once
# R-1	Required and can come only once
# R-n	Required and can come more than once

class CalDAV(object):
    __attribute__= {
    }

    def ical_items(self):
        return self.__attribute__.items()

    def ical_set(self, name, value, type):
        if name in self.__attribute__ and self.__attribute__[name]:
           self.__attribute__[name][type] = value
        return True

    def ical_get(self, name, type):
        if self.__attribute__.get(name):
            val = self.__attribute__.get(name).get(type, None)
            valtype =  self.__attribute__.get(name).get('type', None)
            if type == 'value':
                if valtype and valtype=='datetime' and val:
                     val = val.strftime('%Y-%m-%d %H:%M:%S')
                if valtype and valtype=='integer' and val:
                     val = int(val)
            return  val
        else:
             return  self.__attribute__.get(name, None)

    def export_ical(self):
        pass

    def import_ical(self, cr, uid, ical_data):
        parsedCal = vobject.readOne(ical_data)
        for child in parsedCal.getChildren():
            for cal_data in child.getChildren():
                if cal_data.name.lower() == 'attendee':
                    attendee = Attendee()
                    attendee.import_ical(cr, uid, cal_data)
                if cal_data.name.lower() in self.__attribute__:
                    self.ical_set(cal_data.name.lower(), cal_data.value, 'value')
        return True

class Calendar(CalDAV):
    __attribute__ = {
        'prodid' : None, # Use: R-1, Type: TEXT, Specifies the identifier for the product that created the iCalendar object.
        'version' : None, # Use: R-1, Type: TEXT, Specifies the identifier corresponding to the highest version number
                           #             or the minimum and maximum range of the iCalendar specification
                           #             that is required in order to interpret the iCalendar object.
        'calscale' : None, # Use: O-1, Type: TEXT, Defines the calendar scale used for the calendar information specified in the iCalendar object.
        'method' : None, # Use: O-1, Type: TEXT, Defines the iCalendar object method associated with the calendar object.
        'vevent'  : None, # Use: O-n, Type: Collection of Event class
        'vtodo'   : None, # Use: O-n, Type: Collection of ToDo class
        'vjournal': None, # Use: O-n, Type: Collection of Journal class
        'vfreebusy': None, # Use: O-n, Type: Collection of FreeBusy class
        'vtimezone': None, # Use: O-n, Type: Collection of Timezone class

    }

    def import_ical(self, cr, uid, ical_data):
        # Write openobject data from ical_data
        ical = vobject.readOne(ical_data)
        for child in ical.getChildren():
            child_name = child.name.lower()
            if child_name == 'vevent':
                for event in child.getChildren():
                    if event.name.lower() =="attendee":
                        attendee = Attendee()
                        attendee.import_ical(cr, uid, event)
                    if event.name.lower() =="valarm":
                        alarm = Alarm()
                        alarm.import_ical(cr, uid, event)
            elif child_name == "vtimezone":
                timezone = Timezone()
                timezone.import_ical(cr, uid, child)
        return True        

    def export_ical(self, cr, uid, ids):
        # Read openobject data in ical format
        ical = vobject.iCalendar()
        datas = self.browse(cr, uid, ids)

        vcal = ical.add('vcalendar')
        for name, value in self.ical_items():
            if not value:
                continue
            if name == 'vevent':
                for event in value:
                    vevent = event.ical_read()
                    vcal.add(vevent)
            elif name == 'vtodo':
                for todo in value:
                    vtodo = todo.ical_read()
                    vcal.add(vtodo)
            elif name == 'vjournal':
                for journal in value:
                    vjournal = journal.ical_read()
                    vcal.add(vjournal)
            elif name == 'vfreebusy':
                for freebusy in value:
                    vfreebusy = freebusy.ical_read()
                    vcal.add(vfreebusy)
            elif name == 'vtimezone':
                for timezone in value:
                    vtimezone = timezone.ical_read()
                    vcal.add(vtimezone)
            else:
                vcal.add(name).value = value
        s = ical.serialize()
        return s

    def ical_write(self, data):
        ical = vobject.readOne(data)
        for child in ical.getChildren():
            child_name = child.name.lower()
            child_value = child.value
            if child_name == 'vevent':
                vevents = []
                for event in child.getChildren():
                    vevent = Event()
                    vevent.ical_write(event.serialize())
                    vevents.append(vevent)
                self.ical_set(child_name, vevents)
            else:
                self.ical_set(child_name, child_value)
        return True

class Event(CalDAV):
    __attribute__ = {
        'class' : None, # Use: O-1, Type: TEXT,         Defines the access classification for a calendar  component like "PUBLIC" / "PRIVATE" / "CONFIDENTIAL"
        'created' : None, # Use: O-1, Type: DATE-TIME,    Specifies the date and time that the calendar information  was created by the calendar user agent in the calendar store.
        'description' : None, # Use: O-1, Type: TEXT,            Provides a more complete description of the calendar component, than that provided by the "SUMMARY" property.
        'dtstart' : None, # Use: O-1, Type: DATE-TIME,    Specifies when the calendar component begins.
        'geo' : None, # Use: O-1, Type: FLOAT,        Specifies information related to the global position for the activity specified by a calendar component.
        'last-mod' : None, # Use: O-1, Type: DATE-TIME        Specifies the date and time that the information associated with the calendar component was last revised in the calendar store.
        'location' : None, # Use: O-1, Type: TEXT            Defines the intended venue for the activity defined by a calendar component.
        'organizer' : None, # Use: O-1, Type: CAL-ADDRESS,  Defines the organizer for a calendar component.
        'priority' : None, # Use: O-1, Type: INTEGER,      Defines the relative priority for a calendar component.
        'dtstamp'  : None, # Use: O-1, Type: DATE-TIME,    Indicates the date/time that the instance of the iCalendar object was created.
        'seq' : None, # Use: O-1, Type: INTEGER,      Defines the revision sequence number of the calendar component within a sequence of revision.
        'status' : None, # Use: O-1, Type: TEXT,            Defines the overall status or confirmation for the calendar component.
        'summary' : None, # Use: O-1, Type: TEXT,            Defines a short summary or subject for the calendar component.
        'transp' : None, # Use: O-1, Type: TEXT,            Defines whether an event is transparent or not to busy time searches.
        'uid' : None, # Use: O-1, Type: TEXT,            Defines the persistent, globally unique identifier for the calendar component.
        'url' : None, # Use: O-1, Type: URL,          Defines a Uniform Resource Locator (URL) associated with the iCalendar object.
        'recurid' : None,
        'attach' : None, # Use: O-n, Type: BINARY,       Provides the capability to associate a document object with a calendar component.
        'attendee' : None, # Use: O-n, Type: CAL-ADDRESS,    Defines an "Attendee" within a calendar component.
        'categories' : None, # Use: O-n,    Type: TEXT,            Defines the categories for a calendar component.
        'comment' : None, # Use: O-n,    Type: TEXT,            Specifies non-processing information intended to provide a comment to the calendar user.
        'contact' : None, # Use: O-n,    Type: TEXT,         Used to represent contact information or alternately a  reference to contact information associated with the calendar component.
        'exdate'  : None, # Use: O-n,    Type: DATE-TIME,    Defines the list of date/time exceptions for a recurring calendar component.
        'exrule'  : None, # Use: O-n,    Type: RECUR,        Defines a rule or repeating pattern for an exception to a recurrence set.
        'rstatus' : None,
        'related' : None, # Use: O-n,                     Specify the relationship of the alarm trigger with respect to the start or end of the calendar component.
                                #                               like A trigger set 5 minutes after the end of the event or to-do.---> TRIGGER;RELATED=END:PT5M


        'resources' : None, # Use: O-n, Type: TEXT,            Defines the equipment or resources anticipated for an activity specified by a calendar entity like RESOURCES:EASEL,PROJECTOR,VCR, LANGUAGE=fr:1 raton-laveur
        'rdate' : None, # Use: O-n,    Type: DATE-TIME,    Defines the list of date/times for a recurrence set.
        'rrule' : None, # Use: O-n,    Type: RECUR,        Defines a rule or repeating pattern for recurring events, to-dos, or time zone definitions.
        'x-prop' : None,
        'duration' : None, # Use: O-1,    Type: DURATION,        Specifies a positive duration of time.
        'dtend' : None, # Use: O-1,    Type: DATE-TIME,    Specifies the date and time that a calendar component ends.
    }

    def get_recurrent_dates(self, rrulestring, startdate=None):
        todate = parser.parse
        if not startdate:
            startdate = datetime.now()
        else:
            startdate = todate(startdate)
        rset1 = rrulestr(rrulestring, dtstart=startdate, forceset=True)
        recurrent_dates = map(lambda x:x.strftime('%Y-%m-%d %H:%M:%S'), rset1._iter())
        return recurrent_dates

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        # put logic for recurrent event
        # example : 123-20091111170822
        pass

    def create(self, cr, uid, vals, context={}):
        # put logic for recurrent event
        # example : 123-20091111170822
        pass

    def write(self, cr, uid, ids, vals, context={}):
        # put logic for recurrent event
#        # example : 123-20091111170822
        pass

class ToDo(CalDAV):
    __attribute__ = {
    }

class Journal(CalDAV):
    __attribute__ = {
    }

class FreeBusy(CalDAV):
    __attribute__ = {    
    'contact' : None,       # Use: O-1, Type: Text,         Represent contact information or alternately a  reference to contact information associated with the calendar component.
    'dtstart' : None,       # Use: O-1, Type: DATE-TIME,    Specifies when the calendar component begins.
    'dtend' : None,         # Use: O-1, Type: DATE-TIME,    Specifies the date and time that a calendar component ends.
    'duration' : None,      # Use: O-1, Type: DURATION,     Specifies a positive duration of time.
    'dtstamp' : None,       # Use: O-1, Type: DATE-TIME,    Indicates the date/time that the instance of the iCalendar object was created.
    'organizer' : None,     # Use: O-1, Type: CAL-ADDRESS,  Defines the organizer for a calendar component.
    'uid' : None,           # Use: O-1, Type: Text,         Defines the persistent, globally unique identifier for the calendar component.
    'url' : None,           # Use: O-1, Type: URL,          Defines a Uniform Resource Locator (URL) associated with the iCalendar object.
    'attendee' : None,      # Use: O-n, Type: CAL-ADDRESS,  Defines an "Attendee" within a calendar component.
    'comment' : None,       # Use: O-n, Type: TEXT,         Specifies non-processing information intended to provide a comment to the calendar user.
    'freebusy' : None,      # Use: O-n, Type: PERIOD,       Defines one or more free or busy time intervals.
    'rstatus' : None,
    'X-prop' : None,
    }

class Timezone(CalDAV):
    __attribute__ = {
    'tzid' : None,          # Use: R-1, Type: Text,         Specifies the text value that uniquely identifies the "VTIMEZONE" calendar component.
    'last-mod' : None,      # Use: O-1, Type: DATE-TIME,    Specifies the date and time that the information associated with the calendar component was last revised in the calendar store.
    'tzurl' : None,         # Use: O-1, Type: URI,          Provides a means for a VTIMEZONE component to point to a network location that can be used to retrieve an up-to-date version of itself.
    'standardc' :           # Use: R-n,
        {'tzprop' : None,}, # Use: R-1,
    'daylightc' :           # Use: R-n, Type: Text,
        {'tzprop' : None,}, # Use: R-1,
    'x-prop' : None,        # Use: O-n, Type: Text,
    }
    def import_ical(self, cr, uid, ical_data):
        for val in ical_data.getChildren():
            if self.__attribute__.has_key(val.name.lower()):
                self.__attribute__[val.name] = val.value

class Alarm(CalDAV):
    __attribute__ = {
    
    'action' : None,    # Use: R-1, Type: Text,        defines the action to be invoked when an alarm is triggered LIKE "AUDIO" / "DISPLAY" / "EMAIL" / "PROCEDURE"
    'description' : None,    #      Type: Text,        Provides a more complete description of the calendar component, than that provided by the "SUMMARY" property. Use:- R-1 for DISPLAY,Use:- R-1 for EMAIL,Use:- R-1 for PROCEDURE
    'summary' : None,    # Use: R-1, Type: Text        Which contains the text to be used as the message subject. Use for EMAIL
    'attendee' : None,    # Use: R-n, Type: CAL-ADDRESS,    Contain the email address of attendees to receive the message. It can also include one or more. Use for EMAIL
    'trigger' : None,    # Use: R-1, Type: DURATION,    The "TRIGGER" property specifies a duration prior to the start of an event or a to-do. The "TRIGGER" edge may be explicitly set to be relative to the "START" or "END" of the event or to-do with the "RELATED" parameter of the "TRIGGER" property. The "TRIGGER" property value type can alternatively be set to an absolute calendar date and time of day value. Use for all action like AUDIO, DISPLAY, EMAIL and PROCEDURE
    'duration' : None,    #           Type: DURATION,    Duration' and 'repeat' are both optional, and MUST NOT occur more than once each, but if one occurs, so MUST the other. Use:- 0-1 for AUDIO, EMAIL and PROCEDURE, Use:- 0-n for DISPLAY
    'repeat' : None,    #           Type: INTEGER,    Duration' and 'repeat' are both optional, and MUST NOT occur more than once each, but if one occurs, so MUST the other. Use:- 0-1 for AUDIO, EMAIL and PROCEDURE, Use:- 0-n for DISPLAY
    'attach' : None,    # Use:- O-n : which MUST point to a sound resource, which is rendered when the alarm is triggered for AUDIO, Use:- O-n : which are intended to be sent as message attachments for EMAIL, Use:- R-1:which MUST point to a procedure resource, which is invoked when the alarm is triggered for PROCEDURE.
    'x-prop' : None,
    }
    
    def import_ical(self, cr, uid, ical_data):
        for val in ical_data.getChildren():
            if self.__attribute__.has_key(val.name.lower()):
                self.__attribute__[val.name] = val.value

class Attendee(CalDAV):
    __attribute__ = {
    'cutype' : None,    # Use: 0-1    Specify the type of calendar user specified by the property like "INDIVIDUAL"/"GROUP"/"RESOURCE"/"ROOM"/"UNKNOWN".
    'member' : None,    # Use: 0-1    Specify the group or list membership of the calendar user specified by the property.
    'role' : None,    # Use: 0-1    Specify the participation role for the calendar user specified by the property like "CHAIR"/"REQ-PARTICIPANT"/"OPT-PARTICIPANT"/"NON-PARTICIPANT"
    'partstat' : None, # Use: 0-1    Specify the participation status for the calendar user specified by the property. like use for VEVENT :- "NEEDS-ACTION"/"ACCEPTED"/"DECLINED"/"TENTATIVE"/"DELEGATED", use for VTODO :-"NEEDS-ACTION"/"ACCEPTED"/"DECLINED"/"TENTATIVE"/"DELEGATED"/"COMPLETED"/"IN-PROCESS" and use for VJOURNAL :- "NEEDS-ACTION"/"ACCEPTED"/"DECLINED".
    'rsvp' : None,    # Use: 0-1    Specify whether there is an expectation of a favor of a reply from the calendar user specified by the property value like TRUE / FALSE.
    'delegated-to' : None,    # Use: 0-1    Specify the calendar users to whom the calendar user specified by the property has delegated participation.
    'delegated-from' : None,    # Use: 0-1    Specify the calendar users that have delegated their participation to the calendar user specified by the property.
    'sent-by' : None,    # Use: 0-1    Specify the calendar user that is acting on behalf of the calendar user specified by the property.
    'cn' : None,    # Use: 0-1    Specify the common name to be associated with the calendar user specified by the property.
    'dir' : None,    # Use: 0-1    Specify reference to a directory entry associated with the calendar user specified by the property.
    'language' : None,    # Use: 0-1    Specify the language for text values in a property or property parameter.
    }

    def import_ical(self, cr, uid, ical_data):
        if ical_data.value:
            self.__attribute__['sent-by'] = ical_data.value
        for key, val in ical_data.params.items():
            if self.__attribute__.has_key(key.lower()):
                if type(val) == type([]):
                    self.__attribute__[key] = val[0]
                else:
                    self.__attribute__[key] = val
        return
    
class crm_section(osv.osv, Calendar):
    _name = 'crm.case.section'
    _inherit = 'crm.case.section'
    _description = 'Cases Section'

    def export_cal(self, cr, uid, ids, context={}):
        # Set all property of CalDAV
        self.export_ical()

    def import_cal(self, cr, uid, ids, context={}):
        self.import_ical(cr, uid)
        # get all property of CalDAV
crm_section()

class caldav_attendee(Attendee, osv.osv):
    _name = 'caldav.attendee'
    _description = 'Attendee information'
    _rec_name = 'cutype'
    
    Attendee.__attribute__.update({
        'cutype' : {'field':'cutype', 'type':'text'},    # Use: 0-1    Specify the type of calendar user specified by the property like "INDIVIDUAL"/"GROUP"/"RESOURCE"/"ROOM"/"UNKNOWN".
        'member' : {'field':'member', 'type':'text'},    # Use: 0-1    Specify the group or list membership of the calendar user specified by the property.
        'role' : {'field':'role', 'type':'text'},    # Use: 0-1    Specify the participation role for the calendar user specified by the property like "CHAIR"/"REQ-PARTICIPANT"/"OPT-PARTICIPANT"/"NON-PARTICIPANT"
        'partstat' : {'field':'partstat', 'type':'text'}, # Use: 0-1    Specify the participation status for the calendar user specified by the property. like use for VEVENT :- "NEEDS-ACTION"/"ACCEPTED"/"DECLINED"/"TENTATIVE"/"DELEGATED", use for VTODO :-"NEEDS-ACTION"/"ACCEPTED"/"DECLINED"/"TENTATIVE"/"DELEGATED"/"COMPLETED"/"IN-PROCESS" and use for VJOURNAL :- "NEEDS-ACTION"/"ACCEPTED"/"DECLINED".
        'rsvp' : {'field':'rsvp', 'type':'boolean'},    # Use: 0-1    Specify whether there is an expectation of a favor of a reply from the calendar user specified by the property value like TRUE / FALSE.
        'delegated-to' : {'field':'delegated_to', 'type':'char'},    # Use: 0-1    Specify the calendar users to whom the calendar user specified by the property has delegated participation.
        'delegated-from' : {'field':'delegated_from', 'type':'char'},    # Use: 0-1    Specify the calendar users that have delegated their participation to the calendar user specified by the property.
        'sent-by' : {'field':'sent_by', 'type':'text'},    # Use: 0-1    Specify the calendar user that is acting on behalf of the calendar user specified by the property.
        'cn' : {'field':'cn', 'type':'text'},    # Use: 0-1    Specify the common name to be associated with the calendar user specified by the property.
        'dir' : {'field':'dir', 'type':'text'},    # Use: 0-1    Specify reference to a directory entry associated with the calendar user specified by the property.
        'language' : {'field':'language', 'type':'text'},    # Use: 0-1    Specify the language for text values in a property or property parameter.
    })
     
    _columns = {
                'cutype' : fields.selection([('INDIVIDUAL','INDIVIDUAL'), ('GROUP','GROUP'),\
                        ('RESOURCE','RESOURCE'), ('ROOM','ROOM'), ('UNKNOWN','UNKNOWN') ], 'CUTYPE'),
                'member' : fields.char('Member', size=124),
                'role' : fields.selection([('CHAIR','CHAIR'), ('REQ-PARTICIPANT','REQ-PARTICIPANT'),\
                        ('OPT-PARTICIPANT','OPT-PARTICIPANT'), ('NON-PARTICIPANT','NON-PARTICIPANT')], 'ROLE'),
                'partstat' : fields.selection([('NEEDS-ACTION','NEEDS-ACTION'), ('ACCEPTED','ACCEPTED'),\
                        ('DECLINED','DECLINED'), ('TENTATIVE','TENTATIVE'), ('DELEGATED', 'DELEGATED' )], 'PARTSTAT'),
                'rsvp' :  fields.boolean('RSVP'), 
                'delegated_to' : fields.char('DELEGATED-TO', size=124),
                'delegated_from' : fields.char('DELEGATED-FROM', size=124),
                'sent_by' : fields.char('SENT-BY', size=124),
                'cn' : fields.char('CN', size=124),
                'dir' : fields.char('DIR', size=124),
                'language' : fields.char('LANGUAGE', size=124),
                }

caldav_attendee()

class crm_case(osv.osv, Event):
    _name = 'crm.case'
    _inherit = 'crm.case'
    _description = 'Cases'
    
    Event.__attribute__.update({
        'class' : {'field':'class', 'type':'text'}, 
        'created' : {'field':'create_date', 'type':'datetime'}, # keep none for now
        'description' : {'field':'description', 'type':'text'}, 
        'dtstart' : {'field':'date', 'type':'datetime'}, 
        #'last-mod' : {'field':'write_date', 'type':'datetime'}, 
        'location' : {'field':'location', 'type':'text'}, 
        'organizer' : {'field':'partner_id', 'sub-field':'name', 'type':'text'}, 
        'priority' : {'field':'priority', 'type':'int'}, 
        'dtstamp'  : {'field':'date', 'type':'datetime'}, 
        'seq' : None, 
        'status' : {'field':'state', 'type':'text'}, 
        'summary' : {'field':'name', 'type':'text'}, 
        'transp' : {'field':'transparent', 'type':'text'}, 
        'uid' : {'field':'id', 'type':'text'}, 
        'url' : {'field':'caldav_url', 'type':'text'}, 
        'recurid' : None, 
#        'attach' : {'field':'attachment_ids', 'sub-field':'datas', 'type':'list'}, 
        'attendee' : {'field':'attendees', 'type':'text'},
#        'categories' : {'field':'categ_id', 'sub-field':'name'},
#        'categories' : {'field':None , 'sub-field':'name', 'type':'text'}, # keep none for now
        'comment' : None, 
        'contact' : None, 
        'exdate'  : None, 
        'exrule'  : None, 
        'rstatus' : None, 
        'related' : None, 
        'resources' : None, 
        'rdate' : None, 
        'rrule' : {'field':'rrule', 'type':'text'}, 
        'x-openobject-id' : {'field':'id', 'type':'text'}, 
        'x-openobject-model' : {'value':_name, 'type':'text'}, 
#        'duration' : {'field':'duration'}, 
        'dtend' : {'field':'date_closed', 'type':'datetime'}, 
    })
    
    def _get_location(self, cr, uid, ids, name, arg, context=None):
        res = {}
        
        for case in self.browse(cr, uid, ids):
            if case.partner_address_id:
                add = case.partner_address_id
                st = add.street and add.street+',\n'  or ''
                st2 = add.street2 and add.street2+',\n'  or ''
                ct = add.city and add.city+',\n'  or ''
                zip = add.zip and add.zip or ''
                country = add.country_id and add.country_id.name+',\n'  or ''
                res[case.id] = st + st2+ ct + country + zip
            else:
                res[case.id] = ''
        return res
    
    def _get_rdates(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for case in self.browse(cr, uid, ids):
            if case.rrule:
                res[case.id] = str(self.get_recurrent_dates(str(case.rrule), case.date))
        return res
    
    _columns = {
        'categ_id': fields.many2many('crm.case.categ', 'crm_category_rel', 'case_id', 'category_id', 'Categories'),
        'class' : fields.selection([('PUBLIC','PUBLIC'), ('PRIVATE','PRIVATE'),\
                 ('CONFIDENTIAL','CONFIDENTIAL')], 'Class'),
        'location' : fields.function(_get_location, method=True, store = True, string='Location', type='text'), 
        'freebusy' : fields.text('FreeBusy'), 
        'transparent' : fields.selection([('OPAQUE','OPAQUE'), ('TRANSPARENT','TRANSPARENT')], 'Trensparent'),
        'caldav_url' : fields.char('Caldav URL', size=34), 
#        'attachment_ids' : function ("one2many from ir.attachemnt"), 
        'attendee' :  fields.text('Attendee'),  #TODO : display dynamic view from text value
        'rrule' : fields.text('Recurrent Rule'), 
        'rdates' : fields.function(_get_rdates, method=True, string='Recurrent Dates',\
                                   store=True, type='text'),
       'attendees': fields.many2many('caldav.attendee', 'crm_attendee_rel', 'case_id', 'attendee_id', 'Attendees'),
    }
    
    _defaults = {
             'caldav_url': lambda *a: 'http://localhost:8080',
             'class': lambda *a: 'PUBLIC',
             'transparent': lambda *a: 'OPAQUE',
        }
     
    def export_cal(self, cr, uid, ids, context={}):
        crm_data = self.read(cr, uid, ids, ['name', 'class', 'create_date',\
                     'description', 'date', 'write_date', 'duration', 'priority', \
                     'date', 'state', 'transparent', 'caldav_url', 'categ_id', \
                     'date_closed', 'partner_id', 'location', 'rrule'])
        ical = vobject.iCalendar()
        event = Event()
        for crm in crm_data:
            ical.add('vevent')
            vevent = ical.vevent
            for key, val in event.__attribute__.items():
                if val == None or key == 'rrule':  
                    continue
                if val.has_key('field') and val.has_key('sub-field') and crm[val['field']] and crm[val['field']]:
                    vevent.add(key).value = crm[val['field']][1]
                elif val.has_key('field') and crm[val['field']]:
                    if val['type'] == "text":
                        vevent.add(key).value = str(crm[val['field']])
                    elif val['type'] == 'datetime' and crm[val['field']]:
                        vevent.add(key).value = datetime.strptime(crm[val['field']], "%Y-%m-%d %H:%M:%S")
            if crm[event.__attribute__['rrule']['field']]:
                startdate = datetime.strptime(crm['date'],"%Y-%m-%d %H:%M:%S")
                if not startdate:
                    startdate = datetime.now()
                rset1 = rrulestr(str(crm[event.__attribute__['rrule']['field']]), dtstart=startdate, forceset=True)
                vevent.rruleset = rset1
            
        return ical.serialize().replace(vobject.icalendar.CRLF, vobject.icalendar.LF).strip()

    def import_cal(self, cr, uid, ids, data, context={}):
        file_content = base64.decodestring(data['form']['file_path'])
        self.import_ical(cr, uid, file_content)
        vals = {}
        for map_dict in self.__attribute__:
            map_val = self.ical_get(map_dict, 'value')
            field = self.ical_get(map_dict, 'field')
            if field and map_val:
                    vals[field] = map_val
        section_id = self.pool.get('crm.case.section').search(cr, uid, [('name', 'like', 'Meet%')])[0]
        vals.update({'section_id' : section_id})
        vals.pop('id')
        vals.pop('create_date')
        case_id = self.create(cr, uid, vals)
        return

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        res = super(crm_case, self).search(cr, uid, args, offset,
                limit, order, context,count )
#        Event.search(self, cr, uid, args, offset, limit, order, context, count)
        return res

    def browse(self, cr, uid, select, context=None, list_class=None, fields_process={}):
        select = map(lambda x:int(str(x).split('-')[0]), select)
        return super(crm_case, self).browse(cr, uid, select, context, list_class, fields_process)

    def read(self, cr, uid, ids, fields=None, context=None,
            load='_classic_read'):
#         logic for recurrent event
#         example : 123-20091111170822
        ids = map(lambda x:int(str(x).split('-')[0]), ids)
        res = super(crm_case, self).read(cr, uid, ids, fields=fields,context=context, load=load)
        result =  res + []
        read_ids = ",".join([str(x) for x in ids])
        cr.execute('select id,rrule,rdates from crm_case where id in (%s)' % read_ids)
        rrules = filter(lambda x: not x['rrule']==None,cr.dictfetchall())
        rdates = []
        for data in rrules:
            if data['rrule'] and data['rdates']: # delete 2nd condition at last
                rdates = eval(data['rdates'])
            for res_temp in res:
                if res_temp['id'] == data['id']:
                    val = res_temp
#                    result.remove(val)
            for rdate in rdates:
                import re
                idval = (re.compile('\d')).findall(rdate)
                val['date'] = rdate
                id = str(val['id']).split('-')[0]
#             COMMENTED BECAUSE OF PROBLEM OF INTEGER ID
                val['id'] = id + '-' + ''.join(idval)

                val1 = val.copy()
                result += [val1]
        return result 
    
    def unlink(self, cr, uid, ids, context=None):
        ids_new = map(lambda x:(str(x).split('-')[1]), ids)
        #TODO: Change RRULE
        ids = map(lambda x:int(str(x).split('-')[0]), ids)
        return super(crm_case, self).unlink(cr, uid, ids)

crm_case()


class ir_attachment(osv.osv):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'

    def search_count(self, cr, user, args, context=None):
        args1 = []
        for arg in args:
            args1.append(map(lambda x:str(x).split('-')[0], arg))
        return super(ir_attachment, self).search_count(cr, user, args1, context)

ir_attachment()
