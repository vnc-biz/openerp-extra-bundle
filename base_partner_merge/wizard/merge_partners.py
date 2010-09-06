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
import tools
import wizard
import pooler
from tools import UpdateableStr, UpdateableDict
from tools.translate import _

_MERGE_FORM = UpdateableStr()
_MERGE_FIELDS = UpdateableDict()

partner_form = '''<?xml version="1.0"?>
<form string="Merge Two Partners">
    <field name="partner_id1" />
    <field name="partner_id2" />
</form>'''

partner_fields = {
    'partner_id1': {'string': 'First partner', 'type': 'many2one', 'relation':'res.partner', 'help': 'Select first partner to merge', 'required': True},
    'partner_id2': {'string': 'Second partner', 'type': 'many2one', 'relation':'res.partner', 'help': 'Select second partner to merge', 'required': True},
    }

class wizard_merge_partners(wizard.interface):

    def _build_form(self, cr, uid, data, context):
        res = {}
        quest_fields = {}
        filter_name = {}
        filter_type = {}
        filter_required = {}
        m2m_list = []
        m2m_dict = {}

        pool = pooler.get_pool(cr.dbname)
        quest_form='''<?xml version="1.0"?>
            <form string="%s">''' % _('Merge Partners')
        partner_ids = ",".join(map(str, [data['form']['partner_id1'], data['form']['partner_id2']]))
        fields_ids = pool.get('ir.model.fields').search(cr, uid, [('model', '=', 'res.partner')], context=context)
        fields_data = pool.get('ir.model.fields').read(cr, uid, fields_ids, ['name', 'field_description', 'ttype', 'relation', 'required'], context=context)
        for field in fields_data:
            filter_name[tools.ustr(field['name'])] = tools.ustr(field['field_description'])
            filter_type[tools.ustr(field['name'])] = [tools.ustr(field['ttype']), tools.ustr(field['relation'])]
            filter_required[tools.ustr(field['name'])] = field['required']
            if field['ttype'] == 'many2many':
                m2m_list.append(tools.ustr(field['name']))

        if m2m_list:
            partner_data = pool.get('res.partner').read(cr, uid, [data['form']['partner_id1'], data['form']['partner_id2']], m2m_list ,context=context)
        for m2m in m2m_list:
            m2m_dict[m2m] = [(6, 0, partner_data[0][m2m] + partner_data[1][m2m])]

        cr.execute('SELECT * FROM res_partner AS part WHERE part.id in ('+partner_ids+')')
        result = cr.dictfetchall()
        for part1 in result[0]:
            for part2 in result[1]:
                if part1 == part2:
                    if part1 not in ('create_date', 'write_date', 'id', 'write_uid'):# to be check
                        if result[0][part1] is not None and result[1][part2] is not None and result[0][part1] == result[1][part2]:
                            res[part1] = tools.ustr(result[0][part1])
                        #every fields where one value is 'None', can be filled automatically by the other value if existing: no need to put that field on screen 2
                        elif result[0][part1] is None and result[1][part2] is not None and result[0][part1] != result[1][part2]:
                            res[part1] = tools.ustr(result[1][part2])
                        elif result[0][part1] is not None and result[1][part2] is None and result[0][part1] != result[1][part2]:
                            res[part1] = tools.ustr(result[0][part1])
                        #----------------------
                        elif (result[0][part1] is not None or result[1][part2] is not None) and result[0][part1] != result[1][part2]:
                            if filter_type[part1][0] == 'binary': # Improve: for use binary field copy while merging partner
#                                import base64
#                                import cStringIO
#                                if result[0][part1] is None:
#                                    x = ''
#                                else:
#                                    buf1 = result[0][part1] and cStringIO.StringIO(result[0][part1])
#                                    x = base64.encodestring(buf1.getvalue())
#                                    buf1.close()
#                                if result[1][part2] is None:
#                                    a = ''
#                                else:
#                                    buf2 = result[1][part2] and cStringIO.StringIO(result[1][part2])
#                                    a = base64.encodestring(buf2.getvalue())
#                                    buf2.close()
#                                quest_form = quest_form + '<field name="%s"/><newline/>' % (part1,)
#                                quest_fields['%s' % (part1,)] = {'string': filter_name[part1], 'type': 'selection', 'selection':[(x, 'Partner1-'+part1),(a, 'Partner2-'+part2)],}
                                continue
                            if filter_required[part1]:
                                quest_form = quest_form + '<field name="%s" required="True"/><newline/>' % (part1,)
                            else:
                                quest_form = quest_form + '<field name="%s"/><newline/>' % (part1,)
                            select1 = False
                            select2 = False
                            if isinstance(result[0][part1],float):
                                result[0][part1] = str(result[0][part1])
                            if isinstance(result[0][part2],float):
                                result[0][part1] = str(result[0][part2])
                            if isinstance(result[1][part1],float):
                                result[1][part1] = str(result[1][part2])
                            if isinstance(result[1][part2],float):
                                result[1][part2] = str(result[1][part2])
                            if result[0][part1] in (True, False):
                                result[0][part1] = str(result[0][part1])
                            if result[1][part2] in (True, False):
                                result[1][part2] = str(result[1][part2])
                            if result[0][part1] is None:
                                result[0][part1] = 'None'
                                select1 = True
                            if result[1][part2] is None:
                                result[1][part2] = 'None'
                                select2 = True
                            x = result[0][part1]
                            y = result[0][part1]
                            a = result[1][part2]
                            b = result[1][part2]
                            if filter_type[part1][0] == 'many2one':
                                relation = filter_type[part1][1].replace('.','_')
                                if result[0][part1] != 'None':
                                    cr.execute("select * from "+relation+" where id=%s"%(tools.ustr(result[0][part1])))
                                    first_m2o = cr.dictfetchone()
                                    if first_m2o.has_key('name') and first_m2o['name']:
                                        x = first_m2o['id']
                                        y = first_m2o['name']
                                if result[1][part2] != 'None':
                                    cr.execute("select * from "+relation+" where id=%s"%(tools.ustr(result[1][part2])))
                                    second_m2o = cr.dictfetchone()
                                    if second_m2o.has_key('name') and second_m2o['name']:
                                        a = second_m2o['id']
                                        b = second_m2o['name']
                            if select1:
                                quest_fields['%s' % (part1,)] = {'string': filter_name[part1], 'type': 'selection', 'selection':[(a, b), ('','None')]}
                            elif select2:
                                quest_fields['%s' % (part1,)] = {'string': filter_name[part1], 'type': 'selection', 'selection':[(x, y), ('','None')]}
                            else:
                                quest_fields['%s' % (part1,)] = {'string': filter_name[part1], 'type': 'selection', 'selection':[(x, y),(a, b)],}

        quest_form = quest_form + '''</form>'''
        _MERGE_FORM. __init__(quest_form)
        _MERGE_FIELDS.__init__(quest_fields)
        return {'res': res, 'm2m_dict': m2m_dict, 'new_partner': False}

    def _create_partner(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        res = data['form']['res']
        part1 = data['form']['partner_id1']
        part2 = data['form']['partner_id2']
        data['form'].pop('res')
        data['form'].pop('partner_id1')
        data['form'].pop('partner_id2')
        res.update(data['form'])
        res.update(data['form']['m2m_dict'])
        for key, val in res.items():
            if val in ('True', 'False'):
                res[key] = eval(val)

        if hasattr(pool.get('res.partner'), '_sql_constraints'):
            #for uniqueness constraint (vat number for example)...
            c_names = []
            remove_field = {}
            unique_fields = []
            for const in pool.get('res.partner')._sql_constraints:
                c_names.append('res_partner_' + const[0])
            if c_names:
                c_names = tuple(map(lambda x: "'"+ x +"'", c_names))
                cr.execute("""select column_name from \
                        information_schema.constraint_column_usage u \
                        join  pg_constraint p on (p.conname=u.constraint_name) \
                        where u.constraint_name in (%s) and p.contype='u' """ % c_names)
                for i in cr.fetchall():
                    remove_field[i[0]] = None
                    unique_fields.append(i[0])
                    unique_fields.append('name')
                    unique_data = pool.get('res.partner').read(cr, uid, [part1, part2], unique_fields)
                    str_unq = '---------------------------------------\n'
                    for u in unique_data:
                        for key, value in u.items():
                            if key == 'id' or not value:
                                continue
                        str_unq += key + ': ' + str(value) + '\n'
                    if res.has_key('comment') and res['comment']:
                        res['comment'] += '\n' + str_unq
                    else:
                        res['comment'] = str_unq

        remove_field.update({'active': False})
        pool.get('res.partner').write(cr, uid, [part1, part2], remove_field)
       # if res.has_key('comment') and res['comment']:
       #     res['comment'] += '\n' + str_unq
       # else:
       #     res['comment'] = str_unq

        part_id = pool.get('res.partner').create(cr, uid, res, context)
        # For one2many fields on res.partner
        cr.execute("select name, model from ir_model_fields where relation='res.partner' and ttype not in ('many2many', 'one2many');")
        for name, model_raw in cr.fetchall():
            if hasattr(pool.get(model_raw), '_auto'):
                if not pool.get(model_raw)._auto:
                    continue
            elif hasattr(pool.get(model_raw), '_check_time'):
                continue
            else:
                if hasattr(pool.get(model_raw), '_columns'):
                    from osv import fields
                    if pool.get(model_raw)._columns.get(name, False) and isinstance(pool.get(model_raw)._columns[name], fields.many2one):
                        model = model_raw.replace('.', '_')
                        cr.execute("update "+model+" set "+name+"="+str(part_id)+" where "+ tools.ustr(name) +" in ("+ tools.ustr(part1) +", "+tools.ustr(part2)+")")

        data['form']['new_partner'] = part_id
        return {}

    def _open_partner(self, cr, uid, data, context):
        pool_obj = pooler.get_pool(cr.dbname)
        model_data_ids = pool_obj.get('ir.model.data').search(cr,uid,[('model','=','ir.ui.view'),('name','=','view_partner_form')])
        resource_id = pool_obj.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'domain': "[('id', 'in', ["+','.join(map(str, [data['form']['new_partner']]))+"])]",
            'name': 'Partners',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'views': [(False,'tree'), (resource_id, 'form')],
            'type': 'ir.actions.act_window'
        }

    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form', 'arch': partner_form, 'fields': partner_fields, 'state': [('end', 'Cancel'), ('next', 'Next')]}
                },
        'next': {
             'actions': [_build_form],
             'result':{'type': 'form', 'arch': _MERGE_FORM, 'fields': _MERGE_FIELDS, 'state': [('end', 'Cancel'), ('next_1', 'Create And Open Partner')]}
                 },
        'next_1': {
             'actions': [_create_partner],
             'result': {'type':'action', 'action':_open_partner,  'state': 'end'}
                 },
            }
wizard_merge_partners('base_partner.merge')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
