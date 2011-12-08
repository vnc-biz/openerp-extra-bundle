# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2010 Zikzakmedia S.L. (<http://www.zikzakmedia.com>). All Rights Reserved
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
############################################################################################

from osv import osv, fields
from tools.translate import _
from sets import Set
from ftplib import FTP

import tools
import netsvc
import os
import re
import zipfile
import math

class ingram(osv.osv):
    _name = "ingram"
    _description = "Ingram Configuration"

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'active': fields.boolean('Active'),
        'ftp_ip': fields.char('IP', size=256, required=True),
        'ftp_username': fields.char('Username', required=True, size=32),
        'ftp_password': fields.char('Password', required=True, size=32),
        'main_dir': fields.char('Main Directory', required=True, size=64),
        'locale': fields.many2one('res.lang', 'Locale', required=True),
        'product_ids': fields.many2many('product.product', 'ingram_product_product_rel', 'ingram_id', 'product_id', 'Products'),
        #category
        'category_dir': fields.char('Category Directory', required=True, size=64),
        'category_mapping_id': fields.many2one('csv.file', 'CSV', required=True),
        'category_codification': fields.selection([('iso-8859-15', 'iso-8859-15'),('utf-8', 'UTF-8')], 'Codification', required=True),
        'category_id': fields.many2one('product.category', 'Category', required=True),
        #product
        'product_dir': fields.char('Product Directory', required=True, size=32),
        'producttpl_mapping_id': fields.many2one('csv.file', 'CSV Template', required=True),
        'product_mapping_id': fields.many2one('csv.file', 'CSV Product', required=True),
        'product_codification': fields.selection([('iso-8859-15', 'iso-8859-15'),('utf-8', 'UTF-8')], 'Codification', required=True),
        #stock
#        'stock_dir':fields.char('Stock Directory', required=True, size=64),
#        'stock_mapping_id':fields.many2one('csv.file', 'CSV', required=True),
#        'stock_codification': fields.selection([('iso-8859-15', 'iso-8859-15'),('utf-8', 'UTF-8')], 'Codification', required=True),
    }

    _defaults = {
        'active': lambda *a: 1,
        'category_dir': lambda *a: "AVAIL",
        'category_codification': lambda *a: "iso-8859-15",
        'product_codification': lambda *a: "iso-8859-15",
#        'stock_dir': lambda *a: "AVAIL",
#        'stock_codification': lambda *a: "iso-8859-15",
    }

    def check_ftp(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ingrams = self.browse(cr, uid, ids)
        for ingram in ingrams:
            try: ftp = FTP(ingram.ftp_ip)
            except:
                raise osv.except_osv(_('Error!'), _("IP FTP connection was not successfully!"))
            try: ftp.login(ingram.ftp_username, ingram.ftp_password)
            except:
                raise osv.except_osv(_('Error!'), _("Username/password FTP connection was not successfully!"))
            ftp.quit()
            raise osv.except_osv(_('Ok!'), _("FTP connection was successfully!"))

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if vals.get('active',False):
            actv_ids =  self.search(cr, uid, [('active','=',True)])
            if len(actv_ids):
                raise osv.except_osv(_('Error!'), _('There are another ingram configuration with "Active" field checked. Only one configuration is avaible for active field.'))
        return super(ingram, self).create(cr, uid, vals, context)

    def download_file(self, cr, uid, ids, directory, archive, ingram, path, context=None):
        """ # directory: The ftp directory
            # archive: The ftp name archive to download
            # ingram: This browse object
            # path: The path to save the archive """

        self.logger = netsvc.Logger()

        try:
            ftp = FTP(ingram.ftp_ip)
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Connected to %s") % ingram.ftp_ip)
        except:
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_ERROR, _("Can't connect to %s") % ingram.ftp_ip)
            raise osv.except_osv(_('Error!'), _("IP FTP connection was not successfully!"))

        try:
            ftp.login(ingram.ftp_username, ingram.ftp_password)
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Logged in as a %s") % ingram.ftp_username)
        except:
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_ERROR, _("Can't login as %s") % ingram.ftp_username)
            raise osv.except_osv(_('Error!'), _("Username/password FTP connection was not successfully!"))

        try:
            ftp.cwd(directory)
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Changed to directory %s") % directory)
        except:
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_ERROR, _("Can't change to directory %s") % directory)
            raise osv.except_osv(_('Error!'), _("FTP directory not correct!"))

        try:
            content = ftp.retrbinary('RETR ' + archive, open(path+"/"+archive, 'wb').write)
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Downloaded file %s") % archive)
        except:
            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_ERROR, _("Can't download file %s") % archive)
            raise osv.except_osv(_('Error!'), _("Not possible obtain the file!"))

        ftp.quit()
        return content

    def unzip_file_into_dir(self, file, dir):
    #    os.mkdir(dir, 0777)
        zfobj = zipfile.ZipFile(file)
        for name in zfobj.namelist():
            if name.endswith('/'):
                os.mkdir(os.path.join(dir, name))
            else:
                outfile = open(os.path.join(dir, name), 'wb')
                outfile.write(zfobj.read(name))
                outfile.close()
        return True

    def check_ean(self, eancode):
        if not eancode:
            return True
        if len(eancode) <> 13:
            return False
        try:
            int(eancode)
        except:
            return False
        oddsum=0
        evensum=0
        total=0
        eanvalue=eancode
        reversevalue = eanvalue[::-1]
        finalean=reversevalue[1:]

        for i in range(len(finalean)):
            if i%2:
                oddsum += int(finalean[i])
            else:
                evensum += int(finalean[i])
        total=(oddsum * 3) + evensum

        check = int(10 - math.ceil(total % 10.0)) %10

        if check != int(eancode[-1]):
            return False
        return True

    """
    Product Category Import
    """
    def import_category(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self.logger = netsvc.Logger()

        path = os.path.abspath(os.path.dirname(__file__) ) + "/temp"

        for ingram in self.browse(cr, uid, ids, context):
            csv_file = self.pool.get('csv.file').browse(cr, uid, ingram.category_mapping_id.id, context)

            code_field = self.pool.get('csv.file.field').search(cr, uid, [('file_id','=',ingram.category_mapping_id.id),('ingram_id','=',True)])
            
            if (code_field) < 0:
                logger.notifyChannel('Ingram', netsvc.LOG_ERROR, "Check in CSV Field one Ingram ID available.")
                raise osv.except_osv(_('Error!'), _('Check in CSV Field one Ingram ID available.'))

            code_field = self.pool.get('csv.file.field').browse(cr, uid, code_field[0])

            locale = ingram.locale.code[3:5]
            directory = str(ingram.main_dir) + "/" + str(locale) + "/" + str(ingram.category_dir)
            csvfile = csv_file.file

            content = self.download_file(cr, uid, ids, directory, csvfile, ingram, path, context)

            if content:
                line = False
                values = self.pool.get('csv.file').import_csv(cr, uid, [ingram.category_mapping_id.id], context)

                for value in values:
                    #ingram_values = dicc to OpenERP
                    ingram_value = {}
                    ingram_value['parent_id'] = ingram.category_id.id #parent category ingram

                    for ingram_values in range(len(value)):
                        if value[ingram_values]['field'] == code_field.field_id.name:
                            code = value[ingram_values]['value']

                        #custom ingram transformation at name
                        fields_custom = ['name','description']
                        if value[ingram_values]['field'] in fields_custom:
                            ing_value = re.sub('  ','',value[ingram_values]['value']) #replace spaces
                        else:
                            ing_value = value[ingram_values]['value']

                        if type(ing_value) in ['str']:
                            ingram_value[value[ingram_values]['field']] = unicode(ing_value, ingram.product_codification )
                        else:
                            ingram_value[value[ingram_values]['field']] = ing_value

                    prod_categories = self.pool.get('product.category').search(cr, uid, [(code_field.field_id.name,'=',re.sub('  ','',code))])

                    if len(prod_categories) > 0: #update
                        self.pool.get('product.category').write(cr, uid, prod_categories, ingram_value)
                        self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Update Product Category %s") % ingram_value)
                    else: #create
                        self.pool.get('product.category').create(cr, uid, ingram_value)
                        self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Create Product Category %s") % ingram_value)
                    
                self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("End CSV file %s.") % csvfile)
            else:
                self.logger.notifyChannel(_("Ingram"), netsvc.LOG_ERROR, _("CSV file %s don't download and process") % csvfile)

        return True

    """
    Product Import
    """
    def import_product(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self.logger = netsvc.Logger()

        path = os.path.abspath(os.path.dirname(__file__) ) + "/temp"
        
        for ingram in self.browse(cr, uid, ids, context):
            csv_file = self.pool.get('csv.file').browse(cr, uid, ingram.product_mapping_id.id, context)

            code_field = self.pool.get('csv.file.field').search(cr, uid, [('file_id','=',ingram.product_mapping_id.id),('ingram_id','=',True)])
            
            if (code_field) < 0:
                logger.notifyChannel('Ingram', netsvc.LOG_ERROR, "Check in CSV Field one Ingram ID available.")
                raise osv.except_osv(_('Error!'), _('Check in CSV Field one Ingram ID available.'))

            code_field = self.pool.get('csv.file.field').browse(cr, uid, code_field[0])

            main_dir = ingram.main_dir
            locale = ingram.locale.code[3:5]
            product_dir = ingram.product_dir
            directory = str(main_dir) + "/" + str(locale) + "/" + str(product_dir)
            filename = re.sub('TXT', 'ZIP', csv_file.file)

            content = self.download_file(cr, uid, ids, directory, filename, ingram, path, context)
            content = self.unzip_file_into_dir(open(path+'/'+filename), path)
#            content = True

            if content:
                num_lines = self.pool.get('csv.file').lines_csv(cr, uid, ingram.producttpl_mapping_id.id, context)

                for line in range(num_lines):
                    prod_values = self.pool.get('csv.file').import_line_csv(cr, uid, [ingram.product_mapping_id.id], line, context)
                    prodtpl_values = self.pool.get('csv.file').import_line_csv(cr, uid, [ingram.producttpl_mapping_id.id], line, context)

                    # Join list product template and product csv mapping
                    if len(prodtpl_values) > 0 and len(prod_values) > 0:
                        values = prod_values[0]+prodtpl_values[0]

                        #create dicc all values of product
                        ingram_value = {}
                        for value in values:
                            if value['field'] == 'ingram_sku':
                                code = value['value']

                            #custom ingram transformation at name
                            fields_custom = ['ingram_sku','name','description']
                            if value['field'] in fields_custom:
                                ing_value = re.sub('  ','',value['value']) #replace spaces
                            else:
                                ing_value = value['value']

                            if type(ing_value) in ['str']:
                                ingram_value[value['field']] = unicode(ing_value, ingram.product_codification )
                            else:
                                ingram_value[value['field']] = ing_value

                            ingram_value[value['field']] = ing_value

                        # Search sku or Exclude product => create or update
                        product_ids = self.pool.get('product.product').search(cr, uid, [('ingram_sku','=',code)])
                        ingram_product = self.search(cr, uid, [('product_ids','in',product_ids)])

                        if len(ingram_product) == 0:
                            if len(product_ids) > 0: #update
                                self.pool.get('product.product').write(cr, uid, product_ids, ingram_value)
                                self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Update Product %s") % ingram_value)
                            else: #create
                                product_tmpl_id = self.pool.get('product.product').create(cr, uid, ingram_value)
                                self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Create Product %s: %s") % (code, ingram_value))
                        else:
                            self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Skip Product %s: %s") % (code, ingram_value))

                        cr.commit()
                    
                self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("End CSV file %s.") % filename)
            else:
                self.logger.notifyChannel(_("Ingram"), netsvc.LOG_ERROR, _("CSV file %s don't download and process") % filename)

        return True

    """Scheduler"""
    def _import_ingram(self, cr, uid, callback, context=None):
        if context is None:
            context = {}

        self.logger = netsvc.Logger()
        self.logger.notifyChannel(_("Ingram"), netsvc.LOG_INFO, _("Run Scheduler %s") % (callback))

        ids = self.pool.get('ingram').search(cr, uid, [('active', '=', True)], context=context)
        if ids:
            callback(cr, uid, ids, context=context)

        tools.debug(callback)
        tools.debug(ids)
        return True

    def run_ingram_import_category(self, cr, uid, context=None):
        self._import_ingram(cr, uid, self.import_category, context=None)
        return True

    def run_ingram_import_product(self, cr, uid, context=None):
        self._import_ingram(cr, uid, self.import_product_template, context=None)
        return True

ingram()
