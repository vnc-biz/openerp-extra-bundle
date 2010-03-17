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
from mx import DateTime
import netsvc


class one2many_mod_pline(fields.one2many):#{{{
    def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
        if not context:
            context = {}
        if not values:
                values = {}
        res = {}
        for id in ids:
            res[id] = []
        cr.execute("select id from product_category where name='Direct Marketing'")
        direct_id = cr.fetchone()
        sql="select id,name from product_category where parent_id=%d" %direct_id
        cr.execute(sql)
        res_type = cr.fetchall()
        prod_categ_type={}
        for x in res_type:
            prod_categ_type[x[1]]=x[0]
        for id in ids:
            if name[0] == 'd':
                ids2 = obj.pool.get(self._obj).search(cr, user,
                  [('campaign_id','=',id),
                  ('product_category','=',prod_categ_type['DTP'])], limit=self._limit)
            elif name[0] == 'm':
                ids2 = obj.pool.get(self._obj).search(cr, user,
                   [('campaign_id','=',id),
                   ('product_category','=',prod_categ_type['Mailing Manufacturing'])],
                   limit=self._limit)
            elif name[0] == 'c':
                ids2 = obj.pool.get(self._obj).search(cr, user,
                 [('campaign_id','=',id),
                 ('product_category','=',prod_categ_type['Customers List'])],
                  limit=self._limit)
            elif name[0] == 'i':
                ids2 = obj.pool.get(self._obj).search(cr, user, [('campaign_id','=',id),
                ('product_category','=',prod_categ_type['Items'])], 
                limit=self._limit)
            else :
                ids2 = obj.pool.get(self._obj).search(cr, user, [('campaign_id','=',id),('product_category','=',prod_categ_type['Mailing Manufacturing'])], limit=self._limit)
            for r in obj.pool.get(self._obj)._read_flat(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
                res[id].append( r['id'] )
        return res#}}}


class dm_campaign(osv.osv): # {{{
    _inherit = "dm.campaign"
    _columns = {
        'manufacturing_responsible_id' : fields.many2one('res.users','Responsible'),
        'dtp_responsible_id' : fields.many2one('res.users','Responsible'),
        'files_responsible_id' : fields.many2one('res.users','Responsible'),
        'item_responsible_id' : fields.many2one('res.users','Responsible'),
        'dtp_purchase_line_ids': one2many_mod_pline('dm.campaign.purchase_line',
                                         'campaign_id',"DTP Purchase Lines",
                                    domain=[('product_category', '=', 'DTP')],
                                     context={'product_category': 'DTP'}),
        'manufacturing_purchase_line_ids': one2many_mod_pline('dm.campaign.purchase_line',
                                            'campaign_id', 
                                            "Manufacturing Purchase Lines",
                                            domain=[('product_category', '=',
                                                     'Mailing Manufacturing')],
                         context= {'product_category': 'Mailing Manufacturing'}),
        'cust_file_purchase_line_ids': one2many_mod_pline('dm.campaign.purchase_line',
                                       'campaign_id', 
                                       "Customer Files Purchase Lines",
                                        domain = [('product_category',
                                                 '=', 'Customers List')],
                            context = {'product_category': 'Customers List'}),
        'item_purchase_line_ids': one2many_mod_pline('dm.campaign.purchase_line',
                                     'campaign_id', "Items Purchase Lines",
                                    domain=[('product_category','=','Items')],
                                     context={'product_category': 'Items'}),

    }
dm_campaign() # }}}

PURCHASE_LINE_TRIGGERS = [ # {{{
    ('draft','At Draft'),
    ('open','At Open'),
    ('planned','At Planning'),
    ('close','At Close'),
    ('manual','Manual'),
]

PURCHASE_LINE_STATES = [
    ('pending','Pending'),
    ('requested','Quotations Requested'),
    ('ordered','Ordered'),
    ('delivered','Delivered'),
]

PURCHASE_LINE_TYPES = [
    ('manufacturing','Manufacturing'),
    ('items','Items'),
    ('customer_file','Customer Files'),
    ('translation','Translation'),
    ('dtp','DTP'),
]

QTY_TYPES = [
    ('quantity_planned','planned Quantity'),
    ('quantity_wanted','Wanted Quantity'),
    ('quantity_delivered','Delivered Quantity'),
    ('quantity_usable','Usable Quantity'),
]

DOC_TYPES = [
    ('po','Purchase Order'),
    ('rfq','Request For Quotation'),
] # }}}


class dm_offer(osv.osv):
    _name = "dm.offer"
    _inherit = "dm.offer"

    _columns = {
        'translation_ids': fields.one2many('dm.offer.translation', 
                                            'offer_id', 'Translations', 
                                            ondelete="cascade", readonly=True),
        }

dm_offer()

