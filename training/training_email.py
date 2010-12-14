# -*- encoding: utf-8 -*-
############################################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2008-2009 AJM Technologies S.A. (<http://www.ajm.lu>). All Rights Reserved
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
from osv.orm import browse_record

import tools
import locale
import time
from mako.template import Template as MakoTemplate
from tools.translate import _
import traceback
import sys
import netsvc
import cPickle

class training_email_stylegroup(osv.osv):
    _name = 'training.email.stylegroup'

    _columns = {
        'name': fields.char('Name', size=64, select=1),
        'default': fields.boolean('Default'),
    }

    def check_unique_default(self, cr, uid, ids, context=None):
        default_ids = self.search(cr, uid, [('default', '=', True)], context=context)
        if len(default_ids) > 1:
            return False
        return True

    _constraints = [
        (check_unique_default, "You could only have one default style", ['default']),
    ]

training_email_stylegroup()

class training_email_error(osv.osv):
    _name = 'training.email.error'

    _columns = {
        'create_date' : fields.datetime('Create Date', readonly=True, select=1),
        'create_uid' : fields.many2one('res.users', 'User', readonly=True, select=1),
        'name' : fields.char('Subject', size=256,
                             required=True, readonly=True,
                             select=1),
        'message' : fields.text('Message', select=1,
                                required=True, readonly=True),
        'objects' : fields.text('Objects',
                                required=True, readonly=True),
    }

    _order = 'create_date desc'

    def action_send(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            objects = eval(obj.objects)

            info_email = objects['info_email']
            oo_objects = {}
            for key, values in objects['objects'].items():
                if values['type'] in ('list', 'browse_record') :
                    oo_objects[key] = self.pool.get(values['object']).browse(cr, uid, values['values'], context=objects['ctx'])
                else:
                    oo_objects[key] = values['values']

            session = oo_objects.pop('session', None)
            seance = oo_objects.pop('seance', None)
            stylegroup = oo_objects.pop('stylegroup', None)
            self.pool.get('training.email').send_email(cr, uid,
                                                       trigger=info_email['trigger'],
                                                       target=info_email['target'],
                                                       to=info_email['to'],
                                                       context=objects['ctx'],
                                                       session=session,
                                                       seance=seance,
                                                       stylegroup=stylegroup,
                                                       **oo_objects
                                                      )

            obj.unlink(context=context)

        return True

training_email_error()

class training_email_layout(osv.osv):
    _name = 'training.email.layout'
    _description = 'Layout for emails'

    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'layout': fields.text('Layout', required=True, translate=True),
    }
training_email_layout()

class training_email_sign(osv.osv):
    _name = 'training.email.sign'
    _description = 'Training Email Sign'
    
    _columns = {
        'name': fields.char('Name', size=32, required=True),
        'sign': fields.text('Sign', required=True, translate=True),
    }
training_email_sign()


class training_email(osv.osv):
    _name = 'training.email'
    _description = 'Training Email'
    _rec_name = 'subject'

    # button callback
    def draft_cb(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'draft'}, context=context)

    # button callback
    def validate_cb(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'validated'}, context=context)

    # button callback
    def deprecate_cb(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state' : 'deprecated'}, context=context)

    def _get_default_layout(self, cr, uid, context):
        ima = self.pool.get('ir.model.data')
        imaid = ima.search(cr, uid, [('module', '=', 'training'), ('name', '=', 'default_email_layout')])
        if not imaid:
            return False
        return ima.read(cr, uid, [imaid[0]], ['res_id'])[0]['res_id']

    def _get_default_stylegroup(self, cr, uid, context=None):
        tesg = self.pool.get('training.email.stylegroup')
        default_ids = tesg.search(cr, uid, [('default','=',True)], context=context)
        if default_ids:
            return default_ids[0]
        # get the first one
        all_ids = tesg.search(cr, uid, [], context=context)
        if all_ids:
            return all_ids[0]
        return None

    _columns = {
        'trigger': fields.selection(
            [
                ('sub_confirm_open', 'Subscription Draft -> Confirmation (Session Not Confirmed)'),
                ('sub_confirm_openconf', 'Subscription Draft -> Confirmation (Session Confirmed)'),
                ('sub_cancelled', 'Subscription Confirmed -> Cancelled'),
                ('sub_replacement', 'Subscription Replacement'),
                ('session_open_confirmed', 'Session Open -> Confirmed'),
                ('session_confirm_cancelled', 'Session Confirmed -> Cancelled'),
                ('session_date_changed', 'Session Date Changed'),
                ('sh_request', 'Availability Request - Request'),
                ('sh_cancel', 'Availability Request - Cancellation'),
                ('sh_accept', 'Availability Request - Acceptance'),
                ('sh_refuse', 'Availability Request - Refusal'),
                ('invoice', 'Invoice'),
                ('exam-result', 'Exam Result'),
                ('procurements', 'Procurements'),
                ('correction_request', 'Correction Request - Request'),
                ('correction_cancel', 'Correction Request - Cancellation'),
                ('correction_accept', 'Correction Request - Acceptance'),
                ('correction_refuse', 'Correction Request - Refusal'),
                ('portal_create_user', 'Portal - Create User'),
            ],
            'Trigger',
            size=32,
            required=True,
            select=1),

        'target': fields.selection([
                ('p', 'Participants'),
                ('hr', 'Subscription Contacts (HR)'),
                ('sh', 'Lecturers'),
                ('a', 'Accountants'),
                ('s', 'Suppliers'),
                ('e', 'Examiners'),
                ('po', 'Portal'),
            ],
            'Target',
            size=4,
            required=True,
            select=1),

        'notes': fields.text('Internal Note', translate=True, select=2),

        'subject' : fields.char('Subject', size=256, required=True, translate=True, select=1),
        'smtp_client_id' : fields.many2one('email.smtpclient', 'SMTP Client', required=True, select=2, domain=[('state', '=', 'confirm')]),
        'body' : fields.text('Body', required=True, translate=True),
        'state' : fields.selection([('draft', 'Draft'),
                                    ('validated', 'Validated'),
                                    ('deprecated', 'Deprecated')
                                   ],
                                   'State',
                                   required=True,
                                   readonly=True,
                                   select=1),
        'layout_id': fields.many2one('training.email.layout', 'Layout'),
        'sign_id': fields.many2one('training.email.sign', 'Sign'),
        'from': fields.char('Email From', size=128, help='If not specify, use the email defined in the SMTP Client'),
        'reply_to': fields.char('Reply-to', size=128),
        'bcc': fields.char('Bcc', size=128),
        'fail_email': fields.char('Fail Email', size=128, help='If the mail rendering fail, the traceback will be sent to this email'),
        'stylegroup_id': fields.many2one('training.email.stylegroup', 'Style Group', select=1),
    }

    def verify_trigger_target(self, cr, uid, ids, trigger, target, context=None):
        if not trigger or not target:
            return {}
        warn = None
        values = {}

        if trigger.startswith('sub_') and target == 'sh':
            warn = _('Lecturers never recieve emails about subscriptions')

        elif trigger.startswith('sh_') and target != 'sh':
            warn = _('Only lecturers will receive request emails')

        elif trigger.startswith('correction_') and target != 'e':
            warn = _('Only examiners will receive request emails')
        elif trigger.startswith('portal_') and target != 'po':
            warn = _('This trigger can be only used with the Portal')
        elif trigger == 'invoice':
            if target != 'a':
                warn = _('Invoice emails are only sent to accountants')
                values['target'] = 'a'
        elif target == 'a':
            if trigger != 'invoice':
                warn = _('Accountant can only receive invoice emails')
                values['trigger'] = 'invoice'

        elif trigger == 'procurements':
            if target != 's':
                warn = _('Procurements email are only sent to suppliers')
                values['target'] = 's'
        elif target == 's':
            if trigger != 'procurements':
                warn = _('Suppliers can only receive procurements emails')
                values['trigger'] = 'procurements'


        if not warn:
            return {}
        return {'value': values, 'warning': {'title': _('Unreachable couple trigger/target'), 'message': warn}}

    def _get_email(self, cr, uid, trigger, target, stylegroup, context):
        stylegroup_id = stylegroup and stylegroup.id or None
        def do_search(trigger, target, stylegroup_id):
            search_crit = [('state', '=', 'validated'),
                           ('trigger', '=', trigger),
                           ('target', '=', target),
                           ('stylegroup_id', '=', stylegroup_id)]
            return self.search(cr, uid, search_crit, context=context)
        ids = do_search(trigger, target, stylegroup_id)
        if not ids:
            # no ids, search with the default style
            style_ids = self.pool.get('training.email.stylegroup').search(cr, uid,
                                [('default','=',True)])
            if style_ids:
                stylegroup_id = style_ids[0]
            ids = do_search(trigger, target, stylegroup_id)
            if not ids:
                # last chance, try with style = None
                stylegroup_id = None
                ids = do_search(trigger, target, stylegroup_id)
                if not ids:
                    return None
        # due to the _constraints, we are sure that there is one and only one validated email with this code
        return self.browse(cr, uid, ids[0], context)

    def _check_email(self, cr, uid, ids, context=None):
        """Check that only one email template by training.email `code'
           is in `validated' state
        """
        for email in self.browse(cr, uid, ids, context=context):
            if email.state == 'validated':
                cnt = self.search_count(cr, uid, [('state', '=', 'validated'),
                                                  ('trigger', '=', email.trigger),
                                                  ('target', '=', email.target),
                                                  ('stylegroup_id', '=', email.stylegroup_id.id),
                                                  ('id', '!=', email.id)],
                                        context=context)
                if cnt != 0:
                    return False
        return True

    _constraints = [
        (_check_email, "You can not have two validated emails for the same trigger, target and style group.", ['name', 'state', 'stylegroup_id']),
    ]

    _defaults = {
        'state' : lambda *a: 'draft',
        'layout_id': _get_default_layout,
    }
    

    def render(self, cr, uid, email, what, tpl, **objects):
        try:
            return MakoTemplate(tpl).render_unicode(**objects)
        except Exception, e:
            tb = "".join(traceback.format_exception(*sys.exc_info()))

            fail_tpl = """Trigger: ${email.trigger}
Target: ${email.target}

Objects:
%for o in objects:
    ${ o }<% zz = str(objects[o]) %>
    ${ zz }
%endfor

Traceback: 
${tb}
"""

            subject = "[EMAIL ERROR] Error when rendering %s" % (what,)
            body = MakoTemplate(fail_tpl).render_unicode(email=email, tb=tb, objects=objects)

            params = objects['params_error']

            for key, values in params['objects'].items():
                val = {}
                if isinstance(values, (list, set,)):
                    val = {
                        'values' : [obj.id for obj in values],
                        'object' : values and list(values)[0]._name or False,
                        'type' : 'list',
                    }
                elif isinstance(values, (browse_record, )):
                    val = {
                        'values' : values.id,
                        'object' : values._name,
                        'type' : 'browse_record',
                    }
                else:
                    val = {
                        'values' : values,
                        'type' : str(type(values))
                    }

                params['objects'][key] = val

            values = {
                'name' : subject,
                'message' : body,
                'objects' : str(objects['params_error']),
            }
            proxy = self.pool.get('training.email.error')
            proxy.create(cr, uid, values)

            if email.fail_email:
                self.pool.get('email.smtpclient').send_email(cr, uid, email.smtp_client_id.id, email.fail_email, subject, body, emailfrom=email['from'])
            else:
                netsvc.Logger().notifyChannel('training.email', netsvc.LOG_ERROR, subject) 
                netsvc.Logger().notifyChannel('training.email', netsvc.LOG_ERROR, body) 

            return None

    def _get_attachments(self, cr, uid, model, oid, context=None):
        proxy = self.pool.get('ir.attachment')
        aids = proxy.search(cr, uid, [('res_model', '=', model), ('res_id', '=', oid)], context=context)
        return [(a.datas_fname or a.name, a.datas.decode('base64')) for a in proxy.browse(cr, uid, aids, context=context)]
        
    def _get_lang(self, session, seance, **objects):
        lng = None
        if session:
            lng = session.offer_id.lang_id.code
        elif seance:
            lng = seance.course_id.lang_id.code
        return lng
    
    def convert_date(self, date_string, context=None):
        lc_time_backup = locale.getlocale(locale.LC_TIME)
        lang_format = {
            'fr_FR': '%d %B %Y - %HH%M',
            'de_DE': '%d %B %Y - %HH%M',
            'en_US': '%B, %d %Y - %HH%M',
        }
        lang = 'fr_FR'
        if context and 'lang' in context and context['lang'] in lang_format:
            lang = context['lang']
        try:
            locale.setlocale(locale.LC_TIME, (lang, lc_time_backup[1]))
        except:
            pass
        # convert from ISO time 
        date_tstruct = time.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        # convert to localized time & date
        date_string = time.strftime(lang_format[lang], date_tstruct)
        locale.setlocale(locale.LC_TIME, lc_time_backup)
        return unicode(date_string, 'utf8')

    def get_subline_group_id(self, subline, context=None):
        return subline.participation_ids[0].seance_id.group_id.id

    def send_email(self, cr, uid, trigger, target, to, session=None, seance=None, attachments=None, context=None, stylegroup=None, **objects):
        if not to:
            return False
        
        lng = self._get_lang(session, seance, **objects)

        if context is None:
            context = {}
        ctx = context.copy()
        if lng:
            ctx['lang'] = lng
        
        if attachments is None:
            attachments = []


        email = self._get_email(cr, uid, trigger, target, stylegroup, context=ctx)
        if not email:
            return False
    
        attachments += self._get_attachments(cr, uid, 'training.email', email.id, ctx)
        
        if session:
            objects['session'] = session
        if seance:
            objects['seance'] = seance
        if stylegroup:
            objects['stylegroup'] = stylegroup
        
        user = self.pool.get('res.users').browse(cr, uid, uid, context=ctx)

        objects['params_error'] = {
            'objects' : objects.copy(),
            'ctx' : ctx,
            'info_email' : {
                'trigger' : trigger,
                'target' : target,
                'to' : to,
            },
        }

        data = {
            'ctx': ctx,
            'time': time,
            'user': user,
            'convert_date': self.convert_date,
            'get_subline_group_id': self.get_subline_group_id,
        }

        objects.update(data)
        
        subject = self.render(cr, uid, email, 'subject', email.subject, **objects)
        if subject is None:
            return False

        body = self.render(cr, uid, email, 'body', email.body, **objects)
        if body is None:
            return False
        
        sign = ''
        if email.sign_id:
            attachments += self._get_attachments(cr, uid, 'training.email.sign', email.sign_id.id, ctx)
            sign = self.render(cr, uid, email, 'sign', email.sign_id.sign, **data)
            if sign is None:
                return False
        
        if email.layout_id:
            attachments += self._get_attachments(cr, uid, 'training.email.layout', email.layout_id.id, ctx)
            data['sign'] = sign
            data['body'] = body
            body = self.render(cr, uid, email, 'layout', email.layout_id.layout, **data)
            if body is None:
                return False
        else:
            body += sign

        self.pool.get('email.smtpclient').send_email(cr, uid, email.smtp_client_id.id, 
                                                     emailto=to, 
                                                     subject=subject, 
                                                     body=body, 
                                                     attachments=attachments, 
                                                     emailfrom=email['from'], 
                                                     replyto=email.reply_to,
                                                     bcc=email.bcc)
        return True

training_email()

from email import Encoders
from email.Message import Message
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.Utils import COMMASPACE, formatdate
import re

RE_COMPANY_LOGO = re.compile(r"""('|")cid:company_logo\1""")
RE_PARTNER_LOGO = re.compile(r"""('|")cid:partner_logo\1""")

class smtp_client(osv.osv):
    _inherit = 'email.smtpclient'

    def send_email(self, cr, uid, server_id, emailto, subject, body=False, attachments=[], emailfrom=None, replyto=None, bcc=None):
        queue = self.pool.get('email.smtpclient.queue')
        attach = self.pool.get('ir.attachment')
        
        smtp_server = self.browse(cr, uid, server_id)
        if smtp_server.state != 'confirm':
            raise osv.except_osv(_('SMTP Server Error !'), 'Server is not Verified, Please Verify the Server !')

        if not isinstance(emailto, list):
            emailto = [emailto]

        for to in emailto:
            msg = MIMEMultipart('related')
            msg.preamble = 'This is a multi-part message in MIME format.'
            msg['Subject'] = subject
            msg['To'] =  to
            msg['From'] = emailfrom or smtp_server.from_email
            if replyto:
                msg['Reply-to'] = replyto
            if isinstance(body, unicode):
                body = body.encode('utf-8')
                
            html = MIMEText(body or '', _charset='utf-8', _subtype="html")
            html.add_header('Content-Disposition', 'inline') 
            msg.attach(html)

            # search for company logo in email body
            if RE_COMPANY_LOGO.search(body) is not None:
                user = self.pool.get('res.users').browse(cr, uid, uid)
                if user.company_id.logo:
                    mimg = MIMEImage(user.company_id.logo.decode('base64'), name='company_logo')
                    mimg.add_header('Content-ID', '<company_logo>')
                    mimg.add_header('Content-Disposition', 'inline')
                    msg.attach(mimg)

            for filename, content in attachments:
                if filename == 'logo.partner.png':
                    if RE_PARTNER_LOGO.search(body) is not None:
                        mimg = MIMEImage(content, name="partner_logo")
                        mimg.add_header('Content-ID', '<partner_logo>')
                        mimg.add_header('Content-Disposition', 'inline')
                        msg.attach(mimg)
                else:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(content)
                    Encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % filename)
                    msg.attach(part)

            message = msg.as_string()
            
            tos = [to]
            if bcc:
                tos += [bcc]

            for to in tos:
                queue_id = queue.create(cr, uid, {
                    'to': to,
                    'server_id': server_id,
                    'cc': False,
                    'bcc': False,       # queue does not handle the bcc !?!
                    'name': subject,
                    'body': body,
                    'serialized_message': message,
                })

                for filename, content in attachments:
                    attach.create(cr, uid, {
                                      'name' : filename,
                                      'datas' : content.encode('base64'),
                                      'datas_fname' : filename,
                                      'description' : filename,
                                      'res_model' : 'email.smtpclient.queue',
                                      'res_id' : queue_id,
                                  })

        return True

smtp_client()

class smtp_queue(osv.osv):
    _inherit = 'email.smtpclient.queue'
    _order = 'date_create desc'

    def write(self, cr, *args, **kwargs):
        try:
            return super(smtp_queue, self).write(cr, *args, **kwargs)
        finally:
            cr.commit()

smtp_queue()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


