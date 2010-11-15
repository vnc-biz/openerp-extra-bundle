# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
##############################################################################

from osv import fields, osv

class BetterZip(osv.osv):
    " Zip/NPA object"
    _name = "res.better.zip"
    _description = __doc__
    _order = "priority"

    _columns = {
                   'priority':fields.integer('Priority'),
                   'name':fields.char('ZIP', size=64, required=True),
                   'city':fields.char('City', size=64, required=True),
                }
    _defaults = {
        'priority':lambda *x:100
    }
    
    def name_get(self, cursor, uid, ids, context=None) :
        res = []
        for r in self.browse(cursor, uid, ids) :
            res.append((r.id, u"%s %s" %(r.name, r.city)))
        return res
BetterZip()

class ZipAdd(osv.osv):
    _inherit = "res.partner.address"
    _columns = {
                   'zip_id':fields.many2one('res.better.zip', 'ZIP OBJ')
                }
                
    def onchange_zip_id(self, cursor, uid, ids, zip_id):
        if not zip_id :
            return {}
        else :
            if isinstance(zip_id, list) :
                zip_id = zip_id[0]
            zip = self.pool.get('res.better.zip').browse(cursor, uid, zip_id)
            return {
            'value':{
                'zip':zip.name,
                'city':zip.city
                }
            }
ZipAdd()