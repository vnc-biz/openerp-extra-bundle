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
from tools import to_xml

class survey_form(report_rml):
    def create(self, cr, uid, ids, datas, context):

        _divide_columns_for_matrix = 0.7
        _display_ans_in_rows = 5

        if datas['form']['orientation']=='vertical':
            if datas['form']['paper_size']=='letter':
                _pageSize = ('21.6cm','27.9cm')
            elif datas['form']['paper_size']=='legal':
                _pageSize = ('21.6cm','35.6cm')
            elif datas['form']['paper_size']=='a4':
                _pageSize = ('21.1cm','29.7cm')
        elif datas['form']['orientation']=='horizontal':
            if datas['form']['paper_size']=='letter':
                _pageSize = ('27.9cm','21.6cm')
            elif datas['form']['paper_size']=='legal':
                _pageSize = ('35.6cm','21.6cm')
            elif datas['form']['paper_size']=='a4':
                _pageSize = ('29.7cm','21.1cm')

        _frame_width = str(_pageSize[0])
        _frame_height = str(float(_pageSize[1].replace('cm','')) - float(2.50))+'cm'
        _tbl_widths = str(float(_pageSize[0].replace('cm','')) - float(2.10))+'cm'

        rml=''
        surv_obj = pooler.get_pool(cr.dbname).get('survey')
        for survey in surv_obj.browse(cr,uid,ids):
            rml="""
            <document filename="Survey Form.pdf">
            <template pageSize="("""+_pageSize[0]+""","""+_pageSize[1]+""")" title="Survey Form" author="Martin Simon" allowSplitting="20" >
                <pageTemplate id="first">
                    <frame id="first" x1="0.0cm" y1="1.0cm" width='"""+_frame_width+"""' height='"""+_frame_height+"""'/>
                    <pageGraphics>
                        <lineMode width="1.0"/>
                        <lines>1.0cm """+str(float(_pageSize[1].replace('cm','')) - float(1.65))+'cm'+""" """+str(float(_pageSize[0].replace('cm','')) - float(1.00))+'cm'+""" """+str(float(_pageSize[1].replace('cm','')) - float(1.65))+'cm'+"""</lines>
                        <lines>1.0cm """+str(float(_pageSize[1].replace('cm','')) - float(1.65))+'cm'+""" 1.0cm 1.00cm</lines>
                        <lines>"""+str(float(_pageSize[0].replace('cm','')) - float(1.00))+'cm'+""" """+str(float(_pageSize[1].replace('cm','')) - float(1.65))+'cm'+""" """+str(float(_pageSize[0].replace('cm','')) - float(1.00))+'cm'+""" 1.00cm</lines>
                        <lines>1.0cm 1.00cm """+str(float(_pageSize[0].replace('cm','')) - float(1.00))+'cm'+""" 1.00cm</lines>"""
            if datas['form']['page_number']:
                rml +="""
                <fill color="gray"/>
                <setFont name="Helvetica" size="10"/>
                <drawRightString x='"""+str(float(_pageSize[0].replace('cm','')) - float(1.00))+'cm'+"""' y="0.6cm">Page : <pageNumber/> </drawRightString>"""
            rml +="""
            </pageGraphics>
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
                <blockTableStyle id="title_tbl">
                  <blockFont name="Helvetica-BoldOblique" size="18" start="0,0" stop="-1,-1"/>
                  <blockBackground colorName="black" start="0,0" stop="-1,-1"/>
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
                <paraStyle name="title" fontName="helvetica-bold" fontSize="18.0" leftIndent="0.0" textColor="white"/>
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
            <story>
            """
            if datas['form']['survey_title']:
                    rml += """
                    <blockTable colWidths='"""+_tbl_widths+"""' style="title_tbl">
                        <tr><td><para style="title">""" + to_xml(survey.title) + """</para><para style="P2"><font></font></para></td></tr>
                    </blockTable>"""
            seq = 0
            for page in survey.page_ids:
                seq+=1
                rml += """
                <blockTable colWidths='"""+_tbl_widths+"""' style="page_tbl">
                    <tr><td><para style="page">"""+ str(seq) + """. """ + to_xml(page.title) + """</para></td></tr>
                </blockTable>"""
                for que in page.question_ids:
                    cols_widhts=[]
                    rml +="""
                    <para style="P2"><font></font></para>
                    <blockTable colWidths='"""+_tbl_widths+"""' style="question_tbl">
                        <tr><td><para style="question">Que: """+ to_xml(que.question) + """</para></td></tr>
                    </blockTable>
                    <para style="P2"><font></font></para>"""
                    if que.type in ['multiple_choice_multiple_ans','multiple_choice_only_one_ans']:
                        answer=[]
                        for ans in que.answer_choice_ids:
                            answer.append(to_xml(str((ans.answer))))

                        def divide_list(lst, n):
                            return [lst[i::n] for i in range(n)]

                        divide_list = divide_list(answer,_display_ans_in_rows)
                        for lst in divide_list:
                            if que.type == 'multiple_choice_multiple_ans':
                                if len(lst)<>0 and len(lst)<>int(round(float(len(answer))/_display_ans_in_rows,0)):
                                   lst.append('')
                            if not lst:
                               del divide_list[divide_list.index(lst):]

                        for divide in divide_list:
                            a = _divide_columns_for_matrix*len(divide)
                            b = float(_tbl_widths.replace('cm','')) - float(a)
                            cols_widhts=[]
                            for div in range(0,len(divide)):
                                cols_widhts.append(float(a/len(divide)))
                                cols_widhts.append(float(b/len(divide)))
                            colWidths = "cm,".join(map(str, cols_widhts))
                            colWidths = colWidths+'cm'
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
                            cols_widhts.append(float(_tbl_widths.replace('cm',''))/float(2.0))
                            for col in que.column_heading_ids:
                                cols_widhts.append(float((float(_tbl_widths.replace('cm',''))/float(2.0))/len(que.column_heading_ids)))
                        else:
                            cols_widhts.append(float(_tbl_widths.replace('cm','')))
                        colWidths = "cm,".join(map(str, cols_widhts))
                        colWidths = colWidths+'cm'
                        matrix_ans = ['',]
                        for col in que.column_heading_ids:
                            if col.title not in matrix_ans:
                                matrix_ans.append(col.title)
                        rml+="""
                        <blockTable colWidths=" """ + colWidths + """ " style="ans_tbl">
                            <tr>"""
                        for mat_col in matrix_ans:
                            rml+="""
                            <td><para style="response">""" + to_xml(mat_col) + """</para></td>"""
                        rml+="""</tr>"""
                        for ans in que.answer_choice_ids:
                            rml+= """<tr>"""
                            rml+="""<td><para style="answer">""" + to_xml(str(ans.answer)) + """</para></td>"""
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
                        cols_widhts.append(float(_tbl_widths.replace('cm','')))
                        colWidths = "cm,".join(map(str, cols_widhts))
                        colWidths = colWidths+'cm'
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
                if not datas['form']['without_pagebreak']:
                    rml+="""<pageBreak/>"""
                else:
                    rml+="""<para style="P2"><font></font></para>"""
        rml+="""</story></document>"""
        report_type = datas.get('report_type', 'pdf')
        create_doc = self.generators[report_type]
        pdf = create_doc(rml, title=self.title)
        return (pdf, report_type)
survey_form('report.survey.form', 'survey','','')