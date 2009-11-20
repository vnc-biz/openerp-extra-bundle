# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from osv import fields
from osv import osv

UNITS_DELAY = [
        ('minute','Minutes'),
        ('hour','Hours'),
        ('day','Days'),
        ('week','Weeks'),
        ('month','Months'),
        ]
class dm_campaign_proposition_segment(osv.osv):
    _name = "dm.campaign.proposition.segment"
    _description = "Segmentation"
    _inherit = "dm.campaign.proposition.segment"
    
    _columns = {
            'auto_extract': fields.boolean('Use Automatic Extraction'),
            'extract_date_start': fields.datetime('First Extraction Date'),
            'extract_date_end': fields.datetime('Last Extraction Date'),
            'extract_date_previous': fields.datetime('Previous Extraction Date',readonly=True),
            'extract_date_next': fields.datetime('Next Extraction Date',readonly=True),
            'extract_delay': fields.integer('Delay'),
            'extract_unit_delay': fields.selection(UNITS_DELAY, 'Delay Unit'),
                }
    
dm_campaign_proposition_segment()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
