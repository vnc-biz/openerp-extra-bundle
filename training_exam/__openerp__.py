# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu). All Rights Reserved
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

{
    'name' : 'Training Exam',
    'version' : '0.5',
    'author' : 'Tiny SPRL - AJM Technologies S.A',
    'website' : 'http://www.openerp.com',
    'category' : 'Enterprise Specific Modules/Training',
    'description' : """This module adds the exam management for the training management""",
    'depends' : [
        'training',
    ],
    'init_xml' : [
        'training_exam_data.xml',
    ],
    'demo_xml' : [
        'data/training.exam.question.csv',
        'data/training.exam.question.answer.csv',
        #'training_exam_demo.xml',
    ],
    'update_xml' : [
        'security/training_exam_security.xml',
        'security/ir.model.access.csv',
        'training_exam_view.xml',
        'training_exam_report.xml',
        'workflow/questionnaire_workflow.xml',
        'training_exam_sequence.xml',
        'training_exam_wizard.xml',
    ],
    'active' : False,
    'installable' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
