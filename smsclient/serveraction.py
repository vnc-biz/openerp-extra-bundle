# -*- coding: utf-8 -*-
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

from osv import osv
from osv import fields
import netsvc
import time
from tools.misc import ustr

class ServerAction(osv.osv):
    """
    Possibility to specify the SMS Gateway when configure this server action
    """
    _inherit = 'ir.actions.server'

    _columns = {
        'sms_server':fields.many2one('sms.smsclient', 'SMS Server', help='Select the SMS Gateway configuration to use with this action'),
    }

    def run(self, cr, uid, ids, context={}):
        logger = netsvc.Logger()

        act_ids = []

        for action in self.browse(cr, uid, ids, context):
            obj_pool = self.pool.get(action.model_id.model)
            obj = obj_pool.browse(cr, uid, context['active_id'], context=context)
            cxt = {
                'context':context,
                'object': obj,
                'time':time,
                'cr': cr,
                'pool' : self.pool,
                'uid' : uid
            }

            expr = eval(str(action.condition), cxt)
            if not expr:
                continue

            if action.state == 'sms':
                logger.notifyChannel('sms', netsvc.LOG_INFO, 'send SMS')
                sms_pool = self.pool.get('sms.smsclient')
                mobile = str(action.mobile)
                to = None
                try:
                    cxt = {
                        'context':context,
                        'object': obj,
                        'gateway': action.sms_server,
                        'time':time,
                        'cr': cr,
                        'pool' : self.pool,
                        'uid' : uid
                    }
                    if mobile:
                        to =  eval(action.mobile, cxt)
                    else:
                        logger.notifyChannel('sms', netsvc.LOG_ERROR, 'Mobile number not specified !')
                    text = eval(action.sms, cxt)
                    if sms_pool.send_message(cr, uid, action.sms_server.id, to, text) == True:
                        logger.notifyChannel('sms', netsvc.LOG_INFO, 'SMS successfully send to : %s' % (to))
                    else:
                        logger.notifyChannel('sms', netsvc.LOG_ERROR, 'Failed to send SMS to : %s' % (to))
                except Exception, e:
                    logger.notifyChannel('sms', netsvc.LOG_ERROR, 'Failed to send SMS : %s' % repr(e))
                    pass
            else:
                act_ids.append(action.id)

        if act_ids:
            return super(ServerAction,self).run(cr, uid, act_ids, context)
        else:
            return False

ServerAction()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
