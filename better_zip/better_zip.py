# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
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

class BetterZip(osv.osv):
    " Zip/NPA object"
    _name = "res.better.zip"
    _description = __doc__
    _order = "priority"

    _columns = {
                   'priority':fields.integer('Priority'),
                   'name':fields.char('ZIP', size=64, required=True),
                   'city':fields.char('City', size=64, required=True),
                }
    _defaults = {
        'priority':lambda *x:100
    }
    
    def name_get(self, cursor, uid, ids, context=None) :
        res = []
        for r in self.browse(cursor, uid, ids) :
            res.append((r.id, u"%s %s" %(r.name, r.city)))
        return res
BetterZip()

class ZipAdd(osv.osv):
    _inherit = "res.partner.address"
    _columns = {
                   'zip_id':fields.many2one('res.better.zip', 'ZIP OBJ')
                }
                
    def onchange_zip_id(self, cursor, uid, ids, zip_id):
        if not zip_id :
            return {}
        else :
            if isinstance(zip_id, list) :
                zip_id = zip_id[0]
            zip = self.pool.get('res.better.zip').browse(cursor, uid, zip_id)
            return {
            'value':{
                'zip':zip.name,
                'city':zip.city
                }
            }
ZipAdd()