# -*- coding: utf-8 -*-
##############################################################################
#
#    point_of_sale_extension module for OpenERP, profile for 2ed customer
#
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) 
#       All Rights Reserved, Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 SYLEAM (http://syleam.fr) 
#       All Rights Reserved, Christophe Chauvet <christophe.chauvet@syleam.fr>
#
#    This file is a part of point_of_sale_extension
#
#    point_of_sale_extension is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    point_of_sale_extension is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields

class company(osv.osv):
    _inherit = 'res.company'
    _columns = {
        'intdomain_alert_expire': fields.char('Alert Expire', size=100, help="Days notice of expire (separated with comma. Ex. 30,15,10)"),
        'intdomain_template': fields.many2one('poweremail.templates', 'Template'),
    }

company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
