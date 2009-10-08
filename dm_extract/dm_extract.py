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

class dm_address_segmentation(osv.osv): # {{{
    _name = "dm.address.segmentation"
    _description = "Segmentation"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=32, required=True),
        'notes': fields.text('Description'),
        'sql_query': fields.text('SQL Query'),
        'query_criteria_ids': fields.one2many('dm.query.criteria', 
                                        'segmentation_id', 'Query Criteria'),
#        'address_numeric_criteria_ids':
#            fields.one2many('dm.address.numeric_criteria',
#                                 'segmentation_id','Address Numeric Criteria'),
#        'address_boolean_criteria_ids':
#            fields.one2many('dm.address.boolean_criteria',
#                                'segmentation_id','Address Boolean Criteria'),
#        'address_date_criteria_ids': 
#            fields.one2many('dm.address.date_criteria',
#                                    'segmentation_id','Address Date Criteria'),
    }

    def set_address_criteria(self, cr, uid, ids, context={}):
        query_obj = self.browse(cr, uid, ids).query_criteria_ids
        where_clause = []
        for q_obj in query_obj:
            value = getattr(q_obj, 'value_'+q_obj.field_type)
            if q_obj.field_type == 'boolean':
                where_clause.append("rpa.%s %s %s"% (q_obj.field_id.name,
                                    q_obj.operator.code,value))
            if q_obj.field_type == 'date':
                where_clause.append("rpa.%s %s '%s'"% (q_obj.field_id.name,
                                    q_obj.operator.code,value))
            if q_obj.field_type == 'char':
                where_clause.append("rpa.%s %s '%s'"% (q_obj.field_id.name,
                                    q_obj.operator.code,'%'+ value+ '%'))
            if q_obj.field_type == 'integer':
                where_clause.append("rpa.%s %s %f"% (q_obj.field_id.name,
                                    q_obj.operator.code, value))
        if where_clause:
            sql_query = """select distinct rpa.id\n from res_partner_address \n 
                                where %s"""% (' and '.join(where_clause))
        else:
            sql_query = """select distinct rpa.name \n
                            from res_partner_address rpa """
        return sql_query

    def create(self, cr, uid, vals, context={}):
        ids =super(dm_address_segmentation, self).create(cr, uid, vals, context)
        sql_query = self.set_address_criteria(cr, uid, ids)
        self.write(cr, uid, ids, {'sql_query':sql_query})
        return ids

    def write(self, cr, uid, ids, vals, context=None):
        super(dm_address_segmentation, self).write(cr, uid, ids, vals, context)
        if isinstance(ids, (int, long)):
            ids = [ids]
        for i in ids:
            sql_query = self.set_address_criteria(cr, uid, i)
            super(dm_address_segmentation, self).write(cr, uid, i, 
                                                {'sql_query':sql_query})
        return ids

dm_address_segmentation() # }}}

class dm_campaign_proposition_segment(osv.osv):
    _name = "dm.campaign.proposition.segment"
    _description = "Segmentation"
    _inherit = "dm.campaign.proposition.segment"
    _columns = {
                'segmentation_id':fields.many2one('dm.address.segmentation',
                                                  'Segments'),
                }
    
dm_campaign_proposition_segment()

'''TEXT_OPERATORS = [ # {{{
    ('like','like'),
    ('ilike','ilike'),
] # }}}

NUMERIC_OPERATORS = [ # {{{
    ('=','equals'),
    ('<','smaller then'),
    ('>','bigger then'),
] # }}}

BOOL_OPERATORS = [ # {{{
    ('is','is'),
    ('isnot','is not'),
] # }}}

DATE_OPERATORS = [ # {{{
    ('=','equals'),
    ('<','before'),
    ('>','after'),
] # }}}'''


_OPERATORS = [ # {{{
    ('date','Date'),
    ('boolean','Boolean'),
    ('char','Text'),
    ('integer','Numeric'),
] # }}}

class dm_query_operator(osv.osv): # {{{
    _name = "dm.query.operator"
    _description = "Query Openrators"
    _columns = {
        'field_type': fields.selection(_OPERATORS, 'Field Type', size=32) ,
        'name': fields.char('Name', size=32),
        'code': fields.char('code', size=32),
    }
dm_query_operator() # }}}

class dm_query_criteria(osv.osv): # {{{
    _name = "dm.query.criteria"
    _description = "address Segmentation Textual Criteria"
    _rec_name = "segmentation_id"

    _columns = {
        'segmentation_id':fields.many2one('dm.address.segmentation',
                                          'Segmentation'),
        'field_id':fields.many2one('ir.model.fields', 'Field'),
        'field_type':fields.selection(_OPERATORS, 'Field Type', size=32) ,
        'operator':fields.many2one('dm.query.operator', 'Operator'),
        'value_char':fields.char('Value', size=128),
        'value_integer':fields.float('Value', digits=(16,2)),
        'value_boolean':fields.selection([('true','True'),('false','False')],
                                         'Value'),
        'value_date':fields.date('Date'),
    }
dm_query_criteria() # }}}

class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'
    
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context.has_key('name') and context['name']=='dm_fields':
            if context['ttype'] == 'char':
                cr.execute("select id from ir_model_fields where \
                            model='res.partner.address' and \
                        (ttype='many2one' or ttype = '%s')" %(context['ttype']))
                fields_ids = cr.fetchall()
                fields = map(lambda x: x[0], fields_ids)
                return fields
            else:
                field_id = super(ir_model_fields, self).search(cr, uid, 
                 args, offset, limit, order, context=context, count=count)
                return field_id

ir_model_fields()

'''class dm_address_numeric_criteria(osv.osv): # {{{
    _name = "dm.address.numeric_criteria"
    _description = "address Segmentation Numeric Criteria"
    _rec_name = "segmentation_id"

    _columns = {
        'segmentation_id':fields.many2one('dm.address.segmentation',
                                            'Segmentation'),
        'field_id': fields.many2one('ir.model.fields','Address Field',
               domain=[('model_id.model','=','res.partner.address'),
               ('ttype','in',['integer','float'])],
               context={'model':'res.partner.address'},required=True),
        'operator':fields.selection(NUMERIC_OPERATORS,'Operator',size=32,
                                                    required=True),
        'value': fields.float('Value', digits=(16,2),required=True),
    }
dm_address_numeric_criteria() # }}}

class dm_address_boolean_criteria(osv.osv): # {{{
    _name = "dm.address.boolean_criteria"
    _description = "address Segmentation Boolean Criteria"
    _rec_name = "segmentation_id"

    _columns = {
        'segmentation_id':fields.many2one('dm.address.segmentation',
                                            'Segmentation'),
        'field_id':fields.many2one('ir.model.fields','Address Field',
               domain=[('model_id.model','=','res.partner.address'),
                           ('ttype','like','boolean')],
               context={'model':'res.partner.address'},required=True),
        'operator':fields.selection(BOOL_OPERATORS,'Operator',size=32,
                                        required=True),
        'value':fields.selection([('true','True'),('false','False')],
                                    'Value',required=True),
    }
dm_address_boolean_criteria() # }}}

class dm_address_date_criteria(osv.osv): # {{{
    _name = "dm.address.date_criteria"
    _description = "address Segmentation Date Criteria"
    _rec_name = "segmentation_id"

    _columns = {
        'segmentation_id':fields.many2one('dm.address.segmentation',
                                                'Segmentation'),
        'field_id':fields.many2one('ir.model.fields','Address Field',
               domain=[('model_id.model','=','res.partner.address'),
               ('ttype','in',['date','datetime'])],
               context={'model':'res.partner.address'},required=True),
        'operator':fields.selection(DATE_OPERATORS,'Operator',size=32,
                                        required=True),
        'value': fields.date('Date',required=True),
    }
dm_address_date_criteria() # }}}'''

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
