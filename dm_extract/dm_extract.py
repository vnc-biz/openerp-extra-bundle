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

class dm_segmentation_type(osv.osv): # {{{
    _name = "dm.segmentation.type"
    _description = "Segmentation Type"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=32, required=True),
        'mode': fields.selection([('input', 'Input'), 
                                            ('output', 'Output'), 
                                            ('process', 'Process')], 
                                            'Mode',  readonly=True),
        }  
dm_segmentation_type()

class dm_segmentation(osv.osv): # {{{
    _name = "dm.segmentation"
    _description = "Segmentation"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=64, required=True),
        'step_ids':fields.one2many('dm.segmentation.step','segmentation_id',
                                            'Steps'),
        'notes': fields.text('Description', translate=True),
        'active_only': fields.boolean('Active'),
        }  
dm_segmentation() 

class dm_segmentation_step(osv.osv): # {{{
    _name = "dm.segmentation.step"
    _description = "Segmentation Type"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'mode': fields.selection([('input', 'Input'), 
                                            ('output', 'Output'), 
                                            ('process', 'Process')], 
                                            'Mode',  required=True),
        'segmentation_id':fields.many2one('dm.segmentation',
                                            'Segmentation'),
        'type_id':fields.many2one('dm.segmentation.type',
                                            'Segmentation Type',required=True),
        'segment_type': fields.char('Type Code', size=64),                                   
        'next_step_id':fields.many2one('dm.segmentation.step', 'Next Step'),
        'prev_step_id':fields.many2one('dm.segmentation.step', 'Previous Step'),
        'previous_step_ids':fields.one2many('dm.segmentation.step','prev_step_id',
                                            'Previous Steps'),
        'campaign_id':fields.many2one('dm.campaign', 'Campaign'),                              
                                            
        'proposition_id':fields.many2one('dm.campaign.proposition',
                                            'Proposition'),
        'segment_id':fields.many2one('dm.campaign.proposition.segment','Segments'),                               
        'offer_id':fields.many2one('dm.offer', 'Offer'),  
        'trademark_id':fields.many2one('dm.trademark', 'Trademark'),
        'dealer_id': fields.many2one('res.partner','Dealer', domain="[('category_id.name','=','Dealer')]"),

        'country_id':fields.many2one('res.country', 'Country'),   
        'currency_id':fields.many2one('res.currency', 'Currency'),
        'address_text_criteria_ids' : fields.one2many('dm.address.text_criteria', 'segmentation_id', 'Address Textual Criteria', attrs="{'invisible':[('type','!=','customer')]}"),
        'address_numeric_criteria_ids' : fields.one2many('dm.address.numeric_criteria', 'segmentation_id', 'Address Numeric Criteria'),
        'address_boolean_criteria_ids' : fields.one2many('dm.address.boolean_criteria', 'segmentation_id', 'Address Boolean Criteria'),
        'address_date_criteria_ids' : fields.one2many('dm.address.date_criteria', 'segmentation_id', 'Address Date Criteria'),   
        } 
    def on_change_segment_type(self, cr, uid, ids, type_id):
        res = {'value': {}}
        if type_id:
            segment_type = self.pool.get('dm.segmentation.type').read(cr, uid, [type_id])[0]
            res['value'] = {'segment_type': segment_type['code']}
        return res 
    
dm_segmentation_step()

class dm_campaign_proposition_segment(osv.osv):
    _name = "dm.campaign.proposition.segment"
    _description = "Segmentation"
    _inherit = "dm.campaign.proposition.segment"
    _columns = {
                'segmentation_id':fields.many2one('dm.segmentation', 'Segmentation'),
                }
    
dm_campaign_proposition_segment()

TEXT_OPERATORS = [ # {{{
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
] # }}}

class dm_address_text_criteria(osv.osv): # {{{
    _name = "dm.address.text_criteria"
    _description = "address Segmentation Textual Criteria"
    _rec_name = "segmentation_id"

    def _get_field_type(self, cr, uid, context={}):
        ttype_filter = ['many2many', 'many2one']
        cr.execute("select distinct ttype from ir_model_fields where ttype \
                     in (select distinct ttype from ir_model_fields where model = 'res.partner.address' \
                     and ttype not in ("+ ','.join(map(lambda x:"'"+x+"'", ttype_filter)) + "))")
        field_type = map(lambda x: x[0], cr.fetchall())
        res = []
        for type in field_type:
            if type == 'selection':
                res.append(('char', type))
            else :
                res.append((type, type))
        return res

    _columns = {
        'segmentation_id':fields.many2one('dm.segmentation',
                                          'Segmentation'),
        'field_id' : fields.many2one('ir.model.fields','Address Field',
               domain=[('model_id.model','=','res.partner.address'),
               ('ttype','like','char')],
               context={'model':'res.partner.address'},required=True),
        'operator' : fields.selection(TEXT_OPERATORS, 'Operator', size=32 ,required=True),
        'value' : fields.char('Value', size=128,required=True),
    }
    
dm_address_text_criteria() # }}}

class dm_address_numeric_criteria(osv.osv): # {{{
    _name = "dm.address.numeric_criteria"
    _description = "address Segmentation Numeric Criteria"
    _rec_name = "segmentation_id"

    _columns = {
        'segmentation_id':fields.many2one('dm.segmentation',
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
        'segmentation_id':fields.many2one('dm.segmentation',
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
        'segmentation_id':fields.many2one('dm.segmentation',
                                                'Segmentation'),
        'field_id':fields.many2one('ir.model.fields','Address Field',
               domain=[('model_id.model','=','res.partner.address'),
               ('ttype','in',['date','datetime'])],
               context={'model':'res.partner.address'},required=True),
        'operator':fields.selection(DATE_OPERATORS,'Operator',size=32,
                                        required=True),
        'value': fields.date('Date',required=True),
    }
dm_address_date_criteria() # }}}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
