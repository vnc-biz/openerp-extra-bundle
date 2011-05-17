# -*- encoding: utf-8 -*-
#################################################################################
#                                                                               #
#    base_json_field for OpenERP                                          #
#    Copyright (C) 2011 Akretion Sébastien BEAU <sebastien.beau@akretion.com>   #
#                                                                               #
#    This program is free software: you can redistribute it and/or modify       #
#    it under the terms of the GNU Affero General Public License as             #
#    published by the Free Software Foundation, either version 3 of the         #
#    License, or (at your option) any later version.                            #
#                                                                               #
#    This program is distributed in the hope that it will be useful,            #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of             #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              #
#    GNU Affero General Public License for more details.                        #
#                                                                               #
#    You should have received a copy of the GNU Affero General Public License   #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.      #
#                                                                               #
#################################################################################

from osv import fields, osv
import netsvc
import json

class json_osv(osv.osv):
    
    #TODO : json in product.template and json in product.product

    def _get_js_fields(self, fields):
        self_fields = self._columns.keys()
        js_store_fields = {}
        js_fields = []
        for field in fields:
            if 'x_js_' in field and field in self_fields:
                store_field = field.split('_x_')[0].replace('x_js_', '')
                if js_store_fields.get(store_field, False):
                    js_store_fields[store_field] += [field]
                else:
                    js_store_fields[store_field] = [field]
                js_fields += [field]
        return js_store_fields, js_fields

    def get_json_field_to_read(self, fields=None, context=None):
        if context and context.get('call_from_browse', False):
            return False, [x for x in fields if 'x_js' not in x]
        elif not fields:
            return False, [x for x in self._columns.keys() if not 'x_js' in x]
        else:
            js_store_fields, js_fields = self._get_js_fields(fields)
            return js_store_fields, list(set(fields) - set(js_fields))

    def fields_to_json(vals):
        if 'x_js_' in '/'.join(vals.keys()):
            js_store_fields = self._get_js_fields(vals.keys())
            for js_store_field in js_store_fields:
                res={}
                for key in js_store_fields[js_store_field]:
                    if self._columns[key]._type == 'many2one':
                        print "the field %s have to be converted"%key
                        print dir(self._columns[key]._symbol_f)
                    res[key] = vals[key]
                    del vals[key]
                vals[js_store_field] = json.dumps(res)
        return vals

    def fields_to_json_with_update(object, js_store_fields, vals):
        #tmp_vals = self.convert_m2o_to_json(cr, uid, tmp_vals, context=context)
        for js_store_field in js_store_fields:
            #Read the actual value of json store field
            if object[js_store_field]:
                res = json.loads(object[js_store_field])
            else:
                res = {}

            #Update the json store field with the value and remove json field from the tmp_vals
            for key in js_store_fields[js_store_field]:
                if self._columns[key]._type == 'many2one':
                    print "the field %s have to be converted"%key
                    print self._columns[key]._symbol_f

                res[key] = tmp_vals[key]
                del tmp_vals[key]
            vals[js_store_fields] = json.dumps(res)
        return vals



    def convert_json_to_field(self, vals, js_store_fields, fields):
        if js_store_fields:
            for object in vals:
                #print "\n\n ===== product %s ====\n"%product.get('name', 'rien'), product.get('magento_fields', False)
                if type(object) == dict:
                    for store_field in js_store_fields:
                        print 'object[store_field]', object[store_field]
                        if object[store_field]:
                            values = json.loads(object[store_field])
                        else:
                            values = {}
                        for field in js_store_fields[store_field]:
                            if ('x_js'+ store_field +'_x_') in field:
                                object[field] = values.get(field, False)
                    for field in js_store_fields:
                        if not field in fields: 
                            del object[field_to_remove]
        return vals






    def json_to_field():
        for key in js_store_fields[js_store_field]:
            if self._columns[key]._type == 'many2one':
                print "the field %s have to be converted"%key
                print self._columns[key]._symbol_f._name
            res[key] = vals[key]
            del vals[key]
            vals[js_store_field] = json.dumps(res)
        return







    def read(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        print 'read'
        js_store_fields, fields_to_read = self.get_json_field_to_read(fields, context)
        res = super(json_osv, self).read(cr, uid, ids, fields_to_read, context, load)
        res2 = self.convert_json_to_field(res, js_store_fields, fields)
        print res2
        return res2

    def create(self, cr, uid, vals, context=None):
        if 'x_js_' in '/'.join(vals.keys()):
            vals = self.fields_to_json(vals)
        return super(product_product, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'x_js_' in '/'.join(vals.keys()):
            js_store_fields, js_fields = self._get_js_fields(vals.keys())
            wrid = []
            for object in self.read(cr, uid, ids, fields=js_store_fields, context=context):
                vals = self.fields_to_json_with_update(object, js_store_fields, vals)
                wrid += [super(json_osv, self).write(cr, uid, object['id'], vals, context=context)]
            return wrid
        else:
            return super(json_osv, self).write(cr, uid, ids, vals, context)
























    def read_with_json(self, cr, uid, ids, fields=None, context=None, load='_classic_read'):
        print 'context', context, fields
        print 'we are in the read'
        js_fields = False
        self_fields = self._columns.keys()
        #print 'column', self._columns
        #print "\n\n ===== original field to read ====\n", fields

        if not fields or context.get('call_from_browse', False):
            print 'read allll'
            fields_to_read = [x for x in self_fields if not 'x_js' in x]
        else:
            js_fields = []
            fields_to_read = []
            js_store_fields = []
            print 'else'
            for field in fields:
                #All json field of the object are remove from the field to read and the json store field is added if necessary
                if 'x_js_' in field and field in self_fields:
                    js_fields += [field]
                    store_field = field.split('_x_')[0].replace('x_js_', '')
                    if not store_field in js_store_fields:
                        js_store_fields += [store_field]
                else:
                    fields_to_read += [field]

            js_store_fields_to_add_and_remove = [x for x in js_store_fields if x not in fields_to_read]
            fields_to_read += js_store_fields_to_add_and_remove

        #print "\n\n ===== modif field to read ====\n", fields_to_read
        res = super(json_osv, self).read(cr, uid, ids, fields_to_read, context, load)
        print 'res', res
        if js_fields:
            for object in res:
                #print "\n\n ===== product %s ====\n"%product.get('name', 'rien'), product.get('magento_fields', False)
                if type(object) == dict:
                    for store_field in js_store_fields:
                        values = json.loads(object[store_field])
                        for field in js_fields:
                            if ('x_js'+ store_field +'_x_') in field:
                                object[field] = values.get(field, False)
                    for field_to_remove in js_store_fields_to_add_and_remove:
                        del object[field_to_remove]
        print "\n\n ===== res ====\n", res
        return res

    def convert_m2o_to_json(self, cr, uid, vals, context=None):
        attributs_option_ids = []
        for key in vals:
            if "x_js" in key and self._columns[key]._type == 'many2one':
                attributs_option_ids += [vals[key]]
        attributs_options={}

        for attr in  self.pool.get('magerp.product_attribute_options').read(cr, uid, attributs_option_ids, ['label'], context=context):
            attributs_options.update({attr['id'] : attr['label']})
        for key in vals:
            if "x_magerp_js" in key and self._columns[key]._type == 'many2one':
                vals[key] = [vals[key], attributs_options[vals[key]]]
        return vals



    def tttcreate(self, cr, uid, vals, context=None):
        if 'x_js_' in '/'.join(vals.keys()):
            js_store_fields = self._get_js_fields(vals.keys())
            for js_store_field in js_store_fields:
                res={}
                for key in js_store_fields[js_store_field]:
                    if self._columns[key]._type == 'many2one':
                        print "the field %s have to be converted"%key
                        print dir(self._columns[key]._symbol_f)
                    res[key] = vals[key]
                    del vals[key]
                vals[js_store_field] = json.dumps(res)
        print 'vals', vals
        return super(json_osv, self).create(cr, uid, vals, context)
    

    #The update Json have to be done product per product because the original json can be different
    def tttwrite(self, cr, uid, ids, vals, context=None):
        if 'x_js_' in '/'.join(vals.keys()):
            js_store_fields = self._get_js_fields(vals.key())
            wrid = []
            for object in self.read(cr, uid, ids, fields=js_store_fields, context=context):
                tmp_vals = vals.copy()
                #tmp_vals = self.convert_m2o_to_json(cr, uid, tmp_vals, context=context)
                for js_store_field in js_store_fields:
                    #Read the actual value of json store field
                    if object[js_store_field]:
                        res = json.loads(object[js_store_field])
                    else:
                        res = {}

                    #Update the json store field with the value and remove json field from the tmp_vals
                    for key in js_store_fields[js_store_field]:
                        if self._columns[key]._type == 'many2one':
                            print "the field %s have to be converted"%key
                            print self._columns[key]._symbol_c
                            print self._columns[key]._symbol_f
                            print self._columns[key]._symbol_set

                        res[key] = tmp_vals[key]
                        del tmp_vals[key]
                    tmp_vals[js_store_fields] = json.dumps(res)

                wrid += [super(json_osv, self).write(cr, uid, object['id'], tmp_vals, context=context)]
            return wrid
        else:
            return super(json_osv, self).write(cr, uid, ids, vals, context)





