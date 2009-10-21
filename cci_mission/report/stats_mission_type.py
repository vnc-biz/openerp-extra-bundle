# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import time

from report import report_sxw

class stats_mission_type(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(stats_mission_type, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'time': time,
            'get_missions': self._get_missions,
            'get_missions_total': self._get_missions_total,
            'get_missions_total1':self._get_missions_total1,
            'get_missions_total2':self._get_missions_total2,
            'get_missions_total3':self._get_missions_total3
        })

    def _get_missions(self, d1, d2):
            self.cr.execute('select t.section, count(t.id) as no_certi, sum(goods_value) as no_goods,  \
                            sum(sub_total) as total_sub, type_id, t.name  \
                            from cci_missions_dossier as d,cci_missions_dossier_type as t \
                            where d.type_id=t.id  group by type_id,t.name,t.section, t.id')
            res_ata = self.cr.dictfetchall()

            self.cr.execute('select t.section, count(t.id) as no_certi, sum(goods_value) as no_goods,  \
                            sum(sub_total) as total_sub, type_id, t.name  \
                            from cci_missions_ata_carnet as d,cci_missions_dossier_type as t \
                            where d.type_id=t.id  group by type_id,t.name,t.section, t.id')
            res_ata1 = self.cr.dictfetchall()

            self.cr.execute('select count(e.id) as no_certi, sum(l.customer_amount) as total_sub, s.name\
                    from cci_missions_embassy_folder as e \
                    left join cci_missions_embassy_folder_line as l \
                    on e.id=l.folder_id \
                    left join cci_missions_site as s \
                     on s.id=e.site_id group by s.name' )
            res_ata2 = self.cr.dictfetchall()

            temp_list = []
            for i in res_ata2:
                i.update({'section':'folder'})
                temp_list.append(i)
            return res_ata + res_ata1 + temp_list

    def _get_missions_total(self,d1,d2):
            self.cr.execute('select t.section, count(t.id) as no_certi, sum(goods_value) as no_goods, \
                            sum(sub_total) as total_sub \
                             from cci_missions_dossier as d,cci_missions_dossier_type as t \
                            where d.type_id=t.id  and t.section=\'certificate\' group by t.section' )
            res_ata = self.cr.dictfetchall()
            return res_ata

    def _get_missions_total1(self, d1, d2):
            self.cr.execute('select t.section, count(t.id) as no_certi, sum(goods_value) as no_goods, \
                            sum(sub_total) as total_sub \
                             from cci_missions_dossier as d,cci_missions_dossier_type as t \
                            where d.type_id=t.id  and t.section=\'legalization\' group by t.section' )
            res_ata = self.cr.dictfetchall()
            return res_ata

    def _get_missions_total2(self, d1, d2):
            self.cr.execute('select t.section, count(t.id) as no_certi, sum(goods_value) as no_goods, \
                            sum(sub_total) as total_sub \
                             from cci_missions_ata_carnet as d,cci_missions_dossier_type as t \
                            where d.type_id=t.id  and t.section=\'ATA\' group by t.section' )
            res_ata = self.cr.dictfetchall()
            return res_ata

    def _get_missions_total3(self, d1, d2):
            self.cr.execute('select count(e.id) as no_certi, sum(l.customer_amount) as total_sub  \
                            from cci_missions_embassy_folder as e left join cci_missions_embassy_folder_line as l \
                            on e.id=l.folder_id \
                            left join cci_missions_site as s \
                            on s.id=e.site_id')
            res_ata = self.cr.dictfetchall()
            return res_ata

report_sxw.report_sxw('report.stats.mission.type', 'cci_missions.certificate', 'addons/cci_mission/report/stats_mission_type.rml', parser=stats_mission_type, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: