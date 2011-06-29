# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
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

from osv import osv, fields
from tools.translate import _

import decimal_precision as dp
from datetime import datetime, date, time

def strToDate(dt):
    return date(int(dt[0:4]),int(dt[5:7]),int(dt[8:10]))

class training_participation_generator(osv.osv_memory):
    _name = 'training.participation.generator'

    _columns = {
        'contact_ids': fields.many2many('res.partner.contact', 'participation_contact_rel', 'participation_id', 'contact_id', 'Contact', required=True, help='Select the Participant.'),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'subscription_state': lambda *a: 'confirmed',
    }

    def default_get(self, cr, uid, fields, context=None):
        # context['active_model': u'res.partner.contact'
        if context is None:
            context = {}
        return {'contact_ids': context['active_ids']}

    def generate(self, cr, uid, contact, context=None):
        ''' This methode generate or update participations from the contact data
            If not exist subscription, create one
            If exist more than one subscription, select the first one
            If not exist subscription_line, create one
            If exist more than one subscription_line, select the firs one
            If not exist participations, create one
            If exist participations, update them with the actual values of the contact data
            Input:  contact: One contact browse object
            Output: True: If not error reported
                    False: If error occurred
        '''
        if context is None:
            context = {}
        weekdays = {
            0: 'monday',
            1: 'tuesday',
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
            5: 'saturday',
            6: 'sunday',
        }
        result = True
        today = datetime.now().strftime('%Y-%m-%d 00:00:00')
        seance_obj = self.pool.get('training.seance')
        participation_obj = self.pool.get('training.participation')
        contacts_obj = self.pool.get('res.partner.contact')
        weekdays_obj = self.pool.get('training.dining_hall.weekdays')
        subscription_obj = self.pool.get('training.subscription')
        subscription_line_obj = self.pool.get('training.subscription.line')
        if not contact.group_id:
            raise osv.except_osv(_('Error!'), _('The contact %s %s haven\'t got a group relationship!') % (contact.first_name, contact.name))

        group = weekdays_obj._find_group(cr, uid, contact.group_id, context = context)
        if not group:
            raise osv.except_osv(_('Error!'), _('The group %s or its parents haven\'t got any seance defined. You must choose another one.') % contact.group_id.name)
        session = group.session_id

        if not contact.group_id.school_id:
            raise osv.except_osv(_('Error!'), _('The group %s is not assignet to any school!') % contact.group.name)
        if not contact.group_id.school_id.partner_id.property_product_pricelist:
            raise osv.except_osv(_('Error!'), _('The school %s haven\'t got any default pricelist assigned!') % contact.group_id.school_id.name)
        price_list = contact.group_id.school_id.partner_id.property_product_pricelist
    
        if not contact.job_ids:
            raise osv.except_osv(_('Error!'), _('The contact %s haven\'t got a partner relationship!') % contact.name)
        jobs = contact.job_ids 
        for job in jobs:
            address = job.address_id            #TODO It can exist more than one address. Here we take the first one not empty.
            partner = job.address_id.partner_id #TODO It can exist more than one partner. Here we take the first one not null.
            if address and partner:
                break

        # If not exist subscription, create it.
        subscription_ids = subscription_obj.search(cr, uid, [('partner_id', '=', partner.id)], context=context)
        if not len(subscription_ids):
            subscription_values = {
                'partner_id': partner.id,
                'address_id': address.id,
            }
            subscription_id = subscription_obj.create(cr, uid, subscription_values, context=context)
        else:
            # If exist more than one subscription. Here we take the first one.
            subscription_id = subscription_ids[0]
        subscription = subscription_obj.browse(cr, uid, subscription_id, context = context)

        # If not exist subscription line, create one.
        subscription_line_ids = subscription_line_obj.search(cr, uid, [('session_id', '=', session.id), ('partner_id', '=', partner.id), ('contact_id', '=', contact.id)], context=context)
        if not len (subscription_line_ids):
            subscription_line_values = {
                "job_id": job.id,
                "subscription_id": subscription.id,
                "subscription_state": subscription.state,
                "price_list_id": price_list.id,
                "session_id": session.id,
                "price": 0.0,
                "contact_id": contact.id,
            }
            subscription_line_id = subscription_line_obj.create(cr, uid, subscription_line_values, context=context)
        else:
            # If exist more than one subscription line. Here we take the first one.
            subscription_line_id = subscription_line_ids[0]
        subscription_line = subscription_line_obj.browse(cr, uid, subscription_line_id, context=context)

        seance_ids = seance_obj.search(cr, uid, [('date', '>=', today), ('group_id', '=', group.id)], context=context)
        seances = seance_obj.browse(cr, uid, seance_ids, context=context)
        for seance in seances:
            participation_ids = participation_obj.search(cr, uid, [('seance_id', '=', seance.id),('subscription_line_id', '=', subscription_line_id)], context=context)
            if not len(participation_ids):
                seance_obj._create_participation(cr, uid, seance, subscription_line, context=context)
            else:
                for participation_id in participation_ids:
                    participation = participation_obj.browse(cr, uid, participation_id, context=context)

                    weekdays_ids = weekdays_obj.search(cr ,uid, [
                        ('contact_id', '=', participation.subscription_line_id.job_id.contact_id.id),
                        ('date_from', '<=', participation.seance_date),
                        ('date_to', '>=', participation.seance_date)
                    ], context=context)
                    if weekdays_ids:
                        dining_hall_weekdays = weekdays_obj.read(cr, uid, weekdays_ids, [
                            'sunday','monday','tuesday','wednesday','thursday','friday','saturday'
                        ], context=context)[0]
                        weekday = strToDate(participation.seance_date).weekday()
                        result = result and participation_obj.write(cr, uid, [participation_id], {
                            'expected_present' : dining_hall_weekdays[weekdays[weekday]],
                            'contact_id': contact.id,
                        }, context=context)
                    else:
                        result = result and participation_obj.write(cr, uid, [participation_id], {
                            'expected_present' : False,
                            'contact_id': contact.id,
                        }, context=context)
        return result      

    def generate_participations(self, cr, uid, ids, context=None):
        # context['active_model']: u'res.partner.contact'
        if context is None:
            context = {}
        for data in self.browse(cr, uid, ids, context = context):
            for contact in data.contact_ids:
                self.generate(cr, uid, contact, context = context)
        return {'type': 'ir.actions.act_window_close'}

training_participation_generator()
