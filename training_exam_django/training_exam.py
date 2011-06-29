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

class exam_questionnaire(osv.osv):
    _inherit = 'training.exam.questionnaire'

    _columns = {
        'alias': fields.char('Alias', size=64, required=True, help="Alias Web service"),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription'),
    }

    def onchange_name(self, cr, uid, ids, name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

    def create(self, cr, uid, vals, context=None):
        vals['alias'] = slugify(unicode(vals['alias'],'UTF-8'))

        return super(exam_questionnaire, self).create(cr, uid, vals, context)

    def write(self, cr, uid, ids, vals, context=None):
        if 'alias' in vals:
            vals['alias'] = slugify(unicode(vals['alias'],'UTF-8'))

        return super(exam_questionnaire, self).write(cr, uid, ids, vals, context)

exam_questionnaire()
