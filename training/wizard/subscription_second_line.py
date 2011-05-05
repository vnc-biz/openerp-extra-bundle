# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved.
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
#    $Id$
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

from osv import osv

class training_subscription_second_line(osv.osv_memory):
    _name = 'training.subscription.second.line'

    def make_subscription(self, cr, uid, ids, context=None):
        if context is None:
            context={}
        subscription_line_second_ids = context.get('active_ids',[])
        if not subscription_line_second_ids:
            return {}
        subscription_obj= self.pool.get('training.subscription')
        subscription_line_obj = self.pool.get('training.subscription.line')
        subscription_line_second_obj = self.pool.get('training.subscription.line.second')
        partners = {}
        for subscription_line_second in subscription_line_second_obj.browse(cr, uid, subscription_line_second_ids, context=context):
            if subscription_line_second.partner_id:
                partners.setdefault(subscription_line_second.partner_id.id, []).append(subscription_line_second)
        for partner_id, lines in partners.iteritems():
            values = subscription_obj.on_change_partner(cr, uid, [], partner_id)['value']
            values.update({
                'partner_id' : partner_id,
            })
            subscription_id = subscription_obj.create(cr, uid, values, context=context)
            for line in lines:
                subscription_line_obj.create(cr, uid, {
                    'subscription_id' : subscription_id,
                    'session_id' : line.session_id.id,
                    'contact_id' : line.job_id.id,
                    'price': 1.0,
                    'job_id':line.job_id.id,
                    'price_list_id':line.job_id.pricelist_id.id,
                    'state': 'draft',
                }, context=context)
                line.unlink()

        return {}

training_subscription_second_line()
