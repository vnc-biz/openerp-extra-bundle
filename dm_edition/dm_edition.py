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

class dm_campaign_document_job_batch(osv.osv): # {{{
    _name = "dm.campaign.document.job.batch"

    _columns = {
        'name': fields.char('Name', required=True, size=64),
        'campaign_document_job_ids': fields.one2many('dm.campaign.document.job', 'batch_id', 'Campaign Document Jobs'),
        'state': fields.selection([('pending', 'Pending'), ('error', 'Error'), ('done', 'Done')], 'State'),
    }
    _defaults = {
        'state': lambda *a: 'pending',
        }
    
dm_campaign_document_job_batch() # }}}

#class dm_offer_document_job(osv.osv): # {{{
#    _name = "dm.offer.document.job"
#
#    _columns = {
#        'name': fields.char('Name', required=True, size=64),
#        'document_ids': fields.one2many('dm.offer.document', 'document_job', 'Offer Documents'),
#    }
#    
#dm_offer_document_job() # }}}

class dm_campaign_document_job_sorting_rule(osv.osv): # {{{
    _name = "dm.campaign.document.job.sorting_rule"
    
    _columns = {
        'name': fields.char('Name', required=True, size=64), 
        'code': fields.char('Code', required=True, size=64),
        'by_customer_country': fields.boolean('By Customer Country'),
        'by_overlay': fields.boolean('By Overlay'),
        'by_product': fields.boolean('By Product'),
        'by_page_qty': fields.boolean('By Page Quantity'),
        'by_offer_step': fields.boolean('By Offer Step'),
        'qty_limit': fields.integer('Qty. limit')
    }
    
dm_campaign_document_job_sorting_rule() # }}}

class dm_campaign_document_job(osv.osv): # {{{
    _name = "dm.campaign.document.job"

    _columns = {
        'name': fields.char('Name', required=True, size=64),
        'batch_id': fields.many2one('dm.campaign.document.job.batch', 'Job Batch'),
        'campaign_document_ids': fields.one2many('dm.campaign.document', 'campaign_document_job', 'Campaign Documents'),
        'process_date': fields.datetime('Processing Date'),
        'state': fields.selection([('pending', 'Pending'), ('error', 'Error'), ('done', 'Done')], 'State'),
        'sorting_rule_id': fields.many2one('dm.campaign.document.job.sorting_rule', 'Sorting Rule'),
        'sorting_name' : fields.char('Sorting value', size = 64),
    }
    _defaults = {
        'state': lambda *a: 'pending',
        }    
dm_campaign_document_job() # }}}

class dm_offer_document(osv.osv): # {{{
    _inherit = "dm.offer.document"
    
    _columns = {
        'printer': fields.char('Printer', size=64),
        'printer_tray': fields.char('Printer Tray', size=64),
        'verso': fields.boolean('Verso'),
        'sequence': fields.integer('Sequence')
    }
    
dm_offer_document() # }}}

class dm_campaign_document(osv.osv): # {{{
    _inherit = 'dm.campaign.document'
    
    _columns = {
        'printer': fields.char('Printer', size=64),
        'printer_tray': fields.char('Printer Tray', size=64),
        'campaign_document_job': fields.many2one('dm.campaign.document.job', 'Campaign Document Job'),
        'campaign_document_job_position': fields.integer('Campaign Document Job Position'),
        'verso': fields.boolean('Verso')
    }
    
dm_campaign_document() # }}}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
