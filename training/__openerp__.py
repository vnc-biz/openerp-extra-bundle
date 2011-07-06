# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
#    Copyright (c) 2010-2011 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jesús Martín <jmartin@zikzakmedia.com>
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
    'name' : 'Training Management',
    'version' : '0.5',
    'author' : 'Tiny SPRL - AJM Technologies S.A',
    'website' : 'http://www.openerp.com',
    "license" : "GPL-3",
    'category' : 'Enterprise Specific Modules/Training',
    'description' : """
From the conception of a project to the elaboration of your catalog, our training management allows you to create easily courses and to organize the sessions.
With the analytic account support, you can know the costs of your trainings.

* Manage the subscriptions
* Manage the courses
* Manage the offers (for a planning)
* Manage the sessions
* Manage the support of course
""",
    'depends' : [
        'account',
        'base_contact_team',
        'base_iban',
        'product',
        'smtpclient',
        'sale',
        'document',
        'account_analytic_plans',
        'purchase_analytic_plans',
        'account_payment',
    ],
    'init_xml' : [
        'training_sequence.xml',
        'training_data.xml',
    ],
    'demo_xml' : [ #TODO
        'demo/training_course_type.xml',
        'demo/training_course_category.xml',
        'demo/training_course_theme.xml',
        'demo/training_course.xml',
        'demo/training_offer.xml',
        'demo/training_catalog.xml',
        'demo/training_holiday.xml',
        'demo/training_session.xml',
        #'demo/training_seance.xml', #It needs review you are trying to load data on a osv_memory
    ],
    'update_xml' : [
        'security/training_security.xml',
        'security/ir.model.access.csv',
        
        'wizard/course_pending.xml',
        'wizard/create_block_offer.xml',
        'wizard/create_offer.xml',
        'wizard/create_session.xml',
        'wizard/offer_purchase_line_update.xml',
        'wizard/seance_generate_pdf.xml',
        'wizard/session_duplicate.xml',
        'wizard/subscription_cancelation.xml',
        'wizard/subscription_line_confirm.xml',
        'wizard/subscription_line_change_participant.xml',
        'wizard/subscription_second_line.xml',
        'wizard/subscription_session.xml',
        'wizard/validate_course.xml',

        # TODO move this into the base_contact module
        'contact_security/groups.xml',
        'contact_security/ir.model.access.csv',
        'purchase_view.xml',
        'partner_view.xml',
        'base_contact_view.xml',
        'product_view.xml',
        'training_view.xml',
        'invoice_view.xml',
        'company_view.xml',
        'training_report.xml',
        'workflow/catalog.xml',
        'workflow/course.xml',
        'workflow/offer.xml',
        'workflow/seance.xml',
        'workflow/session.xml',
        'workflow/subscription.xml',
        'workflow/subscription_line.xml',
        'workflow/participation_sh_request.xml',
        'workflow/participation_sh.xml',
        'workflow/invoice.xml',
        'training_email_view.xml',
        'training_holiday_view.xml',
        'wizard/create_holiday_year.xml',
        'wizard/participation_reassign.xml',
        'wizard/subscription_mass.xml',
        'document_price_view.xml',
    ],
    'active' : False,
    'installable' : True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
