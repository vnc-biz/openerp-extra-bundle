# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu). All Rights Reserved
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
############################################################################################

from osv import osv, fields
import netsvc
import time

class res_partner(osv.osv):
    _inherit = 'res.partner'

    _columns = {
        'notify_location' : fields.many2one('res.partner.job',
                                            'Notification for Location',
                                            domain="[('name', '=', active_id),('state', '=', 'current')]"),
    }

res_partner()

class training_location(osv.osv):
    _name = 'training.location'
    _description = 'Location'

    _columns = {
        'name' : fields.char('Room', size=64, select=True, required=True),
        'partner_id' : fields.many2one('res.partner', 'Partner', required=True),
        'address_id' : fields.many2one('res.partner.address', 'Address', required=True,
                                      domain="[('partner_id','=',partner_id)]"),
        'seats' : fields.integer('Seats', help='Total Seats'),
    }

    _defaults = {
        'seats' : lambda *a: 0,
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for obj in self.browse(cr, uid, list(set(ids)), context=context):
            res.append((obj.id, "%s (%s)" % (obj.name, obj.partner_id.name,)))

        return res

    def on_change_partner(self, cr, uid, ids, partner_id, context=None):
        if not partner_id:
            return False

        values = {
            'address_id' : 0,
        }

        proxy = self.pool.get('res.partner.address')
        ids = proxy.search(cr, uid, [('partner_id', '=', partner_id),('type', '=', 'default')])

        if not ids:
            ids = proxy.search(cr, uid, [('partner_id', '=', partner_id)])

        if ids:
            values['address_id'] = ids[0]

        return {'value' : values}

    def _check_address(self, cr, uid, ids, context=None):
        location_proxy = self.pool.get('training.location')

        location = location_proxy.browse(cr, uid, ids[0], context=context)

        address_proxy = self.pool.get('res.partner.address')

        return address_proxy.search_count(cr, uid, [('partner_id', '=', location.address_id.id)]) > 0

    def _check_seats(self, cr, uid, ids, context=None):
        return self.browse(cr, uid, ids, context=context)[0].seats > 0

    _constraints = [
        #(_check_address, "Can you check the address ?", ['partner_id', 'address_id']),
        (_check_seats, "This room has not seats !", ['seats']),
    ]

training_location()

class training_seance(osv.osv):
    _inherit = 'training.seance'

    _columns = {
        'location_id' : fields.many2one('training.location', 'Location', select=1, help='The location for seance'),
        'reserved' : fields.boolean('Reserved', help='Location is reserved '),
        'seats' : fields.related('location_id', 'seats', type='integer', string='Maximum Seats',
                                 readonly=True, help='Maximum seats available in location')
    }

    _defaults = {
        'reserved' : lambda *a: 0,
    }

    # training.seance
    #def copy(self, cr, uid, seance_id, defaults=None, context=None):
    #    defaults['location_id'] = 0
    #    defaults['reserved'] = 0
    #    return super(training_seance, self).copy(cr, uid, seance_id, defaults, context)


training_seance()

class training_session(osv.osv):
    _inherit = 'training.session'
    _columns = {
        'location_id' : fields.many2one('training.location', 'Location', select=1, help='The location for seance'),
        'seats' : fields.related('location_id', 'seats', type='integer', string='Maximum Seats',
                                 readonly=True, help='Maximum seats available in location')
    }

    #def copy(self, cr, uid, session_id, defaults=None, context=None):
    #    defaults['location_id'] = 0
    #    return super(training_session, self).copy(cr, uid, session_id, defaults, context)


    def _create_seance(self, cr, uid, session, context=None):
        seance_ids = super(training_session, self)._create_seance(cr, uid, session, context=context)
        if session.location_id:
            self.pool.get('training.seance').write(cr, uid, seance_ids, {'location_id' : session.location_id.id}, context=context)
        return seance_ids

training_session()

class training_participation_stakeholder(osv.osv):
    _inherit = 'training.participation.stakeholder'
    _columns = {
        'seance_location_id': fields.related('seance_id', 'location_id', type='many2one',
                                             relation='training.location',
                                             string='Location',
                                             readonly=True),
    }
training_participation_stakeholder()
