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

from osv import fields
from osv import osv

class dm_document_job_batch(osv.osv): # {{{
    _name = "dm.document.job.batch"

    _columns = {
        'name': fields.char('Name', required=True, size=64),
        'document_job_ids': fields.one2many('dm.document.job', 'document_job_batch_id', 'Offer Document Jobs'),
        'state': fields.selection([('Pending', 'pending'), ('Error', 'error'), ('Done', 'done')], 'State'),
    }
    
dm_document_job_batch() # }}}

class dm_document_job(osv.osv): # {{{
    _name = "dm.document.job"

    _columns = {
        'name': fields.char('Name', required=True, size=64),
        'document_job_batch_id': fields.many2one('dm.document.job.batch', 'Job Batch'),
        'document_ids': fields.one2many('dm.offer.document', 'document_job', 'Offer Documents'),
        'state': fields.selection([('Pending', 'pending'), ('Error', 'error'), ('Done', 'done')], 'State'),
    }
    
dm_document_job() # }}}

class dm_offer_document(osv.osv): # {{{
    _inherit = "dm.offer.document"
    
    _columns = {
        'printer': fields.char('Printer', size=64),
        'printer_tray': fields.char('Printer Tray', size=64),
        'document_job': fields.many2one('dm.document.job', 'Document Job'),
        'document_job_position': fields.integer('Document Job Position'),
        'verso': fields.boolean('Verso')
    }
    
dm_offer_document() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: