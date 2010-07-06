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
# demonstration of using the BeatBox library to call the sforce API

import sys
import beatbox
import xmltramp
import datetime
import netsvc
logger = netsvc.Logger()

sf = beatbox._tPartnerNS
svc = beatbox.Client()

class BeatBoxDemo:
	def login(self, username, password):
		self.password = password
		loginResult = svc.login(username, password)

	def getServerTimestamp(self):
		 logger.notifyChannel("\ngetServerTimestamp " + svc.getServerTimestamp())

	def describeGlobal(self):
		dg = svc.describeGlobal()
		for t in dg[sf.types:]:
			 logger.notifyChannel(str(t))

	def describeTabs(self):
		dt = svc.describeTabs()
		for t in dt:
			 logger.notifyChannel(str(t[sf.label]))

	def query(self):
		qr = svc.query("select Id, Name from Account")

		for rec in qr[sf.records:]:
			 logger.notifyChannel(str(rec[0]) + " : " + str(rec[2]) + " : " + str(rec[3]))

		if (str(qr[sf.done]) == 'false'):
			qr = svc.queryMore(str(qr[sf.queryLocator]))
			for rec in qr[sf.records:]:
				 logger.notifyChannel(str(rec[0]) + " : " + str(rec[2]) + " : " + str(rec[3]))

	def upsert(self):
		t = { 'type': 'Task',
			  'ChandlerId__c': '12345',
			  'subject': 'BeatBoxTest updated',
			  'ActivityDate' : datetime.date(2006,2,20) }

		ur = svc.upsert('ChandlerId__c', t)

		t = { 	'type': 'Event',
			'ChandlerId__c': '67890',
			'durationinminutes': 45,
			'subject': 'BeatBoxTest',
			'ActivityDateTime' : datetime.datetime(2006,2,20,13,30,30),
			'IsPrivate': False }
		ur = svc.upsert('ChandlerId__c', t)
		if str(ur[sf.success]) == 'true':
			 logger.notifyChannel("id " + str(ur[sf.id]))
		else:
			 logger.notifyChannel("error " + str(ur[sf.errors][sf.statusCode]) + ":" + str(ur[sf.errors][sf.message]))

	def update(self):
		a = { 'type': 'Account',
			  'Id':   '00130000005MSO4',
			  'Name': 'BeatBoxBaby',
			  'NumberofLocations__c': 123.456 }
		sr = svc.update(a)

		if str(sr[sf.success]) == 'true':
			 logger.notifyChannel("id " + str(sr[sf.id]))
		else:
			 logger.notifyChannel("error " + str(sr[sf.errors][sf.statusCode]) + ":" + str(sr[sf.errors][sf.message]))

	def create(self):
		a = { 'type': 'Account',
			'Name': 'New Account',
			'Website': 'http://www.pocketsoap.com/' }
		sr = svc.create([a])

		if str(sr[sf.success]) == 'true':
			 logger.notifyChannel("id " + str(sr[sf.id]))
			 self.__idToDelete = str(sr[sf.id])
		else:
			 logger.notifyChannel("error " + str(sr[sf.errors][sf.statusCode]) + ":" + str(sr[sf.errors][sf.message]))


	def getUpdated(self):
		updatedIds = svc.getUpdated("Account", datetime.datetime.today()-datetime.timedelta(1), datetime.datetime.today()+datetime.timedelta(1))
		self.__theIds = []
		for id in updatedIds:
			self.__theIds.append(str(id))

	def delete(self):
		dr = svc.delete(self.__idToDelete)
		if str(dr[sf.success]) == 'true':
			 logger.notifyChannel("deleted id " + str(dr[sf.id]))
		else:
			 logger.notifyChannel("error " + str(dr[sf.errors][sf.statusCode]) + ":" + str(dr[sf.errors][sf.message]))

	def getDeleted(self):
		drs = svc.getDeleted("Account", datetime.datetime.today()-datetime.timedelta(1), datetime.datetime.today()+datetime.timedelta(1))
		for dr in drs:
			 logger.notifyChannel("getDeleted " + str(dr[sf.id]) + " on " + str(dr[sf.deletedDate]))

	def retrieve(self):
		accounts = svc.retrieve("id, name", "Account", self.__theIds)
		for acc in accounts:
			if len(acc._dir) > 0:
				 logger.notifyChannel(str(acc[beatbox._tSObjectNS.Id]) + " : " + str(acc[beatbox._tSObjectNS.Name]))
			else:
				 logger.notifyChannel("<null>")


	def getUserInfo(self):
		ui = svc.getUserInfo()
		logger.notifyChannel("hello " + str(ui[sf.userFullName]) + " from " + str(ui[sf.organizationName]))

	def resetPassword(self):
		ui = svc.getUserInfo()
		pr = svc.resetPassword(str(ui[sf.userId]))

		svc.setPassword(str(ui[sf.userId]), self.password)

	def describeSObjects(self):
		desc = svc.describeSObjects("Account")
		for f in desc[sf.fields:]:
			 logger.notifyChannel("\t" + str(f[sf.name]))

		desc = svc.describeSObjects(["Lead", "Contact"])
		for d in desc:
			logger.notifyChannel(str(d[sf.name]) + "\n" + ( "-" * len(str(d[sf.name]))))
			for f in d[sf.fields:]:
				 logger.notifyChannel("\t" + str(f[sf.name]))

	def describeLayout(self):
		desc = svc.describeLayout("Account")
		for layout in desc[sf.layouts:]:
			 logger.notifyChannel("sections in detail layout " + str(layout[sf.id]))
			 for s in layout[sf.detailLayoutSections:]:
				 logger.notifyChannel("\t" + str(s[sf.heading]))



if __name__ == "__main__":

	if len(sys.argv) != 3:
		 logger.notifyChannel("usage is demo.py <username> <password>")
	else:
		demo = BeatBoxDemo()
		demo.login(sys.argv[1], sys.argv[2])
		demo.getServerTimestamp()
		demo.getUserInfo()
		demo.resetPassword()
		demo.describeGlobal()
		demo.describeTabs()
		demo.describeSObjects()
		demo.describeLayout()
		demo.query()
		demo.upsert()
		demo.update()
		demo.create()
		demo.getUpdated()
		demo.delete()
		demo.getDeleted()
		demo.retrieve()