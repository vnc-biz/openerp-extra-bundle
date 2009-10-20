# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
from osv import fields
from osv import osv

class dm_as_reject_type(osv.osv):#{{{
    _name = "dm.as.reject.type"
    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'code': fields.char('Code', size=32, required=True),
    }
dm_as_reject_type()#}}}

class dm_as_reject(osv.osv):#{{{
    _name = "dm.as.reject"
    _columns = {
                
        'date': fields.datetime('Date', required=True),
        'name': fields.char('Description', size=128, required=True),
        'origin':fields.char('Origin', size=64),
        'type_od': fields.many2one('dm.as.reject.type', 'Type', required=True),
   
    }
dm_as_reject()#}}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
