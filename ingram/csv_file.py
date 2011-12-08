# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
#                       Raimon Esteve <resteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from osv import osv, fields
from tools.translate import _

import re

class csv_file(osv.osv):
    _inherit = 'csv.file'

    def cyr2lat(self, string):
        value = ""

        cylyric_conversion = {
            u'а' : 'a',
            u'б' : 'b',
            u'в' : 'v',
            u'г' : 'g',
            u'д' : 'd',
            u'е' : 'e',
            u'ё' : 'e',
            u'ж' : 'zh',
            u'з' : 'z',
            u'и' : 'i',
            u'й' : 'j',
            u'к' : 'k',
            u'л' : 'l',
            u'м' : 'm',
            u'н' : 'n',
            u'о' : 'o',
            u'п' : 'p',
            u'р' : 'r',
            u'с' : 's',
            u'т' : 't',
            u'у' : 'u',
            u'ф' : 'f',
            u'х' : 'h',
            u'ц' : 'c',
            u'ч' : 'ch',
            u'ш' : 'sh',
            u'щ' : 'sch',
            u'ь' : "'",
            u'ы' : 'y',
            u'ь' : "'",
            u'э' : 'e',
            u'ю' : 'ju',
            u'я' : 'ja',
            u'А' : 'A',
            u'Б' : 'B',
            u'В' : 'V',
            u'Г' : 'G',
            u'Д' : 'D',
            u'Е' : 'E',
            u'Ё' : 'E',
            u'Ж' : 'ZH',
            u'З' : 'Z',
            u'И' : 'I',
            u'Й' : 'J',
            u'К' : 'K',
            u'Л' : 'L',
            u'М' : 'M',
            u'Н' : 'N',
            u'О' : 'O',
            u'П' : 'P',
            u'Р' : 'R',
            u'С' : 'S',
            u'Т' : 'T',
            u'У' : 'U',
            u'Ф' : 'F',
            u'Х' : 'H',
            u'Ц' : 'C',
            u'Ч' : 'CH',
            u'Ш' : 'SH',
            u'Щ' : 'SCH',
            u'Ъ' : "'",
            u'Ы' : 'Y',
            u'Ь' : "'",
            u'Э' : 'E',
            u'Ю' : 'JU',
            u'Я' : 'JA',
        }

        try:
            value = cylyric_conversion[string]
        except KeyError:
            value = re.sub(r'\W+', ' ', string)

        return value

csv_file()

class csv_file_field(osv.osv):
    _inherit = 'csv.file.field'

    _columns = {
		'ingram_id': fields.boolean('Ingram ID', help="Identification Ingram CSV"),
    }

csv_file_field()
