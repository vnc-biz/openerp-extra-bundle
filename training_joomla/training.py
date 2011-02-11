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
from tools.translate import _
import re
import unicodedata
import netsvc

class training_joomla(osv.osv):
    _name = "training.joomla"
    _description = "Training Joomla Configuration"

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'location': fields.char('Location', size=128, required=True, help="Your Joomla! URL. For example: http://www.domain.com"),
        'username': fields.char('User Name', size=32, required=True, help="Super administrator user: username"),
        'password': fields.char('Password', size=32, required=True, help="Super administrator user: password"),
        'price_list_id' : fields.many2one('product.pricelist', 'Pricelist', required=True, domain="[('type', '=', 'sale')]"),
        'product_category_id': fields.many2one('product.category','Product Category', required=True),
        'partner_joomla_ids': fields.many2many('res.partner','training_partner_joomla_rel', 'partner_id','joomla_id','Partner to export',required=True),
        'course_draft': fields.boolean('Draft'),
        'course_pending': fields.boolean('Pending'),
        'course_deprecated': fields.boolean('Deprecated'),
        'course_validated': fields.boolean('Validated'),
        'offer_draft': fields.boolean('Draft'),
        'offer_deprecated': fields.boolean('Deprecated'),
        'offer_validated': fields.boolean('Validated'),
        'session_draft': fields.boolean('Draft'),
        'session_opened': fields.boolean('Opened'),
        'session_opened_confirmed': fields.boolean('Confirmed'),
        'session_closed_confirmed': fields.boolean('Closed Subscriptions'),
        'session_inprogress': fields.boolean('In Progress'),
        'session_closed': fields.boolean('Closed'),
        'session_cancelled': fields.boolean('Cancelled'),
        'duplicate_subscription': fields.boolean('Duplicate subscription', help="If active, cancel other subscriptions with same edition and create new subscription"),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': lambda *a: 1,
        'course_validated': lambda *a: 1,
        'offer_validated': lambda *a: 1,
        'session_opened': lambda *a: 1,
        'session_opened_confirmed': lambda *a: 1,
    }

training_joomla()

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)

class training_course(osv.osv):
    _inherit = 'training.course'

    _columns = {
        'long_name' : fields.char('Long Name', size=256, select=1, help='Allows to show the long name of the course for the external view', required=True),
        'alias': fields.char('Alias', size=256),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription'),
    }

    def onchange_longName(self, cr, uid, ids, long_name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(long_name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

training_course()

class training_offer(osv.osv):
    _inherit = 'training.offer'

    _columns = {
        'alias': fields.char('Alias', size=64),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription'),
        'frontpage' : fields.boolean('Front Page', help='Show this offer at Front Page'),
    }

    def onchange_name(self, cr, uid, ids, name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

training_offer()

class training_session(osv.osv):
    _inherit = 'training.session'

    _columns = {
        'alias': fields.char('Alias', size=64),
        'metakey' : fields.text('MetaKey'),
        'metadescription' : fields.text('MetaDescription'),
    }

    def onchange_name(self, cr, uid, ids, name, alias):
        value = {}
        if not alias:
            alias = slugify(unicode(name,'UTF-8'))
            value = {'alias': alias}
        return {'value':value}

training_session()

class training_subscription(osv.osv):
    _inherit = 'training.subscription'

    def check_vat(self, vat):
        partner_obj = self.pool.get('res.partner')
        vat_country, vat_number = vat[:2].lower(), vat[2:].replace(' ', '')
        if hasattr(partner_obj, 'check_vat_' + vat_country.lower()):
            check = getattr(partner_obj, 'check_vat_' + vat_country.lower())
            res = check(vat_number)
        return res

    def create_partner(self, cr, uid, values, context=None):
        partner_obj = self.pool.get('res.partner')
        contact_obj = self.pool.get('res.partner.contact')
        partner_address_obj = self.pool.get('res.partner.address')
        partner_job_obj = self.pool.get('res.partner.job')

        partner_id = ''
        ids = partner_obj.search(cr, uid, [('vat','=',values['vat'])])
        if ids:
            partner_id = ids[0]

        contact_id = ''
        ids = contact_obj.search(cr, uid, [('email','=',values['email'])])
        if ids:
            contact_id = ids[0]

        if not partner_id:
            if self.check_vat(values['vat']):
                vat = values['vat']
                comment = ''
            else:
                vat = ''
                comment = values['vat']

            partner_values = {
                'name' : values['first_name']+' '+values['name'],
                'vat' : vat,
                'comment' : comment,
            }
            partner_id = partner_obj.create(cr, uid, partner_values)

        if not contact_id:
            contact_values = {
                'name' : values['name'],
                'first_name' : values['first_name'],
                'mobile' : values['mobile'],
                'email' : values['email'],
            }
            contact_id = contact_obj.create(cr, uid, contact_values)

        #check if this partner exist this address
        partner_address_id = ''
        ids = partner_address_obj.search(cr, uid, [('street','=',values['street']),('zip','=',values['zip'])])
        if ids:
            partner_address_id = ids[0]

        if not partner_address_id:
            partner_address_values = {
                'partner_id': partner_id,
                'street': values['street'],
                'zip': values['zip'],
                'city': values['city'],
#                'state_id': values['state_id'],
                'country_id': values['country_id'],
                'email': values['email'],
                'phone': values['phone'],
            }
            partner_address_id = partner_address_obj.create(cr, uid, partner_address_values)

        # create partner_job
        partner_job_values = {
            'name': partner_id,
            'address_id': partner_address_id,
            'contact_id': contact_id,
            'email': values['email'],
            'phone': values['phone'],
        }
        partner_job_id = partner_job_obj.create(cr, uid, partner_job_values)

        #return information ID
        values = {
            'partner_id': partner_id,
            'address_id': partner_address_id,
            'contact_id': contact_id,
            'job_id': partner_job_id,
        }

        return values

    def write_partner(self, cr, uid, values, context=None):
        contact_obj = self.pool.get('res.partner.contact')
        partner_address_obj = self.pool.get('res.partner.address')

        if(values['address_id']):
            ids = [values['address_id']]
            partner_address_values = {
                'street': values['street'],
                'zip': values['zip'],
                'city': values['city'],
#                'state_id': values['state_id'],
                'country_id': values['country_id'],
                'email': values['email'],
                'phone': values['phone'],
            }
            partner_address_obj.write(cr, uid, ids, partner_address_values, context)

        if(values['contact_id']):
            ids = [values['contact_id']]
            contact_values = {
                'mobile' : values['mobile'],
                'email' : values['email'],
            }
            contact_obj.write(cr, uid, ids, contact_values, context)

        return True

    def create_subscription(self, cr, uid, subscription_order, context=None):
        """Internet Subscription: create Subscription"""
        if context == None:
            context = {}

        logger = netsvc.Logger()

        if not subscription_order['website']:
            logger.notifyChannel(_("Training Joomla Subscription"), netsvc.LOG_ERROR, _("Training Enrol Component not defined Name Website"))

        ids = self.pool.get('training.joomla').search(cr, uid, [('name','=',subscription_order['website']),('active','=',True)])
        if ids:
            website = self.pool.get('training.joomla').browse(cr, uid, ids[0], context)
            price_list_id = website.price_list_id.id

            # Delete duplicate subscripcions
            if website.duplicate_subscription:
                for line in subscription_order['lines']:
                    subscription_line_ids = self.pool.get('training.subscription.line').search(cr, uid, [('partner_id','=',subscription_order['partner_id']),('session_id','=',line['session_id']),('subscription_state','=','draft')])
                    for subscription_line_id in subscription_line_ids:
                        subscription_id = self.pool.get('training.subscription').search(cr, uid, [('partner_id','=',subscription_order['partner_id']),('subscription_line_ids','=',subscription_line_id),('state','=','draft')])
                        if subscription_id:
                            # Cancel Subscription
                            wf_service = netsvc.LocalService('workflow')
                            wf_service.trg_validate(uid, 'training.subscription', subscription_id[0], 'signal_cancel', cr)

            name = self.pool.get('ir.sequence').get(cr, uid, 'training.joomla.subscription') #reference

            #check if partner training fields exists. if not, add
            partner = self.pool.get('res.partner').browse(cr, uid, subscription_order['partner_id'])

            if not partner.notif_contact_id.id:
                self.pool.get('res.partner').write(cr, uid, [subscription_order['partner_id']], {'notif_contact_id': subscription_order['job_id']}, context)
            if not partner.notif_invoicing_id.id:
                self.pool.get('res.partner').write(cr, uid, [subscription_order['partner_id']], {'notif_invoicing_id': subscription_order['job_id']}, context)

            # creates Subscription Order
            subscription_id = self.create(cr, uid, {
                'name' : name,
                'partner_id': subscription_order['partner_id'],
                'address_id': subscription_order['address_id'],
		        'is_from_web': 1,
                'state': 'draft',
            },context)

            job_id = subscription_order['job_id']

            for line in subscription_order['lines']:
                values = {
                    'name': self.pool.get('ir.sequence').get(cr, uid, 'training.joomla.subs.line'),
                    'subscription_id': subscription_id,
                    'job_id': job_id,
                    'session_id': line['session_id'],
                    'price_list_id': price_list_id,
                    'price': line['price_unit'],
                    'session_state': 'draft',
                    'state': 'draft',
                }

                self.pool.get('training.subscription.line').create(cr, uid, values ,context)

            logger.notifyChannel(_("Training Joomla Subscription"), netsvc.LOG_INFO, _("Subscription Create: %s") % (name))

            return name
        else:
            logger.notifyChannel(_("Training Joomla Subscription"), netsvc.LOG_ERROR, _("Price List %s not found or not active") % (subscription_order['website']))
            return False

    def cancel_subscription(self, cr, uid, subscription_order, context=None):
        """Internet Subscription: cancel Subscription"""
        if context == None:
            context = {}

        logger = netsvc.Logger()

        ids = self.search(cr, uid, [('name','=',subscription_order['reference']),('state','=','draft')])
        subscription_ids = self.action_workflow_cancel(cr, uid, ids, context)

        if subscription_ids:
            logger.notifyChannel(_("Training Joomla Subscription"), netsvc.LOG_ERROR, _("Subscription %s is cancell") % (subscription_order['reference']))
            return True
        else:
            return False

    def confirm_subscription(self, cr, uid, values, context=None):
        """Internet Subscription"""
        if context == None:
            context = {}

        # values = refence / payment
        subscription_id = self.search(cr, uid, [('name','=',values['reference']),('state','=','draft')])

        if subscription_id:
            # TODO: by payment type
            # 1. Subscription lines: if payment is X, Draf -> Confirmed
            # 3. Subscription Lines: if payment is X, Confirmed -> Done
            # 4. Subscription: if payment is X, Draf -> Request Send
            # 5. Subscription: if payment is X, Request Send -> Done
            # 4. Create invoice: if payment is X, Create invoice & confirm
            return True
 
training_subscription()

class training_subscription_line(osv.osv):
    _inherit = 'training.subscription.line'

    def check_subscription_web(self, cr, uid, values, context=None):
        """Check subscription are state not cancelled"""
        if context == None:
            context = {}

        if values:
            same_contact_same_session = [('contact_id', '=', values['contact_id']), ('session_id', '=', values['session_id']), ('state', '!=', 'cancelled')]

            sl_ids = self.search(cr, 1, same_contact_same_session, context=context)

            if sl_ids:
                return True
            else:
                return False

training_subscription_line()

#class training_offer_format(osv.osv):
#    _inherit = 'training.offer.format'

#    _columns = {
#        'alias': fields.char('Alias', size=64),
#    }

#    def onchange_name(self, cr, uid, ids, name, alias):
#        value = {}
#        if not alias:
#            alias = slugify(unicode(name,'UTF-8'))
#            value = {'alias': alias}
#        return {'value':value}

#training_offer_format()

#class training_course_type(osv.osv):
#    _inherit = 'training.course_type'

#    _columns = {
#        'alias': fields.char('Alias', size=64),
#    }

#    def onchange_name(self, cr, uid, ids, name, alias):
#        value = {}
#        if not alias:
#            alias = slugify(unicode(name,'UTF-8'))
#            value = {'alias': alias}
#        return {'value':value}

#training_course_type()

#class training_course_theme(osv.osv):
#    _inherit = 'training.course.theme'

#    _columns = {
#        'alias': fields.char('Alias', size=64),
#    }

#    def onchange_name(self, cr, uid, ids, name, alias):
#        value = {}
#        if not alias:
#            alias = slugify(unicode(name,'UTF-8'))
#            value = {'alias': alias}
#        return {'value':value}

#training_course_theme()
