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

class dm_address_segmentation(osv.osv): # {{{
    _inherit = "dm.address.segmentation"

    def set_address_criteria(self, cr, uid, id, context={}):
        query_obj = self.browse(cr, uid, id).query_criteria_ids
        rpa_where = []
        so_where = []
        for q_obj in query_obj:
            value = getattr(q_obj, 'value_'+q_obj.field_type)
            where = ''
            print "q_obj.field_id.model_id", q_obj.field_id.model_id
            tn = ''.join(map(lambda x: x[0], 
                             q_obj.field_id.model_id.model.split('.')))
            if q_obj.field_type == 'boolean':
                where = "%s.%s %s %s"% (tn, q_obj.field_id.name, 
                                        q_obj.operator.code, value)
            elif q_obj.field_type == 'date':
                where = "%s.%s %s '%s'"% (tn, q_obj.field_id.name, 
                                        q_obj.operator.code, value)
            elif q_obj.field_type == 'char':
                where = "%s.%s %s '%s'"% (tn, q_obj.field_id.name,
                                        q_obj.operator.code,'%'+value+'%')
            elif q_obj.field_type == 'integer':
                where = "%s.%s %s %f"% (tn, q_obj.field_id.name, 
                                        q_obj.operator.code, value)
            if where and q_obj.field_id.model_id.model == 'res.partner.address':
                rpa_where.append(where)
            elif where and q_obj.field_id.model_id.model == 'sale.order':
                so_where.append(where)
        if so_where:
            rpa_where.append('partner_id in (select partner_id from sale_order \
                                where %s )'%' and '.join(so_where))
        if rpa_where:
            sql_query = """select distinct rpa.id\n from res_partner_address rpa\
                            \n where %s"""% (' and '.join(rpa_where))
        else:
            sql_query = """
                    select distinct rpa.name \nfrom res_partner_address rpa """
        return sql_query

    _columns = {
        'order_query_criteria_ids': fields.one2many('dm.query.criteria', 
                                        'segmentation_id1', 'Query Criteria'),
        }

dm_address_segmentation() # }}}

class dm_query_criteria(osv.osv): # {{{
    _inherit = "dm.query.criteria"

    _columns = {
        'segmentation_id1' : fields.many2one('dm.address.segmentation' , 
        domain = [('model_id.model','in',('res.partner.address','sale.order'))])
    }

dm_query_criteria() # }}}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
