# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

from osv import osv
from osv import fields
from tools.translate import _

def size2cm(text):
    """Converts the size text ended with 'cm' or 'in' to the numeric value in cm and returns it"""
    if text:
        if text[-2:] == "cm":
            return float(text[:-2])
        elif text[-2:] == "in":
            return float(text[:-2]) * 2.54
    return 0

class label_wizard(osv.osv_memory):
    _name = 'res.partner.label'
    _description = 'Label printing wizard'

    _columns = {
        'label_format': fields.many2one('report.label', _('Label Format'), required=True),
        'printer_top': fields.char(_('Top'), size=20, help="Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in"),
        'printer_bottom': fields.char(_('Bottom'), size=20, help="Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in"),
        'printer_left': fields.char(_('Left'), size=20, help="Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in"),
        'printer_right': fields.char(_('Right'), size=20, help="Numeric size ended with the unit (cm or in). For example, 0.3cm or 0.2in"),
        'font_type': fields.selection([('Times-Roman','Times-Roman'),('Times-Bold','Times-Bold'),('Times-Italic','Times-Italic'),('Times-BoldItalic','Times-BoldItalic'),('Helvetica','Helvetica'),('Helvetica-Bold','Helvetica-Bold'),('Helvetica-Oblique','Helvetica-Oblique'),('Helvetica-BoldOblique','Helvetica-BoldOblique'),('Courier','Courier'),('Courier-Bold','Courier-Bold'),('Courier-Oblique','Courier-Oblique'),('Courier-BoldOblique','Courier-BoldOblique')],
                                      _('Font Type'), required=True),
        'font_size': fields.selection([('6','6'),('7','7'),('8','8'),('9','9'),('10','10'),('11','11'),('12','12'),('14','14'),],
                                      _('Font Size'), required=True),
        'first_row': fields.integer(_('First Row'), help='The Row of the first label in the first page'),
        'first_col': fields.integer(_('First Column'), help='The Column of the first label in the first page'),
        'rows': fields.related('label_format', 'rows', type='integer', string=_('#rows'), ),
        'cols': fields.related('label_format', 'cols', type='integer', string=_('#columns'), ),
        'page_width': fields.float(_('page width'), ),
        'page_height': fields.float(_('page height'), ),
        'label_width': fields.related('label_format', 'label_width', type='char', string=_('Label width'), ),
        'label_height': fields.related('label_format', 'label_height', type='char', string=_('Label height'), ),
        'width_incr': fields.related('label_format', 'width_incr', type='char', string=_('Width increment'), ),
        'height_incr': fields.related('label_format', 'height_incr', type='char', string=_('height increment'), ),
        'landscape': fields.related('label_format', 'landscape', type='boolean', string=_('Lanscape'), ),
        'initial_left_pos': fields.related('label_format', 'margin_left', type='char', string=_('Initial Left Margin'), ),
        'initial_bottom_pos': fields.float(_('Initial bottom Margin'), ),
    }
    _defaults = {
        'font_type': 'Helvetica',
        'font_size': '8',
        'first_row': 1,
        'first_col': 1,
    }

    #_constraints = [
        #(_top_margin_height, "Printer top margin bigger than (top label margin + label height). Try again.", ['printer_top']),
        #(_bottom_margin_height, "Printer bottom margin bigger than (bottom label margin + label height). Try again.", ['printer_bottom']),
        #(_left_margin_height, "Printer left margin bigger than (left label margin + label height). Try again.", ['printer_left']),
        #(_right_margin_height, "Printer right margin bigger than (right label margin + label height). Try again.", ['printer_right']),
    #]

    def create(self, cr, uid, data, context=None):
        label_obj = self.pool.get('report.label')
        label = label_obj.browse(cr, uid, data['label_format'], context)
        data['page_width'] = size2cm(label.landscape and label.pagesize_id.height or label.pagesize_id.width)
        data['page_height'] = size2cm(label.landscape and label.pagesize_id.width or label.pagesize_id.height)
        mtop = size2cm(label.margin_top)
        data['initial_bottom_pos'] = data['page_height'] - mtop - size2cm(label.label_height)
        return super(label_wizard, self).create(cr, uid, data, context)

    def do_print(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context=context)[0]
        for f in ['printer_top', 'printer_bottom', 'printer_left', 'printer_right',
                  'label_width', 'label_height', 'width_incr', 'height_incr',
                  'initial_left_pos']:
            data[f] = size2cm(data[f])

        return {'type': 'ir.actions.report.xml',
                'report_name': 'res.partner.address.label',
                'datas': data,
                'context': context,
                'nodestroy': True}

label_wizard()

