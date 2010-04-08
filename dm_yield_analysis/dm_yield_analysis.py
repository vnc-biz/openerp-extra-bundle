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

from osv import osv
from osv import fields

class dm_offer_step_tht_yield(osv.osv):
	_name = 'dm.offer.step.tht_yield'
	_description = 'Therotical yield offer steps'
	
	_columns = {
		'step_id':fields.many2one('dm.offer.step', 'Offer Step'),
		'country_id':fields.many2one('res.country', 'Country'),
		'rate': fields.float('Theoretical Rate'),
		'offer_id':fields.many2one('dm.offer', 'Offer'),
	}
	
dm_offer_step_tht_yield()

class dm_offer(osv.osv):
	_inherit = 'dm.offer'
	
	_columns = {
	    'tht_yield_country_ids':fields.many2many('res.country', 'dm_yield_country_rel', 'tht_yield_id', 'country_id', 'Application Countries'),
	    'tht_step_yield_ids':fields.one2many('dm.offer.step.tht_yield', 'offer_id', 'Theoretical Yields Array'),
	}
	
dm_offer()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

