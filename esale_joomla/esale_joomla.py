# -*- coding: utf-8
##############################################################################
#
# Copyright (c) 2010 BCIM sprl. (http://www.bcim.be) All Rights Reserved.
#
# $Id:  $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields, osv

import sys, time, xmlrpclib
from tools import config
from wizard import except_wizard

import urllib2


def _decode(name):
    name = name.replace('+', '%20')
    name = urllib2.unquote(name)
    #DB is corrupted with utf8 and latin1 chars.
    decoded_name = name
    if isinstance(name, unicode):
        try:
            decoded_name = name.encode('utf8')
        except:
            decoded_name = name
    else:
        try:
            decoded_name = unicode(name, 'utf8')
        except:
            try:
                decoded_name = unicode(name, 'latin1').encode('utf8')
            except:
                decoded_name = name
    return decoded_name


def _xmlrpc(website):
    return xmlrpclib.ServerProxy("%s/xmlrpc/index.php" % website.url)


STATES = [
    ('new', 'new'),
    ('modified', 'modified'),
    ('deleted', 'deleted'),
    ('sync', 'synchronized'),
    ('imported', 'imported'),
    ('error', 'error')
]


class esale_joomla_web(osv.osv):
    _name = "esale_joomla.web"
    _description = "eCommerce Website"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'url': fields.char('URL', size=64, required=True),
        'login': fields.char('Login', size=64, required=True),
        'password': fields.char('Password', size=64, required=True),
        'shop_id': fields.many2one('sale.shop', 'Sale Shop', required=True),
        'active': fields.boolean('Active'),
        'product_ids': fields.one2many('esale_joomla.product_map', 'web_id', string='Products'),
        'tax_ids': fields.one2many('esale_joomla.tax_map', 'web_id', string='Taxes'),
        'category_ids': fields.one2many('esale_joomla.category_map', 'web_id', string='Categories'),
        'language_id': fields.many2one('res.lang', 'Language'),
        'producttypes_ids': fields.one2many('esale_joomla.producttype_map', 'web_id', string='Product Types'),
    }

    _defaults = {
        'active': lambda *a: 1
    }

esale_joomla_web()


class esale_joomla_synclog(osv.osv):
    _name = 'esale_joomla.synclog'
    _description = "eSale Import/Export log"
    _order = "date desc"

    OBJECT_TYPES = [('product', 'Product'), ('producttype', 'Product Type'), ('category', 'Category'), ('tax', 'Tax')]
    DIRECTIONS = [('import', 'Import'), ('export', 'Export')]

    _columns = {
        'date': fields.datetime('Log date', required=True, select=1),
        'user_id': fields.many2one('res.users', 'Exported By', required=True, readonly=True, select=1),
        'web_id': fields.many2one('esale_joomla.web', 'Web Shop', select=1),
        'object': fields.selection(OBJECT_TYPES, 'Object type', required=True, readonly=True),
        'type': fields.selection(DIRECTIONS, 'Synchronization direction', required=True, readonly=True, select=1),
        'errors': fields.integer('Number of errors', required=True, readonly=True),
        'junk': fields.function(lambda self, cr, uid, ids, name, attr, context: dict([(idn, '') for idn in ids]),
                method=True, string=" ", type="text"),
    }

    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for r in self.read(cr, uid, ids):
            res.append((r['id'], r['id']))
        return res

esale_joomla_synclog()


class esale_joomla_tax_map(osv.osv):
    _name = "esale_joomla.tax_map"
    _description = "eSale Taxes Mapping"
    _rec_name = 'esale_joomla_id'
    _order = 'esale_joomla_rate'

    def _status(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for e in self.browse(cr, uid, ids, context=context):
            if e.state in ('new', 'modified', 'deleted'):
                res[e.id] = e.state
            elif not e.tax_id and e.esale_joomla_id:
                res[e.id] = 'imported'
            elif e.tax_id and e.esale_joomla_id:
                res[e.id] = 'sync'
                if e.tax_id.amount != e.esale_joomla_rate:
                    res[e.id] = 'modified'
            else:
                res[e.id] = e.state
        return res

    _columns = {
        'tax_id': fields.many2one('account.tax', 'Tax'),
        'web_id': fields.many2one('esale_joomla.web', 'Web Shop', required=True),
        'esale_joomla_id': fields.integer('Web ID', readonly=True),
        'esale_joomla_country_id': fields.many2one('res.country', 'Web Country', required=True),
        'esale_joomla_rate': fields.float('Web Rate', digits=(16, 4), readonly=True),
        'state': fields.selection(STATES, 'state', readonly=True, required=True),
        'status': fields.function(_status, method=True, type='selection', selection=STATES, string='Status', store=False),
    }
    _defaults = {
        'state': lambda *a: 'new'
    }

    def write(self, cr, uid, ids, values, context=None):
        if 'state' in values:
            return super(esale_joomla_tax_map, self).write(cr, uid, ids, values, context=context)
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        k_ids = []
        m_ids = []
        s_ids = []
        for e in self.read(cr, uid, ids):
            if e['state'] in ('new'):
                k_ids.append(e['id'])
            elif e['state'] in ('imported', 'sync'):
                for k, v in values.iteritems():
                    if k not in ('tax_id'):
                        if not k.endswith('_id'):
                            if e[k] != v:
                                m_ids.append(e['id'])
                                break
                        elif e[k]:
                            if e[k][0] != v:
                                m_ids.append(e['id'])
                                break
                        elif v:
                            m_ids.append(e['id'])
                            break
                else:
                    s_ids.append(e['id'])
            else:
                m_ids.append(e['id'])
        res = True
        if len(k_ids):
            res &= super(esale_joomla_tax_map, self).write(cr, uid, k_ids, values, context=context)
        if len(m_ids):
            values['state'] = 'modified'
            res &= super(esale_joomla_tax_map, self).write(cr, uid, m_ids, values, context=context)
        if len(s_ids):
            values['state'] = 'sync'
            res &= super(esale_joomla_tax_map, self).write(cr, uid, s_ids, values, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        d_ids = []
        k_ids = []
        for e in self.browse(cr, uid, ids, context=context):
            if e.state in ('new'):
                d_ids.append(e.id)
            else:
                k_ids.append(e.id)
        res = True
        if len(d_ids):
            res &= super(esale_joomla_tax_map, self).unlink(cr, uid, d_ids, context=context)
        if len(k_ids):
            res &= self.write(cr, uid, k_ids, {'state': 'deleted'}, context=context)
        return res

    def unlink_permanent(self, cr, uid, ids, context=None):
        return super(esale_joomla_tax_map, self).unlink(cr, uid, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for r in self.read(cr, uid, ids):
            res.append((r['id'], r['id']))
        return res

    def webimport(self, cr, uid, web_ids, context={}):
        cnew = cupdate = cerror = 0
        for website in self.pool.get('esale_joomla.web').browse(cr, uid, web_ids):
            server = _xmlrpc(website)
            try:
                taxes = server.openerp2vm.get_taxes(website.login, website.password) #id, country, state, rate
            except Exception, e:
                print >> sys.stderr, "XMLRPC Error: %s" % e
                cerror += 1
            else:
                countryL = set()
                stateL = set()
                for tax in taxes:
                    (cid, ccountry, crate) = tax
                    countryL.add(str(ccountry))
                countries = {}
                if len(countryL):
                    cr.execute("select id, code from res_country where code in (%s);"%', '.join(map(repr, countryL)))
                    for x in cr.fetchall():
                        countries[x[1]] = x[0]
                for tax in taxes:
                    (cid, ccountry, crate) = tax
                    if not cid:
                        cerror += 1
                        continue
                    value = {
                        'web_id': website.id,
                        'esale_joomla_id': cid,
                        'esale_joomla_country_id': countries[ccountry],
                        'esale_joomla_rate': crate,
                        'state': 'imported',
                    }
                    id = self.search(cr, uid, [('web_id', '=', website.id), ('esale_joomla_id', '=', cid)])
                    if not len(id):
                        self.create(cr, uid, value)
                        cnew += 1
                    else:
                        self.write(cr, uid, id, value)
                        cupdate += 1
            self.pool.get('esale_joomla.synclog').create(cr, uid, {
                'web_id': website.id,
                'object': 'tax',
                'type': 'import',
                'errors': cerror,
            })

        return (cnew, cupdate, cerror)

    def webexport(self, cr, uid, web_id, tax_ids, context=None):
        cnew = cupdate = cdelete = cerror = 0
        website = self.pool.get('esale_joomla.web').browse(cr, uid, web_id)
        server = _xmlrpc(website)
        for el in self.browse(cr, uid, tax_ids, context=context):
            if el.state == 'deleted':
                try:
                    server.openerp2vm.delete_tax(website.login, website.password, el.esale_joomla_id)
                except Exception, e:
                    print >> sys.stderr, "XMLRPC Error : %r" % e
                else:
                    self.unlink_permanent(cr, uid, el.id, context=context)
                    cdelete += 1
            elif not el.tax_id:
                pass
            else:
                try:
                    eid = server.openerp2vm.set_tax(website.login, website.password, {'id': el.esale_joomla_id or 0,
                                    'country': el.esale_joomla_country_id.code,
                                    'rate': el.tax_id.amount, #FIX
                                   })
                    if not eid:
                        raise Exception('Failed')
                except Exception, e:
                    cerror += 1
                    print >> sys.stderr, "XMLRPC Error : %r" % e
                    self.write(cr, uid, el.id, {'state': 'error'}, context=context)
                else:
                    if not el.esale_joomla_id:
                        cnew += 1
                    else:
                        cupdate += 1
                    self.write(cr, uid, el.id, {'esale_joomla_id': eid, 'esale_joomla_rate': el.tax_id.amount, 'state': 'sync'}, context=context)
        self.pool.get('esale_joomla.synclog').create(cr, uid, {
            'web_id': web_id,
            'object': 'tax',
            'type': 'export',
            'errors': cerror,
        })
        return (cnew, cupdate, cdelete, cerror)

esale_joomla_tax_map()


class esale_joomla_category(osv.osv):
    _name = "esale_joomla.category"
    _description = "eSale Web Category"
    _columns = {
        'name': fields.char('Name', size=128, required=True),
    }

esale_joomla_category()


class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'esale_category_ids': fields.many2many('esale_joomla.category', 'esale_category_product_rel', 'product_id', 'category_id', 'eSale Categories'),
        'image': fields.char('Image Name', size=64),
        'online': fields.boolean('Visible on website', help="This will set the 'Publish' state in Joomla for this product"),
    }

product_product()


class esale_joomla_category_map(osv.osv):
    _name = "esale_joomla.category_map"
    _description = "eSale Web Categories Mapping"

    def _status(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for e in self.browse(cr, uid, ids, context=context):
            if e.state in ('new', 'modified', 'deleted'):
                res[e.id] = e.state
            elif not e.category_id and e.esale_joomla_id:
                res[e.id] = 'imported'
            elif e.category_id and e.esale_joomla_id:
                res[e.id] = 'sync'
            else:
                res[e.id] = e.state
        return res

    _columns = {
        'category_id': fields.many2one('esale_joomla.category', 'Web Category'),
        'web_id': fields.many2one('esale_joomla.web', 'Web Shop', required=True),
        'esale_joomla_id': fields.integer('Web ID', readonly=True),
        'esale_joomla_name': fields.char('Web Name', size=64, translate=True, required=True),
        'esale_joomla_parent_id': fields.many2one('esale_joomla.category_map', 'Parent'),
        'state': fields.selection(STATES, 'state', readonly=True, required=True),
        'status': fields.function(_status, method=True, type='selection', selection=STATES, string='Status', store=False),
    }
    _defaults = {
        'state': lambda *a: 'new'
    }

    def write(self, cr, uid, ids, values, context=None):
        if 'state' in values:
            return super(esale_joomla_category_map, self).write(cr, uid, ids, values, context=context)
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        k_ids = []
        m_ids = []
        s_ids = []
        for e in self.read(cr, uid, ids):
            if e['state'] in ('new'):
                k_ids.append(e['id'])
            elif e['state'] in ('imported', 'sync'):
                for k, v in values.iteritems():
                    if k not in ('category_id'):
                        if not k.endswith('_id'):
                            if e[k] != v:
                                m_ids.append(e['id'])
                                break
                        elif e[k]:
                            if e[k][0] != v:
                                m_ids.append(e['id'])
                                break
                        elif v:
                            m_ids.append(e['id'])
                            break
                else:
                    s_ids.append(e['id'])
            else:
                m_ids.append(e['id'])
        res = True
        if len(k_ids):
            res &= super(esale_joomla_category_map, self).write(cr, uid, k_ids, values, context=context)
        if len(m_ids):
            values['state'] = 'modified'
            res &= super(esale_joomla_category_map, self).write(cr, uid, m_ids, values, context=context)
        if len(s_ids):
            values['state'] = 'sync'
            res &= super(esale_joomla_category_map, self).write(cr, uid, s_ids, values, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        d_ids = []
        k_ids = []
        for e in self.browse(cr, uid, ids, context=context):
            if e.state in ('new'):
                d_ids.append(e.id)
            else:
                k_ids.append(e.id)
        res = True
        pids = self.search(cr, uid, [('esale_joomla_parent_id', 'in', ids)])
        res &= self.write(cr, uid, pids, {'esale_joomla_parent_id': None}, context=context)
        if len(d_ids):
            res &= super(esale_joomla_category_map, self).unlink(cr, uid, d_ids, context=context)
        if len(k_ids):
            res &= self.write(cr, uid, k_ids, {'state': 'deleted'}, context=context)
        return res

    def unlink_permanent(self, cr, uid, ids, context=None):
        return super(esale_joomla_category_map, self).unlink(cr, uid, ids, context=context)

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for r in self.read(cr, uid, ids, ['esale_joomla_name']):
            res.append((r['id'], r['esale_joomla_name']))
        return res

    def webimport(self, cr, uid, web_ids, context={}):
        cnew = cupdate = cerror = 0
        for website in self.pool.get('esale_joomla.web').browse(cr, uid, web_ids):
            server = _xmlrpc(website)
            try:
                #get languages
                languages = server.openerp2vm.get_languages(website.login, website.password)
                if website.language_id.code not in languages:
                    print >> sys.stderr, 'Cannot match shop language'
                    cerror += 1
                    continue
                del languages[website.language_id.code]
                context['lang'] = website.language_id.code
                #get categories
                categories = server.openerp2vm.get_categories(website.login, website.password) #id, country, state, rate
                for i in range(len(categories)):
                    categories[i][1] = _decode(categories[i][1])
                    categories[i][1] = len(categories[i][1]) > 64 and categories[i][1][0:61] + '...' or categories[i][1]
                cats = []
                for e in categories:
                    (cid, cname, cparent) = e
                    if not cid:
                        cerror += 1
                        continue
                    value = {
                        'web_id': website.id,
                        'esale_joomla_id': cid,
                        u'esale_joomla_name': cname,
                        'state': 'imported',
                    }
                    id = self.search(cr, uid, [('web_id', '=', website.id), ('esale_joomla_id', '=', cid)])
                    if not len(id):
                        id = self.create(cr, uid, value, context=context)
                        cnew += 1
                    else:
                        id = id[0]
                    for (lang_name, lang_id) in languages.iteritems():
                        try:
                            tr = server.openerp2vm.get_translation(website.login, website.password, lang_id, 'vm_category', 'category_name', cid)
                        except Exception, e:
                            print >> sys.stderr, "XMLRPC Error: %s" % e
                        else:
                            if tr[0]:
                                self.write(cr, uid, id, {u'esale_joomla_name': tr[1], 'state': 'imported'}, {'lang': lang_name})
                    cats.append([e, id])
                for (category, id) in cats:
                    (cid, cname, cparent) = category
                    value = {
                        u'esale_joomla_name': cname,
                        u'esale_joomla_parent_id': None,
                        'state': 'imported',
                    }
                    if cparent:
                        parent_id = self.search(cr, uid, [('web_id', '=', website.id), ('esale_joomla_id', '=', cparent)])
                        if not len(parent_id):
                            print >> sys.stderr, "Error while searching for parent"
                        else:
                            print "category %s/%s has parent %s/%s" % (id, cid, parent_id[0], cparent)
                            value['esale_joomla_parent_id'] = parent_id[0]
                    self.write(cr, uid, id, value, context=context)
                cupdate += len(cats)
            except (xmlrpclib.ProtocolError, xmlrpclib.ResponseError, xmlrpclib.Fault) as e:
                print >> sys.stderr, "XMLRPC Error: %s" % e
                cerror += 1
        cupdate += 0 - cnew - cerror
        self.pool.get('esale_joomla.synclog').create(cr, uid, {
            'web_id': website.id,
            'object': 'category',
            'type': 'export',
            'errors': cerror,
        })

        return (cnew, cupdate, cerror)

    def webexport(self, cr, uid, web_id, category_ids, context={}):
        cnew = cupdate = cdelete = cerror = 0
        website = self.pool.get('esale_joomla.web').browse(cr, uid, web_id)
        server = _xmlrpc(website)
        try:
            #get languages
            languages = server.openerp2vm.get_languages(website.login, website.password)
            if website.language_id.code not in languages:
                raise Exception('Cannot match shop language')
        except Exception, e:
            print >> sys.stderr, "XMLRPC Error: %s" % e
            cerror += 1
        else:
            del languages[website.language_id.code]
            context['lang'] = website.language_id.code
            #step1 : export categories and get esale_joomla_id
            categories = []
            for el in self.browse(cr, uid, category_ids, context=context):
                if el.state == 'deleted':
                    try:
                        server.openerp2vm.delete_category(website.login, website.password, el.esale_joomla_id)
                    except Exception, e:
                        print >> sys.stderr, "XMLRPC Error : %r" % e
                        cerror += 1
                    else:
                        self.unlink_permanent(cr, uid, el.id, context=context)
                        cdelete += 1
                elif not el.category_id:
                    pass
                else:
                    try:
                        eid = server.openerp2vm.set_category(website.login, website.password, {'id': el.esale_joomla_id or 0, 'name': el.esale_joomla_name, })
                        if not eid:
                            raise Exception('Failed')
                    except Exception, e:
                        cerror += 1
                        print >> sys.stderr, "XMLRPC Error : %r" % e
                        self.write(cr, uid, el.id, {'state': 'error'}, context=context)
                    else:
                        err = 0
                        for (lang_name, lang_id) in languages.iteritems():
                            tr = self.browse(cr, uid, el.id, context={'lang': lang_name})
                            try:
                                err &= server.openerp2vm.set_translation(website.login, website.password, lang_id, 'vm_category', 'category_name', eid, tr.esale_joomla_name)
                            except Exception, e:
                                print >> sys.stderr, "XMLRPC Error: %s" % e
                        if err:
                            cerror += 1
                        elif not el.esale_joomla_id:
                            cnew += 1
                        else:
                            cupdate += 1
                        self.write(cr, uid, el.id, {'esale_joomla_id': eid, 'state': 'sync'}, context=context)
                        categories.append([el, eid])
            #step2 : export parent ids
            data = []
            print 'export parents'
            for (category, eid) in categories:
                print 'eid=%s' % eid
                print 'category.esale_joomla_id=%s' % category.esale_joomla_id
                if category.esale_joomla_parent_id:
                    print "category %s/%s has parent %s/%s" % (category.id, eid, category.esale_joomla_parent_id.id, category.esale_joomla_parent_id.esale_joomla_id)
                    if not category.esale_joomla_parent_id.esale_joomla_id:
                        print >> sys.stderr, "Error while searching for parent"
                        data.append({'child': eid, 'parent': 0})
                    #elif category.esale_joomla_parent_id.web_id.id!=web_id:
                    #    print >> sys.stderr, "Error in constraint: parent id %s of rowid %s is not of the same webid"%(parent.id, category.id)
                    else:
                        data.append({'child': eid, 'parent': category.esale_joomla_parent_id.esale_joomla_id})
                else:
                    print "category %s/%s has no parent /0" % (category.id, eid)
                    data.append({'child': eid, 'parent': 0})
            try:
                server.openerp2vm.set_categories_parents(website.login, website.password, data)
            except Exception, e:
                print >> sys.stderr, "XMLRPC Error : %r" % e
        self.pool.get('esale_joomla.synclog').create(cr, uid, {
            'web_id': web_id,
            'object': 'category',
            'type': 'import',
            'errors': cerror,
        })

        return (cnew, cupdate, cdelete, cerror)

esale_joomla_category_map()


class esale_joomla_product_map(osv.osv):
    _name = "esale_joomla.product_map"
    _description = "eSale Products Mapping"

    def _status(self, cr, uid, ids, field_name, arg, context):
        res = {}
        sql = "select m.id, m.state,(p.create_date > m.export_date or p.write_date > m.export_date)"
        sql += " from esale_joomla_product_map m"
        sql += " left outer join product_product p on m.product_id=p.id"
        sql += " where m.id in (%s);" % ', '.join(map(str, ids))
        cr.execute(sql)
        for (id, state, mod) in cr.fetchall():
            if mod is None:
                res[id] = 'deleted'
            elif mod is True:
                res[id] = 'modified'
            else:
                res[id] = state
        return res

    _columns = {
        'product_id': fields.many2one('product.product', 'Product', readonly=True), #not required otherwise corresponding product cannot be deleted
        'web_id': fields.many2one('esale_joomla.web', 'Web Shop', required=True, readonly=True),
        'esale_joomla_id': fields.integer('Web ID', required=True, readonly=True),
        'state': fields.selection(STATES+[('exported', 'exported')], 'state', readonly=True),
        'status': fields.function(_status, method=True, type='selection', selection=STATES+[('exported', 'exported')], string='Status', store=False),
        'export_date': fields.datetime('Export date', readonly=True),
    }
    _defaults = {
        'export_date': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    def name_get(self, cr, uid, ids, context=None):
        return map(lambda x: (x, x), ids)

    def unlink(self, cr, uid, ids, context=None):
        #manual unlink not allowed
        return False

    def unlink_permanent(self, cr, uid, ids, context=None):
        return super(esale_joomla_product_map, self).unlink(cr, uid, ids, context=context)

    def webexport_stock(self, cr, uid, web_id, prod_ids, webcategories, context=None):
        cupdate = cerror = 0
        website = self.pool.get('esale_joomla.web').browse(cr, uid, web_id)
        product_obj = self.pool.get('product.product')
        server = _xmlrpc(website)


        #check products to export
        if not len(prod_ids):
            print >> sys.stderr, 'No products found.'
        else:
            for product in product_obj.browse(cr, uid, prod_ids, context=context):
                #id, eid
                id = self.search(cr, uid, [('web_id', '=', web_id), ('product_id', '=', product.id)])
                if len(id):
                    eid = self.browse(cr, uid, id[0]).esale_joomla_id

                    d = {
                      #vm_product
                        'id': eid,
                        'in_stock': product_obj.browse(cr, uid, product.id).qty_available,
                    }

                    try:
                        eid = server.openerp2vm.set_stock(website.login, website.password, d)
                        cupdate += 1
                        if not eid:
                            raise Exception('Failed')
                    except Exception, e:
                        print >> sys.stderr, "XMLRPC Error : %r" % e
                        cerror += 1
                        if id:
                            self.write(cr, uid, id, {'state': 'error', 'export_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
                        else:
                            self.create(cr, uid, {
                                'product_id': product.id,
                                'web_id': web_id,
                                'esale_joomla_id': 0,
                                'state': 'error',
                            }, context=context)
##                         #create/update entry in mapping table
##                         if not id:
##                             cnew += 1
##                             self.create(cr, uid, {'product_id': product.id, 'web_id': web_id, 'esale_joomla_id': eid, 'state': 'exported'}, context=context)
##                         else:
##                             cupdate += 1
##                             self.write(cr, uid, id, {'esale_joomla_id': eid, 'state': 'exported', 'export_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        self.pool.get('esale_joomla.synclog').create(cr, uid, {
            'web_id': web_id,
            'object': 'product',
            'type': 'export',
            'errors': cerror,
        })

        return (cupdate, cerror)

    def webexport_product(self, cr, uid, web_id, prod_ids, webcategories, context=None):
        def _get_tax_amount(cr, uid, tax_id):
            if isinstance(tax_id , (int, long)):
                account_tax_obj = self.pool.get('account.tax')
                tax = account_tax_obj.browse(cr, uid, tax_id)
            else:
                tax = tax_id

            if tax.child_depend and tax.child_ids:
                tax_amount = sum([t.amount for t in tax.child_ids])
            else:
                tax_amount = tax.amount

            return tax_amount
        # END _get_tax_amount

        cnew = cupdate = cdelete = cerror = 0
        website = self.pool.get('esale_joomla.web').browse(cr, uid, web_id)

        product_obj = self.pool.get('product.product')
        esale_joomla_tax_map_obj = self.pool.get('esale_joomla.tax_map')
        esale_joomla_producttype_map_obj = self.pool.get('esale_joomla.producttype_map')
        product_pricelist_obj = self.pool.get('product.pricelist')
        account_tax_obj = self.pool.get('account.tax')

        server = _xmlrpc(website)
        #delete, look missing ref in product_map table
        sql = "select m.id, m.esale_joomla_id from esale_joomla_product_map m where product_id is NULL;"
        cr.execute(sql)
        for (id, eid) in cr.fetchall():
            print 'delete %s/%s' % (id, eid)
            try:
                if server.openerp2vm.delete_product(website.login, website.password, eid):
                    cdelete += 1
            except Exception, e:
                print >> sys.stderr, "XMLRPC Error: %s" % e
            else:
                self.unlink_permanent(cr, uid, id)
        #check products to export
        if not len(prod_ids):
            print >> sys.stderr, 'No product to export'
        else:
            #get languages
            try:
                languages = server.openerp2vm.get_languages(website.login, website.password)
                if website.language_id.code not in languages:
                    raise Exception('Cannot match shop language')
            except Exception, e:
                print >> sys.stderr, "XMLRPC Error: %s" % e
                cerror += 1
            else:
                del languages[website.language_id.code]
                context['lang'] = website.language_id.code
                #pricelist
                pricelist = website.shop_id.pricelist_id.id
                if not pricelist:
                    raise except_wizard('UserError', 'You must define a pricelist in your shop !')
                #webtaxes
                webtaxes = {}
                tax_ids = esale_joomla_tax_map_obj.search(cr, uid, [('web_id', '=', web_id), ('tax_id', '!=', False), ('esale_joomla_id', '!=', 0)], context=context)
                print "tax_ids=%s" % tax_ids
                for x in esale_joomla_tax_map_obj.read(cr, uid, tax_ids, ['tax_id', 'esale_joomla_id'], context=context):
                    webtaxes[x['tax_id'][0]] = x['esale_joomla_id']
                print 'webtaxes=%r' % webtaxes
                #
                for product in product_obj.browse(cr, uid, prod_ids, context=context):
                    #id, eid
                    id = self.search(cr, uid, [('web_id', '=', web_id), ('product_id', '=', product.id)])
                    if len(id):
                        eid = self.browse(cr, uid, id[0]).esale_joomla_id
                    else:
                        eid = 0
                    if not product.active or not product.sale_ok:
                        if eid:
                            try:
                                if server.openerp2vm.delete_product(website.login, website.password, eid):
                                    self.unlink_permanent(cr, uid, id)
                            except Exception, e:
                                print >> sys.stderr, "XMLRPC Error: %s" % e
                                cerror += 1
                        continue
                    #
                    d = {
                      #vm_product
                        'id': eid,
                        'sku': product.code or '',
                        's_desc': str(product.description_sale or ''),
                        'desc': str(product.description_sale or ''),
                        'image': product.image,
                        'publish': product.online and 'Y' or 'N',
                        'weight': float(0.0),
                        #'weight_uom': '', #product.uom_id.name,
                        'length': float(0.0),
                        'width': float(0.0),
                        'height': float(0.0),
                        #'lwh_uom': '',
                        'url': '',
                        'in_stock': product_obj.browse(cr, uid, product.id).qty_available,
                        #'available_date': ,
                        #'availability': ,
                        'special': 'N',
                        #'discount_id': ,
                        'name': product.name or '',
                        #'sales': ,
                        'tax_id': 0,
                        #'unit', ,
                        'packaging': 0,
                      #vm_product_category_xref
                        'category_id': sorted([webcategories[cat.id] for cat in product.esale_category_ids]),
                      #vm_product_price
                        'price': 0,
                        'currency': 'EUR',
                      #
                        'params': {},
                    }

                    d['price'] = product_pricelist_obj.price_get(cr, uid, [pricelist], product.id, 1, 'list')[pricelist]

                    if self.pool.get('sale.order')._columns.get('price_type'):
                        # price is tax included:
                        inv_price = d['price']
                        for tax in product.taxes_id:
                            if tax.id in webtaxes and not d['tax_id']:
                                d['tax_id'] = webtaxes[tax.id]
                                inv_price = self.pool.get('account.tax').compute_inv(cr, uid, [tax], d['price'], 1)[0]['price_unit']

                        d['price'] = inv_price

                    #packaging
                    for packaging in product.packaging:
                        res = packaging.qty
                        if packaging.name in ('U.V.', 'Unité de Vente') and res != 0:
                            d['packaging'] = res
                    #parameters
                    for ptm_id in esale_joomla_producttype_map_obj.search(cr, uid, [('web_id', '=', web_id), ('category_id', '=', product.categ_id.id)], context=context):
                        ptm = esale_joomla_producttype_map_obj.browse(cr, uid, ptm_id, context=context)
                        d['params'][str(ptm.esale_joomla_id)] = {}
                        for ptpm in ptm.producttypeparam_map_ids:
                            if ptpm.attribute:
                                try:
                                    val = eval(ptpm.attribute)
                                    if val is not False:
                                        d['params'][str(ptm.esale_joomla_id)][ptpm.esale_joomla_id] = val
                                except Exception, e:
                                    print >> sys.stderr, 'Cannot evaluate parameter %s: %s' % (ptpm.esale_joomla_id, e)
                    print 'params=%r' % d['params']

                    try:
                        print 'set_product(%r)' % d
                        eid = server.openerp2vm.set_product(website.login, website.password, d)
                        if not eid:
                            raise Exception('Failed')
                    except Exception, e:
                        print >> sys.stderr, "XMLRPC Error : %r" % e
                        cerror += 1
                        if id:
                            self.write(cr, uid, id, {'state': 'error', 'export_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
                        else:
                            self.create(cr, uid, {'product_id': product.id, 'web_id': web_id, 'esale_joomla_id': 0, 'state': 'error'}, context=context)
                    else:
                        #export translations
                        err = 0
                        for (lang_name, lang_id) in languages.iteritems():
                            tr = product_obj.browse(cr, uid, product.id, context={'lang': lang_name})
                            try:
                                err &= server.openerp2vm.set_translation(website.login, website.password, lang_id, 'vm_product', 'product_s_desc', eid, str(product.description_sale or ''))
                                err &= server.openerp2vm.set_translation(website.login, website.password, lang_id, 'vm_product', 'product_desc', eid, str(product.description_sale or ''))
                            except Exception, e:
                                print >> sys.stderr, "XMLRPC Error: %s" % e
                        if err:
                            cerror += 1
                        #create/update entry in mapping table
                        if not id:
                            cnew += 1
                            self.create(cr, uid, {'product_id': product.id, 'web_id': web_id, 'esale_joomla_id': eid, 'state': 'exported'}, context=context)
                        else:
                            cupdate += 1
                            self.write(cr, uid, id, {'esale_joomla_id': eid, 'state': 'exported', 'export_date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
        self.pool.get('esale_joomla.synclog').create(cr, uid, {
            'web_id': web_id,
            'object': 'product',
            'type': 'export',
            'errors': cerror,
        })

        return (cnew, cupdate, cdelete, cerror)

esale_joomla_product_map()


class esale_joomla_producttype_map(osv.osv):
    _name = "esale_joomla.producttype_map"
    _description = "eSale Product Types Mapping"

    _columns = {
        'category_id': fields.many2one('product.category', 'Category'),
        'web_id': fields.many2one('esale_joomla.web', 'Web Shop', required=True),
        'esale_joomla_id': fields.integer('Web ID', readonly=True),
        'esale_joomla_name': fields.char('Web Product Type Name', size=64, readonly=True),
        'producttypeparam_map_ids': fields.one2many('esale_joomla.producttypeparam_map', 'producttype_map_id', 'Product Type Parameters'),
        'state': fields.selection(STATES, 'state', readonly=True, required=True),
    }
    _defaults = {
        'state': lambda *a: 'new'
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for r in self.read(cr, uid, ids):
            res.append((r['id'], r['id']))
        return res

    def webimport(self, cr, uid, web_ids, *args):
        cnew = cupdate = cerror = 0
        for website in self.pool.get('esale_joomla.web').browse(cr, uid, web_ids):
            server = _xmlrpc(website)
            try:
                types = server.openerp2vm.get_producttypes(website.login, website.password) #id, name
            except Exception, e:
                print >> sys.stderr, "XMLRPC Error: %s" % e
                cerror += 1
                continue
            for type in types:
                (cid, cname, cparams) = type
                cname = _decode(cname)
                cname = len(cname) > 64 and cname[0:61] + '...' or cname
                if not cid:
                    cerror += 1
                    continue
                value = {
                    'web_id': website.id,
                    'esale_joomla_id': cid,
                    'esale_joomla_name': cname,
                    'state': 'imported',
                }
                id = self.search(cr, uid, [('web_id', '=', website.id), ('esale_joomla_id', '=', cid)])
                if not len(id):
                    id = self.create(cr, uid, value)
                    cnew += 1
                else:
                    self.write(cr, uid, id, value)
                    id = id[0]
                    cupdate += 1
                for param in cparams:
                    (cid, cname) = param
                    cid = _decode(cid)
                    if len(cid) > 64:
                        continue #we cannot import this key
                    cname = _decode(cname)
                    cname = len(cname) > 64 and cname[0:61] + '...' or cname
                    value = {
                        'producttype_map_id': id,
                        'esale_joomla_id': cid,
                        'esale_joomla_name': cname,
                        'state': 'imported',
                    }
                    pid = self.pool.get('esale_joomla.producttypeparam_map').search(cr, uid, [('producttype_map_id', '=', id), ('esale_joomla_id', '=', cid)])
                    if not len(pid):
                        self.pool.get('esale_joomla.producttypeparam_map').create(cr, uid, value)
                    else:
                        self.pool.get('esale_joomla.producttypeparam_map').write(cr, uid, pid, value)
            self.pool.get('esale_joomla.synclog').create(cr, uid, {
                'web_id': website.id,
                'object': 'producttype',
                'type': 'import',
                'errors': cerror,
            })

        return (cnew, cupdate, cerror)

esale_joomla_producttype_map()


class esale_joomla_producttypeparam_map(osv.osv):
    _name = "esale_joomla.producttypeparam_map"
    _description = "eSale Product Type Parameters Mapping"

    _columns = {
        'attribute': fields.char('Product Attribute', size=128),
        'producttype_map_id': fields.many2one('esale_joomla.producttype_map', 'Product Type'),
        'esale_joomla_id': fields.char('Web Parameter Name', size=64, readonly=True, required=True),
        'esale_joomla_name': fields.char('Web Parameter Label', size=64, readonly=True),
        'state': fields.selection(STATES, 'state', readonly=True, required=True),
    }
    _defaults = {
        'state': lambda *a: 'new'
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for r in self.read(cr, uid, ids):
            res.append((r['id'], r['esale_joomla_id']))
        return res

esale_joomla_producttypeparam_map()

#----------------------------------------------------------------------------
#TINY part

class esale_joomla_partner(osv.osv):
    _name = 'esale_joomla.partner'
    _description = 'eShop Partner'
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'esale_id': fields.char('eSale ID', size=64),
        'address': fields.char('Address', size=128),
        'city': fields.char('City', size=64),
        'zip': fields.char('Zip', size=64),
        'country': fields.char('Country', size=64),
        'email': fields.char('Mail', size=64),
        'state': fields.char('State', size=64),
        'address_id': fields.many2one('res.partner.address', 'Partner Address'),
    }

    def address_set(self, cr, uid, ids, context={}):
        for adr in self.browse(cr, uid, ids, context):
            if adr.address_id:
                continue
            country = self.pool.get('res.country').name_search(cr, uid, adr.country)
            state = self.pool.get('res.country.state').name_search(cr, uid, adr.state)
            create_id = self.pool.get('res.partner').create(cr, uid, {
                'name': adr.name,
            })
            address_dico = {
                    'street': adr.address,
                    'partner_id': create_id,
                    'zip': adr.zip,
                    'city': adr.city,
                    'email': adr.email,
            }
            if adr.country and len(country) == 1:
                address_dico['country_id'] = country and country[0][0]
            if adr.state and len(state) == 1:
                address_dico['state_id'] = state and state[0][0]

            create_id2 = self.pool.get('res.partner.address').create(cr, uid, address_dico)

            self.write(cr, uid, [adr.id], {'address_id': create_id2})
        return True

esale_joomla_partner()


class esale_joomla_order(osv.osv):
    _name = 'esale_joomla.order'
    _columns = {
        'name': fields.char('Order Description', size=64, required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done', 'Done'),
            ('cancel', 'Cancel')
        ], 'Order State'),
        'date_order': fields.date('Date Ordered', required=True),

        'epartner_shipping_id': fields.many2one('esale_joomla.partner', 'Joomla Shipping Address', required=True),
        'epartner_invoice_id': fields.many2one('esale_joomla.partner', 'Joomla Invoice Address', required=True),

        'partner_id': fields.many2one('res.partner', 'Contact Address'),
        'partner_shipping_id': fields.many2one('res.partner.address', 'Shipping Address'),
        'partner_invoice_id': fields.many2one('res.partner.address', 'Invoice Address'),

        'web_id': fields.many2one('esale_joomla.web', 'Web Shop', required=True),
        'web_ref': fields.integer('Web Ref'),

        'order_lines': fields.one2many('esale_joomla.order.line', 'order_id', 'Order Lines'),
        'order_id': fields.many2one('sale.order', 'Sale Order'),
        'note': fields.text('Notes'),
    }

    _defaults = {
        'date_order': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a: 'draft',
    }

    def webimport(self, cr, uid, web_ids, *args):
        cnew = cupdate = cerror = 0
        for website in self.pool.get('esale_joomla.web').browse(cr, uid, web_ids):
            server = _xmlrpc(website)
            try:
                orders = server.openerp2vm.get_orders(website.login, website.password) #id, name
            except Exception, e:
                print >> sys.stderr, "XMLRPC Error: %s" % e
                cerror += 1
                continue
            for order in orders:
                (cid, cname, cparams) = order
                cname = _decode(cname)
                cname = len(cname) > 64 and cname[0:61] + '...' or cname
                if not cid:
                    cerror += 1
                    continue
                value = {
                    'web_id': website.id,
                    'esale_joomla_id': cid,
                    'esale_joomla_name': cname,
                    'state': 'imported',
                }
                id = self.search(cr, uid, [('web_id', '=', website.id), ('esale_joomla_id', '=', cid)])
                if not len(id):
                    id = self.create(cr, uid, value)
                    cnew += 1
                else:
                    self.write(cr, uid, id, value)
                    id = id[0]
                    cupdate += 1
                for param in cparams:
                    (cid, cname) = param
                    cid = _decode(cid)
                    if len(cid) > 64:
                        continue #we cannot import this key
                    cname = _decode(cname)
                    cname = len(cname) > 64 and cname[0:61] + '...' or cname
                    value = {
                        'producttype_map_id': id,
                        'esale_joomla_id': cid,
                        'esale_joomla_name': cname,
                        'state': 'imported',
                    }
                    pid = self.pool.get('esale_joomla.producttypeparam_map').search(cr, uid, [('producttype_map_id', '=', id), ('esale_joomla_id', '=', cid)])
                    if not len(pid):
                        self.pool.get('esale_joomla.producttypeparam_map').create(cr, uid, value)
                    else:
                        self.pool.get('esale_joomla.producttypeparam_map').write(cr, uid, pid, value)
            self.pool.get('esale_joomla.synclog').create(cr, uid, {
                'web_id': website.id,
                'object': 'producttype',
                'type': 'import',
                'errors': cerror,
            })

        return (cnew, cupdate, cerror)

    def order_create(self, cr, uid, ids, context={}):
        for order in self.browse(cr, uid, ids, context):
            if not (order.partner_id and order.partner_invoice_id and order.partner_shipping_id):
                raise osv.except_osv('No addresses !', 'You must assign addresses before creating the order.')
            #pricelist_id=order.partner_id.property_product_pricelist[0]
            pricelist_id = order.partner_id.property_product_pricelist.id
            order_lines = []
            for line in order.order_lines:
                val = {
                    'name': line.name,
                    'product_uom_qty': line.product_qty,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom_id.id,
                    'price_unit': line.price_unit,
                }
                fpos = order.partner_id.property_account_position and order.partner_id.property_account_position.id or False
                val_new = self.pool.get('sale.order.line').product_id_change(cr, uid, None, pricelist_id, line.product_id.id, line.product_qty,
                                                                             line.product_uom_id.id, name=line.name, partner_id=order.partner_id.id, fiscal_position=fpos)['value']
                del val_new['price_unit']
                #del val_new['weight']
                del val_new['th_weight']
                val_new['product_uos'] = 'product_uos' in val_new and val_new['product_uos'] and val_new['product_uos'][0] or False
                val.update(val_new)
                val['tax_id'] = 'tax_id' in val and [(6, 0, val['tax_id'])] or False
                order_lines.append((0, 0, val))

            order_id = self.pool.get('sale.order').create(cr, uid, {
                'name': order.name,
                'shop_id': order.web_id.shop_id.id,
                'origin': 'WEB:' + str(order.web_ref),
                'user_id': uid,
                'note': order.note or '',
                'partner_id': order.partner_id.id,
                'partner_invoice_id': order.partner_invoice_id.id,
                'partner_order_id': order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'pricelist_id': pricelist_id,
                'order_line': order_lines,
                'fiscal_position': order.partner_id.property_account_position.id
            })
            self.write(cr, uid, [order.id], {'state': 'done', 'order_id': order_id})
#           wf_service = netsvc.LocalService("workflow")
#           wf_service.trg_validate(uid, 'sale.order', order_id, 'order_confirm', cr)
        return True

    def address_set(self, cr, uid, ids, *args):
        done = []
        for order in self.browse(cr, uid, ids):
            for idn in [order.epartner_shipping_id.id, order.epartner_invoice_id.id]:
                if idn not in done:
                    done.append(idn)
                    self.pool.get('esale_joomla.partner').address_set(cr, uid, [idn])
            self.write(cr, uid, [order.id], {
                'partner_shipping_id': order.epartner_invoice_id.address_id.id,
                'partner_id': order.epartner_invoice_id.address_id.partner_id.id,
                'partner_invoice_id': order.epartner_shipping_id.address_id.id,

            })
        return True

    def order_cancel(self, cr, uid, ids, context={}):
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

esale_joomla_order()


class esale_joomla_order_line(osv.osv):
    _name = 'esale_joomla.order.line'
    _description = 'eSale Order line'
    _columns = {
        'name': fields.char('Order Line', size=64, required=True),
        'order_id': fields.many2one('esale_joomla.order', 'eOrder Ref'),
        'product_qty': fields.float('Quantity', digits=(16, 2), required=True),
        'product_id': fields.many2one('product.product', 'Product', domain=[('sale_ok', '=', True)], change_default=True),
        'product_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'price_unit': fields.float('Unit Price', digits=(16, int(config['price_accuracy'])), required=True),
    }
    _defaults = {
    }

esale_joomla_order_line()

