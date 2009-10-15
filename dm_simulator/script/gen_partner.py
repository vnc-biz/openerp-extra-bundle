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
import xmlrpclib
import time

host = "localhost"
port = "8069"
db = "dm"
user = "admin"
pwd = "admin"

print "Number of Partners",
no_partner = raw_input('=> ')

sock = xmlrpclib.ServerProxy("http://"+host+':'+port+'/xmlrpc/common')
uid = sock.login(db, user, pwd)

server = xmlrpclib.ServerProxy("http://"+host+':'+port+'/xmlrpc/object')
padding = len(no_partner)+1
start_time = time.time()

print "Creating %s partners" % no_partner

for i in range(1,int(no_partner)+1):
    p_id = server.execute(db,uid,pwd,'res.partner','create',{'name':str('P%%0%sd' % padding % i)})
    a_id = server.execute(db,uid,pwd,'res.partner.address','create',{'name':str('Address of P%%0%sd' % padding % i),'partner_id':p_id})
#    print p_id, a_id

end_time = time.time()
delta = end_time - start_time

print "%s partners created in %s seconds"% (no_partner,str(delta))

