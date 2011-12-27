# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Zikzakmedia. (http://zikzakmedia.com) All Rights Reserved.
#                    Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright (c) 2011 ToolPart Team LLC (http://toolpart.hu)
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

from report.interface import report_rml

import pooler

class report_custom(report_rml):
    def get_partner_ids(self, cr, uid, model, ids):
        '''
        Returns the partners associated to the given model instances.

        Currently supports:
            * res.partner
            * res.partner.address
            * account.invoice
            * sale.order
        (actually it supports res.partner + every model that connects to
        it using a foreign key called partner_id)

        :param model: the _name of the model to start from
        :param ids: a list of ids of the model
        :returns: a list of ids of partners
        '''
        if model == 'res.partner':
            return ids

        pool = pooler.get_pool(cr.dbname)
        obj = pool.get(model)
        return map(lambda x: x['partner_id'], obj.read(cr, uid, ids, ['partner_id'], load='_classic_write'))

    def create_xml(self, cr, uid, ids, data, context):
        # Adding report data
        report_xml = '''
    <page_width>%s</page_width>
    <page_height>%s</page_height>
    <rows>%s</rows>
    <cols>%s</cols>
    <label_width>%s</label_width>
    <label_height>%s</label_height>
    <width_incr>%s</width_incr>
    <height_incr>%s</height_incr>
    <initial_bottom_pos>%s</initial_bottom_pos>
    <initial_left_pos>%s</initial_left_pos>
    <font_type>%s</font_type>
    <font_size>%s</font_size>
    <printer_top>%s</printer_top>
    <printer_bottom>%s</printer_bottom>
    <printer_left>%s</printer_left>
    <printer_right>%s</printer_right>''' % (
            data['page_width'],
            data['page_height'],
            data['rows'],
            data['cols'],
            data['label_width'],
            data['label_height'],
            data['width_incr'],
            data['height_incr'],
            data['initial_bottom_pos'],
            data['initial_left_pos'],
            data['font_type'],
            data['font_size'],
            data['printer_top'],
            data['printer_bottom'],
            data['printer_left'],
            data['printer_right']
        )

        # Adding empty labels
        info_xml = '\n'
        for i in range((data['first_row']-1) * data['cols'] + data['first_col']-1):
            info_xml += '<address>\n'
            info_xml += '    <company-title/>\n'
            info_xml += '    <company-name/>\n'
            info_xml += '    <contact>\n'
            info_xml += '        <type/>\n'
            info_xml += '        <title/>\n'
            info_xml += '        <name/>\n'
            info_xml += '        <street/>\n'
            info_xml += '        <street2/>\n'
            info_xml += '        <zip/>\n'
            info_xml += '        <city/>\n'
            info_xml += '        <state/>\n'
            info_xml += '        <country/>\n'
            info_xml += '    </contact>\n'
            info_xml += '</address>\n'

        # Adding partner labels
        pool = pooler.get_pool(cr.dbname)
        addr_type = context.get('address_type', 'contact')
        partner_ids = self.get_partner_ids(cr, uid, context.get('active_model', 'res.partner'), context['active_ids'])
        for partner_id in partner_ids:
            addr_ids = pool.get('res.partner').address_get(cr, uid, [partner_id], adr_pref=[addr_type])[addr_type]
            address = pool.get('res.partner.address').browse(cr, uid, addr_ids)
            info_xml += '<address>\n'
            info_xml += '    <company-title>%s</company-title>\n' % (address.partner_id.title or '')
            info_xml += '    <company-name>%s</company-name>\n' % (address.partner_id.name or '')
            info_xml += '    <contact>\n'
            info_xml += '        <type>%s</type>\n' % (address.type or '')
            info_xml += '        <title>%s</title>\n' % (address.title or '')
            info_xml += '        <name>%s</name>\n' % (address.name or '')
            info_xml += '        <street>%s</street>\n' % (address.street or '')
            info_xml += '        <street2>%s</street2>\n' % (address.street2 or '')
            info_xml += '        <zip>%s</zip>\n' % (address.zip or '')
            info_xml += '        <city>%s</city>\n' % (address.city or '')
            info_xml += '        <state>%s</state>\n' % (address.state_id and address.state_id.name) or ''
            info_xml += '        <country>%s</country>\n' % (address.country_id and address.country_id.name) or ''
            info_xml += '    </contact>\n'
            info_xml += '</address>\n'

        # Computing the xml
        xml='''<?xml version="1.0" encoding="UTF-8" ?>
<addresses>%s%s</addresses>''' % (report_xml, info_xml)
        #print xml

        return xml

report_custom('report.res.partner.address.label', 'res.partner', '', 'addons/label/report/partner_address.xsl')
