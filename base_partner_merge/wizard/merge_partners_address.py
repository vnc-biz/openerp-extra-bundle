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

import wizard
import pooler
from tools import UpdateableStr, UpdateableDict

_MERGE_FORM = UpdateableStr()
_MERGE_FIELDS = UpdateableDict()

address_form = '''<?xml version="1.0"?>
<form string="Merge Two Partner Address">
    <field name="address_id1" />
    <field name="address_id2" />
</form>'''

address_fields = {
    'address_id1': {'string': 'First address', 'type': 'many2one', 'relation':'res.partner.address', 'help': 'Select first partner address to merge', 'required': True},
    'address_id2': {'string': 'Second address', 'type': 'many2one', 'relation':'res.partner.address', 'help': 'Select second partner address to merge', 'required': True},
    }

class wizard_merge_partner_address(wizard.interface):

    def _build_form(self, cr, uid, data, context):
        res = {}
        quest_fields = {}
        filter_name = {}
        filter_type = {}
        m2m_list = []
        m2m_dict = {}

        pool = pooler.get_pool(cr.dbname)
        quest_form='''<?xml version="1.0"?>
            <form string="%s">''' % _('Merge Partner Addresses')
        partner_ids = ",".join(map(str, [data['form']['address_id1'], data['form']['address_id2']]))
        fields_ids = pool.get('ir.model.fields').search(cr, uid, [('model', '=', 'res.partner.address')], context=context)
        fields_data = pool.get('ir.model.fields').read(cr, uid, fields_ids, ['name', 'field_description', 'ttype', 'relation'], context=context)
        for field in fields_data:
            filter_name[str(field['name'])] = str(field['field_description'])
            filter_type[str(field['name'])] = [str(field['ttype']), str(field['relation'])]
            if field['ttype'] == 'many2many':
                m2m_list.append(str(field['name']))

        if m2m_list:
            partner_data = pool.get('res.partner.address').read(cr, uid, [data['form']['address_id1'], data['form']['address_id2']], m2m_list ,context=context)
        for m2m in m2m_list:
            m2m_dict[m2m] = [(6, 0, partner_data[0][m2m] + partner_data[1][m2m])]

        cr.execute('SELECT * FROM res_partner_address AS part WHERE part.id in ('+partner_ids+')')
        result = cr.dictfetchall()
        for add1 in result[0]:
            for add2 in result[1]:
                if add1 == add2:
                    if add1 not in ('create_date', 'write_date', 'id', 'write_uid'):# to be check
                        if result[0][add1] is not None and result[1][add2] is not None and result[0][add1] == result[1][add2]:
                            res[add1] = str(result[0][add1])
                        elif (result[0][add1] is not None or result[1][add2] is not None) and result[0][add1] != result[1][add2]:
                            if filter_type[add1][0] == 'binary': # Improve: for use binary field copy while merging partners
                                continue
                            quest_form = quest_form + '<field name="%s"/><newline/>' % (add1,)
                            select1 = False
                            select2 = False
                            if result[0][add1] in (True, False):
                                result[0][add1] = str(result[0][add1])
                            if result[1][add2] in (True, False):
                                result[1][add2] = str(result[1][add2])
                            if result[0][add1] is None:
                                result[0][add1] = 'None'
                                select1 = True
                            if result[1][add2] is None:
                                result[1][add2] = 'None'
                                select2 = True
                            x = result[0][add1]
                            y = result[0][add1]
                            a = result[1][add2]
                            b = result[1][add2]
                            if filter_type[add1][0] == 'many2one':
                                relation = filter_type[add1][1].replace('.','_')
                                if result[0][add1] != 'None':
                                    cr.execute("select * from "+relation+" where id=%s"%(str(result[0][add1])))
                                    first_m2o = cr.dictfetchone()
                                    if first_m2o.has_key('name') and first_m2o['name']:
                                        x = first_m2o['id']
                                        y = first_m2o['name']
                                if result[1][add2] != 'None':
                                    cr.execute("select * from "+relation+" where id=%s"%(str(result[1][add2])))
                                    second_m2o = cr.dictfetchone()
                                    if second_m2o.has_key('name') and second_m2o['name']:
                                        a = second_m2o['id']
                                        b = second_m2o['name']
                            if select1:
                                quest_fields['%s' % (add1,)] = {'string': filter_name[add1], 'type': 'selection', 'selection':[(a, b), ('','None')]}
                            elif select2:
                                quest_fields['%s' % (add1,)] = {'string': filter_name[add1], 'type': 'selection', 'selection':[(x, y), ('','None')]}
                            else:
                                quest_fields['%s' % (add1,)] = {'string': filter_name[add1], 'type': 'selection', 'selection':[(x, y),(a, b)],}

        quest_form = quest_form + '''</form>'''
        _MERGE_FORM. __init__(quest_form)
        _MERGE_FIELDS.__init__(quest_fields)
        return {'res': res, 'm2m_dict': m2m_dict, 'new_address': False}

    def _create_partner_address(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        res = data['form']['res']
        add1 = data['form']['address_id1']
        add2 = data['form']['address_id2']
        data['form'].pop('res')
        data['form'].pop('address_id1')
        data['form'].pop('address_id2')
        res.update(data['form'])
        res.update(data['form']['m2m_dict'])
        for key, val in res.items():
            if val in ('True', 'False'):
                res[key] = eval(val)
        add_id = pool.get('res.partner.address').create(cr, uid, res, context=context)

        # For one2many fields on res.partner.address
        cr.execute("select name, model from ir_model_fields where relation='res.partner.address' and ttype not in ('many2many', 'one2many');")
        for name, model_raw in cr.fetchall():
            if hasattr(pool.get(model_raw), '_auto'):
                if not pool.get(model_raw)._auto:
                    continue
            else:
                if hasattr(pool.get(model_raw), '_columns'):
                    from osv import fields
                    if isinstance(pool.get(model_raw)._columns[name], fields.many2one):
                        model = model_raw.replace('.', '_')
                        cr.execute("update "+model+" set "+name+"="+str(add_id)+" where "+str(name)+" in ("+str(add1)+", "+str(add2)+")")
        pool.get('res.partner.address').write(cr, uid, [add1, add2], {'active': False})
        data['form']['new_address'] = add_id
        return {}

    def _open_address(self, cr, uid, data, context):
        pool_obj = pooler.get_pool(cr.dbname)
        model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_partner_address_form1')])
        resource_id = pool_obj.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'domain': "[('id', 'in', ["+','.join(map(str, [data['form']['new_address']]))+"])]",
            'name': 'Address',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner.address',
            'views': [(False,'tree'), (resource_id, 'form')],
            'type': 'ir.actions.act_window'
        }

    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch': address_form, 'fields': address_fields, 'state': [('end', 'Cancel'), ('next', 'Next')]}
                },
        'next': {
             'actions': [_build_form],
             'result':{'type': 'form', 'arch': _MERGE_FORM, 'fields': _MERGE_FIELDS, 'state': [('end', 'Cancel'), ('next_1', 'Create And Open Address')]}
                 },
        'next_1': {
             'actions': [_create_partner_address],
             'result': {'type':'action', 'action':_open_address, 'state': 'end'}
                 },

            }
wizard_merge_partner_address('base_partner_address.merge')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: