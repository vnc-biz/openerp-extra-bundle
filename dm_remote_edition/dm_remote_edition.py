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

from osv import fields
from osv import osv

class dm_mail_service(osv.osv): # {{{
    _inherit = "dm.mail_service"
    
    _columns = {
          'default_printer': fields.char('Default Printer', size=64),
          'default_printer_tray': fields.char('Default Printer Tray', size=64),
          'user_id': fields.many2one('res.users', 'Printer User'),
          'sorting_rule_id': fields.many2one('dm.campaign.document.job.sorting_rule', 'Sorting Rule')
        }
    
dm_mail_service() # }}}


class dm_campaign_document_job(osv.osv): # {{{
    _inherit = "dm.campaign.document.job"
    
    _columns = {
         'user_id': fields.many2one('res.users', 'Printer User'),
        }
    
dm_campaign_document_job() # }}}



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
