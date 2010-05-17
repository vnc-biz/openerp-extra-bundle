#!/usr/bin/env python
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

from osv import osv, fields
import wizard
import pooler

class city(osv.osv):

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        res = []
        for line in self.browse(cr, uid, ids, context=context):
            location = line.name
            if line.zipcode:
                location = "%s %s" % (line.zipcode, location)
            if line.state_id:
                location = "%s, %s" % (location, line.state_id.name)
            if line.country_id:
                location = "%s, %s" % (location, line.country_id.name)
            res.append((line['id'], location))
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        res = super(city, self).search(cr, uid, args, offset=offset,
            limit=limit, order=order, context=context, count=count)
        if not res and args:
            args = [('zipcode', 'ilike', args[0][2])]
            res = super(city, self).search(cr, uid, args, offset=offset,
                limit=limit, order=order, context=context, count=count)
        return res

    _name = 'city.city'
    _description = 'City'
    _columns = {
        'state_id': fields.many2one("res.country.state", 'State',
            domain="[('country_id','=',country_id)]", select=1),
        'name': fields.char('City Name', size=64, required=True, select=1),
        'zipcode': fields.char('ZIP', size=64, select=1),
        'country_id': fields.many2one('res.country', 'Country', select=1),
        'code': fields.char('City Code', size=64,
            help="The official code for the city"),
    }
city()


class CountryState(osv.osv):
    _inherit = 'res.country.state'
    _columns = {
        'city_ids': fields.one2many('city.city', 'state_id', 'Cities'),
    }
CountryState()


class res_partner_address(osv.osv):
    _inherit = "res.partner.address"

    def _get_zip(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.location:
                res[obj.id] = obj.location.zipcode
            else:
                res[obj.id] = ""
        return res

    def _get_city(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.location:
                res[obj.id] = obj.location.name
            else:
                res[obj.id] = ""
        return res

    def _get_state(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.location and obj.location.state_id:
                res[obj.id] = [obj.location.state_id.id,
                               obj.location.state_id.name]
            else:
                res[obj.id] = False
        return res

    def _get_country(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.location and obj.location.country_id:
                res[obj.id] = [obj.location.country_id.id,
                               obj.location.country_id.name]
            else:
                res[obj.id] = False
        return res

    def _zip_search(self, cr, uid, obj, name, args, context=None):
        """Search for addresses in cities with this zip code"""
        if not args:
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid,
                [('zipcode', operator, value)], context=context)
            new_args.append(('location', 'in', ids))
        if new_args:
            # We need to ensure that location is NOT NULL. Otherwise all
            # addresses that have no location will 'match' current search
            # pattern.
            new_args.append(('location', '!=', False))
        return new_args

    def _city_search(self, cr, uid, obj, name, args, context=None):
        """Search for addresses in cities with this city name"""
        if not args:
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid,
                [('name', operator, value)], context=context)
            new_args.append(('location', 'in', ids))
        if new_args:
            # We need to ensure that location is NOT NULL. Otherwise all
            # addresses that have no location will 'match' current search
            # pattern.
            new_args.append(('location', '!=', False))
        return new_args

    def _state_id_search(self, cr, uid, obj, name, args, context=None):
        """Search for addresses in cities in this state"""
        if not args:
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid,
                [('state_id', operator, value)], context=context)
            new_args.append(('location', 'in', ids))
        if new_args:
            # We need to ensure that location is NOT NULL. Otherwise all
            # addresses that have no location will 'match' current search
            # pattern.
            new_args.append(('location', '!=', False))
        return new_args

    def _country_id_search(self, cr, uid, obj, name, args, context=None):
        """Search for addresses in cities in this country"""
        # Some countries don't have states, so we must search for cities in the
        # by country, not by country+state.
        if not args:
            return []
        new_args = []
        for argument in args:
            operator = argument[1]
            value = argument[2]
            ids = self.pool.get('city.city').search(cr, uid,
                [('country_id', operator, value)], context=context)
            new_args.append(('location', 'in', ids))
        if new_args:
            # We need to ensure that location is NOT NULL. Otherwise all
            # addresses that have no location will 'match' current search
            # pattern.
            new_args.append(('location', '!=', False))
        return new_args

    _columns = {
        'location': fields.many2one('city.city', 'Location', select=1),
        # XXX add store={...}
        'zip': fields.function(_get_zip, fnct_search=_zip_search, method=True,
            type="char", string='Zip', size=24),
        # XXX add store={...}
        'city': fields.function(_get_city, fnct_search=_city_search,
            method=True, type="char", string='City', size=128),
        # XXX add store={...}
        'state_id': fields.function(_get_state, fnct_search=_state_id_search,
            obj="res.country.state", method=True, type="many2one",
            string='State'),
        # XXX add store={...}
        'country_id': fields.function(_get_country,
            fnct_search=_country_id_search, obj="res.country", method=True,
            type="many2one", string='Country'),
    }
res_partner_address()
