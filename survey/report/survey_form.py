# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import pooler
from report.interface import report_rml

class survey_form(report_rml):
    def create(self, cr, uid, ids, datas, context):
        rml=''
        surv_obj = pooler.get_pool(cr.dbname).get('survey')
        for survey in surv_obj.browse(cr,uid,ids):
            rml="""
            <document filename="Survey Form.pdf">
            <template pageSize="(1120.5,767.8)" title="Survey Form" author="Martin Simon" allowSplitting="20" >
                <pageTemplate id="first">
                    <frame id="first" x1="22.0" y1="31.0" width="1080" height="680"/>
                </pageTemplate>
            </template>
            <stylesheet>
                <blockTableStyle id="ans_tbl">
                  <blockAlignment value="LEFT"/>
                  <blockValign value="TOP"/>
                  <lineStyle kind="LINEBELOW" colorName="#e6e6e6" start="0,0" stop="-1,-1"/>
                </blockTableStyle>
                <blockTableStyle id="page_tbl">
                  <blockFont name="Helvetica-BoldOblique" size="18" start="0,0" stop="-1,-1"/>
                  <blockBackground colorName="gray" start="0,0" stop="-1,-1"/>
                  <blockTextColor colorName="white" start="0,0" stop="0,0"/>
                  <blockAlignment value="LEFT"/>
                  <blockValign value="TOP"/>
                  <lineStyle kind="LINEBELOW" colorName="#000000" start="0,-1" stop="1,-1"/>
                </blockTableStyle>
                <blockTableStyle id="question_tbl">
                  <blockAlignment value="LEFT"/>
                  <blockValign value="TOP"/>
                  <lineStyle kind="LINEBELOW" colorName="#8f8f8f" start="0,-1" stop="1,-1"/>
                </blockTableStyle>
                <initialize>
                  <paraStyle name="all" alignment="justify"/>
                </initialize>
                <paraStyle name="P1" fontName="helvetica"/>
                <paraStyle name="Standard1" fontName="helvetica-bold" alignment="RIGHT" fontSize="09.0"/>
                <paraStyle name="Standard" alignment="LEFT" fontName="Helvetica-Bold" fontSize="11.0" />
                <paraStyle name="header1" fontName="Helvetica" fontSize="11.0"/>
                <paraStyle name="Standard2" fontName="Helvetica-bold" fontSize="11.0"/>
                <paraStyle name="response" fontName="Helvetica-oblique" fontSize="9.5"/>
                <paraStyle name="page" fontName="helvetica-bold" fontSize="15.0" leftIndent="0.0" textColor="white"/>
                <paraStyle name="question" fontName="helvetica-boldoblique" fontSize="10.0" leftIndent="3.0"/>
                <paraStyle name="answer" fontName="helvetica" fontSize="09.0" leftIndent="2.0"/>
                <paraStyle name="Heading" fontName="Helvetica" fontSize="14.0" leading="17" spaceBefore="12.0" spaceAfter="6.0"/>
                <paraStyle name="P2" fontName="Helvetica" fontSize="14.0" leading="15" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="Text body" fontName="helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="List" fontName="helvetica" spaceBefore="0.0" spaceAfter="6.0"/>
                <paraStyle name="Caption" fontName="helvetica" fontSize="12.0" leading="15" spaceBefore="6.0" spaceAfter="6.0"/>
                <paraStyle name="Title" fontName="helvetica" fontSize="20.0" leading="15" spaceBefore="6.0" spaceAfter="6.0" alignment="CENTER"/>
                <paraStyle name="Index" fontName="helvetica"/>
                <paraStyle name="Table Contents" fontName="helvetica"/>
            </stylesheet>
            <story>"""
            for page in survey.page_ids:
                rml += """
                <para style="P2"><font></font></para>
                <blockTable colWidths="1000.0" style="page_tbl">
                    <tr><td><para style="page"><seq/>. """ + page.title + """</para></td></tr>
                </blockTable>"""
                for que in page.question_ids:
                    cols_widhts=[]
                    rml +="""
                    <para style="P2"><font></font></para>
                    <blockTable colWidths="1000.0" style="question_tbl">
                        <tr><td><para style="question">Que: """+ que.question + """</para></td></tr>
                    </blockTable>
                    <para style="P2"><font></font></para>"""
                    if que.type in ['multiple_choice_multiple_ans','multiple_choice_only_one_ans']:
                        answer=[]
                        for ans in que.answer_choice_ids:
                            answer.append(str((ans.answer.replace('&','&amp;')).replace('<','below')))

                        def divide_list(lst, n):
                            return [lst[i::n] for i in range(n)]

                        rows = 5
                        divide_list = divide_list(answer,rows)
                        for lst in divide_list:
                            if que.type == 'multiple_choice_multiple_ans':
                                if len(lst)<>0 and len(lst)<>int(round(float(len(answer))/rows,0)):
                                   lst.append('')
                            if not lst:
                               del divide_list[divide_list.index(lst):]

                        for divide in divide_list:
                            a = 20*len(divide)
                            b = 1000 - a
                            cols_widhts=[]
                            for div in range(0,len(divide)):
                                cols_widhts.append(float(a/len(divide)))
                                cols_widhts.append(float(b/len(divide)))
                            colWidths = ",".join(map(str, cols_widhts))
                            rml+="""<blockTable colWidths=" """ + colWidths + """ " style="ans_tbl">
                                        <tr>"""
                            for div in range(0,len(divide)):
                               if divide[div]!='':
                                   if que.type == 'multiple_choice_multiple_ans':

                                           rml+="""
                                           <td>
                                               <illustration>
                                                   <rect x="0.1cm" y="-0.4cm" width="0.5 cm" height="0.5cm" fill="no" stroke="yes"/>
                                                </illustration>
                                           </td>
                                           <td><para style="answer">""" + divide[div] + """</para></td>"""

                                   else:
                                       rml+="""
                                       <td>
                                           <illustration>
                                               <circle x="0.3cm" y="-0.18cm" radius="0.23 cm" fill="no" stroke="yes"/>
                                            </illustration>
                                       </td>
                                       <td><para style="answer">""" + divide[div] + """</para></td>"""
                               else:
                                   rml+="""
                                   <td></td>
                                   <td></td>"""
                            rml+="""
                            </tr></blockTable>"""
                    elif que.type in ['matrix_of_choices_only_one_ans','matrix_of_choices_only_multi_ans']:
                        if len(que.column_heading_ids):
                            cols_widhts.append(600)
                            for col in que.column_heading_ids:
                                cols_widhts.append(float(400/len(que.column_heading_ids)))
                        else:
                            cols_widhts.append(1000.0)
                        colWidths = ",".join(map(str, cols_widhts))
                        matrix_ans = ['',]
                        for col in que.column_heading_ids:
                            if col.title not in matrix_ans:
                                matrix_ans.append(col.title)
                        rml+="""
                        <blockTable colWidths=" """ + colWidths + """ " style="ans_tbl">
                            <tr>"""
                        for mat_col in matrix_ans:
                            rml+="""
                            <td><para style="response">""" + mat_col + """</para></td>"""
                        rml+="""</tr>"""
                        for ans in que.answer_choice_ids:
                            rml+= """<tr>"""
                            rml+="""<td><para style="answer">""" + str(ans.answer.replace('&','&amp;')) + """</para></td>"""
                            for mat_col in range(1,len(matrix_ans)):
                                rml+="""
                                <td>
                                    <illustration>
                                        <rect x="0.25cm" y="-0.5cm" width="0.8 cm" height="0.5cm" fill="no" stroke="yes" round="0.1cm"/>
                                    </illustration>
                                </td>"""
                            rml+= """</tr>"""
                        rml+="""</blockTable>"""
                    else:
                        cols_widhts.append(1000.00)
                        colWidths = ",".join(map(str, cols_widhts))
                        rml+="""
                        <para style="P2"><font color="white"> </font></para>
                        <blockTable colWidths=" """ + colWidths + """ " style="ans_tbl">
                            <tr>
                                <td>
                                    <illustration>
                                        <rect x="0.2cm" y="0.3cm" width="15.0 cm" height="0.6cm" fill="no" stroke="yes"/>
                                    </illustration>
                                </td>
                            </tr>
                        </blockTable>
                        """
                rml+="""<pageBreak/>"""
        rml+="""</story></document>"""
        report_type = datas.get('report_type', 'pdf')
        create_doc = self.generators[report_type]
        pdf = create_doc(rml, title=self.title)
        return (pdf, report_type)
survey_form('report.survey.form', 'survey','','')