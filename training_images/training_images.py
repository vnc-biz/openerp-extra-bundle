# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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
import base64, urllib

class training_images(osv.osv):
    "Offer Image gallery"
    _name = "training.images"
    _description = __doc__
    _table = "training_images"
    
    def get_image(self, cr, uid, id):
        each = self.read(cr, uid, id, ['link', 'filename', 'image'])
        if each['link']:
            (filename, header) = urllib.urlretrieve(each['filename'])
            f = open(filename , 'rb')
            img = base64.encodestring(f.read())
            f.close()
        else:
            img = each['image']
        return img
    
    def _get_image(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for each in ids:
            res[each] = self.get_image(cr, uid, each)
        return res
    
    _columns = {
        'name':fields.char('Image Title', size=100, required=True),
        'base_image':fields.boolean('Base Image', help="Main Image of Offer"),
        'filename':fields.char('File Location', size=250),
        'comments':fields.text('Comments'),
        'offer_id':fields.many2one('training.offer', 'Offer')
    }

training_images()
