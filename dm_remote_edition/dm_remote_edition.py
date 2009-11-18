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
import pooler

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

def generate_document_job(cr,uid,obj_id):
    pool = pooler.get_pool(cr.dbname)
    camp_doc_object = pool.get('dm.campaign.document')
    obj = camp_doc_object.browse(cr,uid,[obj_id])[0]
    ms_id = obj.mail_service_id
    camp_doc_id = camp_doc_object.search(cr,uid,[('mail_service_id','=',ms_id.id)])
    s_rule = ms_id.sorting_rule_id.by_customer_country
    camp_doc_job = {}
    if ms_id.sorting_rule_id.by_customer_country :
	    for camp_doc in camp_doc_object.browse(cr,uid,camp_doc_id):
		    country_id = camp_doc.address_id.country_id.id
		    if country_id in camp_doc_job :
			    camp_doc_job[country_id].append(camp_doc.id)
		    else : 
			    camp_doc_job[country_id] = [camp_doc.id]
    elif ms_id.sorting_rule_id.by_offer_step:
	    for camp_doc in camp_doc_object.browse(cr,uid,camp_doc_id):
		    step_id = camp_doc.document_id.step_id.id
		    if step_id in camp_doc_job :
			    camp_doc_job[step_id].append(camp_doc.id)
		    else : 
			    camp_doc_job[step_id] = [camp_doc.id]
    print camp_doc_job
    if camp_doc_job:
        camp_doc_job_obj = pool.get('dm.campaign.document.job')
        for k,v in camp_doc_job.items():
            job_id = camp_doc_job_obj.search(cr, uid, [('sorting_rule_id', '=', ms_id.sorting_rule_id.id),
                                               ('state', '=', 'pending')])[0]
            if not job_id :
	            vals = {'name': camp_doc.segment_id.name or '' + str(k),
					         	'user_id': ms_id.user_id,
						        'sorting_rule_id': ms_id.sorting_rule_id.id,}
	            job_id = camp_doc_job_obj.create(cr,uid,vals)
            for i in v:
                camp_doc_job_obj.write(cr, uid, job_id, {'campaign_document_ids': [[4,i]]})						 

    return {'code':'done','ids':obj.id}								   		    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
