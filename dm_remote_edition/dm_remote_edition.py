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
import re
import base64
pattern = re.compile("/Count\s+(\d+)")
class dm_mail_service(osv.osv): # {{{
    _inherit = "dm.mail_service"
    
    _columns = {
          'default_printer': fields.char('Default Printer', size=64),
          'default_printer_tray': fields.char('Default Printer Tray', size=64),
          'user_id': fields.many2one('res.users', 'Printer User'),
          'sorting_rule_id': fields.many2one('dm.campaign.document.job.sorting_rule', 'Sorting Rule'),
          'front_job_recap': fields.many2one('dm.offer.document', 'Front Job Recap'),
          'bottom_job_recap': fields.many2one('dm.offer.document', 'Bottom Job Recap'),

        }
dm_mail_service() # }}}


class dm_campaign_document_job(osv.osv): # {{{
    _inherit = "dm.campaign.document.job"
    
    _columns = {
         'user_id': fields.many2one('res.users', 'Printer User'),
         'use_front_recap': fields.boolean('Use Front Job Recap'),
         'use_bottom_recap': fields.boolean('Use Bottom Job Recap'),
        }
  
dm_campaign_document_job() # }}}

def generate_document_job(cr, uid, obj_id, context):
    pool = pooler.get_pool(cr.dbname)
    camp_doc_object = pool.get('dm.campaign.document')
    obj = camp_doc_object.browse(cr,uid,[obj_id])[0]
    ms_id = obj.mail_service_id
    type_id = pool.get('dm.campaign.document.type').search(cr, uid, [('code', '=', 'pdf')])[0]
    s_rule = ms_id.sorting_rule_id.by_customer_country
    camp_doc_job = {}
    camp_doc = camp_doc_object.browse(cr,uid,obj_id)
    sorting_name = ''
    if ms_id.sorting_rule_id.by_customer_country:
	    sorting_name = str(camp_doc.address_id.country_id.id)
    if ms_id.sorting_rule_id.by_offer_step:
        v = str(camp_doc.document_id.step_id.id)
        sorting_name = sorting_name and sorting_name+'_'+v or v        
    if ms_id.sorting_rule_id.by_page_qty:
        attach_obj = pool.get('ir.attachment')
        pattern = re.compile(r"/Count\s+(\d+)")
        attach_id = attach_obj.search(cr, uid,[('res_id', '=', camp_doc.id), 
	                           ('res_model', '=', 'dm.campaign.document')])
        if attach_id:
            attach = attach_obj.browse(cr, uid, attach_id[0])
            datas = base64.decodestring(attach.datas)
            v = str(pattern.findall(datas) and pattern.findall(datas)[0] or 0)
            sorting_name = sorting_name and sorting_name+'_'+v or v
    if ms_id.sorting_rule_id.by_product:
        if 'workitem_id' in context:
            res = pool.get('dm.workitem').browse(cr,uid,context['workitem_id'])
            if res.sale_order_id:
                product =['%d:%s'%(line.product_id.id,line.product_uom_qty) for line in res.sale_order_id.order_line]
                product.sort()
                v = '_'.join(product)
                sorting_name = sorting_name and sorting_name+'_'+v or v
    if ms_id.sorting_rule_id.by_overlay:
        if 'segment_id' in context:
            res = pool.get('dm.campaign.proposition.segment').browse(cr,uid,context['segment_id'])
            if res.campaign_id:
                product =['%d:%s'%(line.product_id.id,line.product_uom_qty) for line in res.sale_order_id.order_line]
                product.sort()
                v = '_'.join(product)
                sorting_name = sorting_name and sorting_name+'_'+v or v
                
    if sorting_name:
        camp_doc_job_obj = pool.get('dm.campaign.document.job')
        job_ids = camp_doc_job_obj.search(cr, uid, [('state', '=', 'pending'),
                            ('sorting_rule_id', '=', ms_id.sorting_rule_id.id),('sorting_name','=',sorting_name)])
        job_id = ''
        no_camp_doc =''
        for j_id in camp_doc_job_obj.browse(cr, uid, job_ids):
            if not ms_id.sorting_rule_id.qty_limit or ms_id.sorting_rule_id.qty_limit ==0 :
                job_id = j_id.id
            elif len(j_id.campaign_document_ids) < ms_id.sorting_rule_id.qty_limit:
                job_id = j_id.id
        if not job_id :
            camp_doc = camp_doc_object.browse(cr,uid,obj_id)
            job_vals = {
                    'name': camp_doc.segment_id.name or '' + str(k),
	             	'user_id': ms_id.user_id.id,
		            'sorting_rule_id': ms_id.sorting_rule_id.id,
                    'sorting_name': sorting_name,
                    'use_front_recap': ms_id.front_job_recap and True or False,
                    'bottom_job_recap': ms_id.bottom_job_recap and True or False,
                    'campaign_document_ids': [[4,obj_id]],
                    }
            job_id = camp_doc_job_obj.create(cr,uid,job_vals)
            if  ms_id.front_job_recap or ms_id.bottom_job_recap:
                camp_vals={
                       'segment_id': camp_doc.segment_id.id or False,
                       'name': camp_doc.document_id.step_id.code + "_" + str(camp_doc.address_id.id),
                       'type_id': type_id,
                       'mail_service_id': ms_id.id,
                       'address_id':camp_doc.address_id.id,
                       'campaign_document_job_ids' : job_id
                  }
                if ms_id.front_job_recap: 
                    camp_vals['document_id'] = ms_id.front_job_recap.id
                    no_camp_doc += 1
                if ms_id.bottom_job_recap:
                    camp_vals['document_id'] = ms_id.bottom_job_recap.id
                    no_camp_doc += 1                
        else:
            camp_doc_job_obj.write(cr, uid, job_id, 
                                       {'campaign_document_ids': [[4,obj_id]]})
    return {'code':'doc_done','ids': obj.id}								   		    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
