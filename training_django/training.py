# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2011 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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
############################################################################################

from osv import osv, fields
from tools.translate import _
import re
import unicodedata
import netsvc

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

class training_course(osv.osv):
    _inherit = 'training.course'

    _columns = {
        'long_name' : fields.char('Long Name', size=256, select=1, help='Allows to show the long name of the course for the external view', required=True),
        'alias': fields.char('Alias', size=256, required=True),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription', required=True),
    }

    def onchange_longName(self, cr, uid, ids, long_name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(long_name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

training_course()

class training_offer(osv.osv):
    _inherit = 'training.offer'

    _columns = {
        'alias': fields.char('Alias', size=64),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription'),
        'frontpage' : fields.boolean('Front Page', help='Show this offer at Front Page'),
        'active' : fields.boolean('Active'),
    }

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}

        result = super(training_offer, self).create(cr, uid, vals, context)

        if 'alias' not in vals:
            alias = slugify(unicode(vals['name']))
            slugs = self.search(cr, uid, [('alias','=', alias)])
            if len(slugs)>0:
                alias = alias+'-%s' % (len(slugs))
            self.write(cr, uid, result, {'alias':alias})

        return result

    def onchange_name(self, cr, uid, ids, name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

    _defaults = {
        'active' : lambda *a: 'true',
    }

training_offer()

class training_session(osv.osv):
    _inherit = 'training.session'

    _columns = {
        'alias': fields.char('Alias', size=64, required=True),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription'),
    }

    def onchange_name(self, cr, uid, ids, name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

training_session()
