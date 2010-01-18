import xmlrpclib
import sys
import socket
import os
import pythoncom
import time

waittime = 10
wait_count = 0
wait_limit = 12

def execute(connector, method, *args):
    global wait_count
    res = False
    try:
        res = getattr(connector,method)(*args)
    except socket.error,e:
        if e.args[0] == 111:
            if wait_count > wait_limit:
                print "Server is taking too long to start, it has exceeded the maximum limit of %d seconds."%(wait_limit)
                clean()
                sys.exit(1)
            print 'Please wait %d sec to start server....'%(waittime)
            wait_count += 1
            time.sleep(waittime)
            res = execute(connector, method, *args)
        else:
            return res
    wait_count = 0
    return res

class XMLRpcConn:
    __name__ = 'XMLRpcConn'
    _com_interfaces_ = ['_IDTExtensibility2']
    _public_methods_ = ['GetDBList', 'login', 'GetAllObjects', 'GetObjList', 'InsertObj', 'DeleteObject', \
                        'ArchiveToOpenERP', 'IsCRMInstalled', 'GetCSList', 'GetPartners', 'GetObjectItems', \
                        'CreateCase', 'MakeAttachment', 'CreateContact', 'CreatePartner', '_port']
    _reg_clsctx_ = pythoncom.CLSCTX_INPROC_SERVER
    _reg_clsid_ = "{C6399AFD-763A-400F-8191-7F9D0503CAE2}"
    _reg_progid_ = "Python.OpenERP.XMLRpcConn"
    _reg_policy_spec_ = "win32com.server.policy.EventHandlerPolicy"
    def __init__(self,server='localhost',port=8069,uri='http://localhost:8069'):
        self._server=server
        self._port=port
        self._uri=uri
        self._obj_list=[]
        self._dbname=''
        self._uname='admin'
        self._pwd='a'
        self._login=False
        self._running=False
        self._uid=False
        self._iscrm=True

    def GetDBList(self):
        conn = xmlrpclib.ServerProxy(self._uri + '/xmlrpc/db')
        try:
            db_list = execute(conn, 'list')
            if db_list == False:
                self._running=False
                return []
            else:
                self._running=True
        except:
            db_list=-1
            self._running=True
        return db_list

    def login(self,dbname, user, pwd):
        self._dbname = dbname
        self._uname = user
        self._pwd = pwd
        conn = xmlrpclib.ServerProxy(self._uri + '/xmlrpc/common')
        uid = execute(conn,'login',dbname, user, pwd)
        return uid

    def GetAllObjects(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[])
        objects = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','read',ids,['model'])
        obj_list = [item['model'] for item in objects]
        return obj_list

    def GetObjList(self):
        self._obj_list.sort(reverse=True)
        return self._obj_list

    def InsertObj(self, obj_title,obj_name,image_path):
        self._obj_list.append((obj_title,obj_name,image_path))
        self._obj_list.sort(reverse=True)

    def DeleteObject(self,sel_text):
        for obj in self._obj_list:
            if obj[0] == sel_text:
                self._obj_list.remove(obj)
                break

    def ArchiveToOpenERP(self, recs, mail):
        import win32ui, win32con
        conn = xmlrpclib.ServerProxy(self._uri + '/xmlrpc/object')
        import eml
        eml_path=eml.generateEML(mail)
        att_name = eml_path.split('\\')[-1]
        cnt=1
        for rec in recs: #[('res.partner', 3, 'Agrolait')]
            cnt+=1
            obj = rec[0]
            obj_id = rec[1]
            ids=execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.attachment','search',[('res_id','=',obj_id),('name','=',att_name)])
            if ids:
                name=execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'read',obj_id,['name'])['name']
                msg="This mail is already attached to object with name '%s'"%name
                win32ui.MessageBox(msg,"Make Attachment",win32con.MB_ICONINFORMATION)
                continue
            sub = mail.Subject
            res={}
            res['res_model'] = obj
            content = "".join(open(eml_path,"r").readlines()).encode('base64')
            res['name'] = att_name
            res['datas_fname'] = sub+".eml"
            res['datas'] = content
            res['res_id'] = obj_id
            execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.attachment','create',res)

    def IsCRMInstalled(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.model','search',[('model','=','crm.case')])
        return id

    def GetCSList(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(int(self._uid)),self._pwd,'crm.case.section','search',[])
        objects = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'crm.case.section','read',ids,['name'])
        obj_list = [item['name'] for item in objects]
        return obj_list

    def GetPartners(self):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids=[]
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','search',[],0,100,'create_date')
        obj_list=[]
        for id in ids:
            object = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','read',[id],['id','name'])[0]
            obj_list.append((object['id'], object['name']))
        return obj_list

    def GetObjectItems(self, search_list=[], search_text=''):
        res = []
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        for obj in search_list:
            if obj == "res.partner.address":
                ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'search',['|',('name','ilike',search_text),('email','ilike',search_text)])
                recs = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'read',ids,['id','name','street','city'])
                for rec in recs:
                    name = str(rec['name'])
                    if rec['street']:
                        name += ', ' + str(rec['street'])
                    if rec['city']:
                        name += ', ' + str(rec['city'])
                    res.append((obj,rec['id'],name))
            else:
                ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'search',[('name','ilike',search_text)])
                recs = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,obj,'read',ids,['id','name'])
                for rec in recs:
                    name = str(rec['name'])
                    res.append((obj,rec['id'],name))
        return res

    def CreateCase(self, section, mail, partner_ids):
        res={}
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        res['name'] = mail.Subject
        res['note'] = mail.Body
        attachments = mail.Attachments
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'crm.case.section','search',[('name','=',section)])
        res['section_id'] = ids[0]
        if partner_ids:
            for partner_id in partner_ids:
                res['partner_id'] = partner_id
                partner_addr = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','address_get',[partner_id])
                res['partner_address_id'] = partner_addr['default']
                id=execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'crm.case','create',res)
                recs=[('crm.case',id,'')]
                self.MakeAttachment(recs, mail)
        else:
            id=execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'crm.case','create',res)
            recs=[('crm.case',id,'')]
            self.MakeAttachment(recs, mail)

    def MakeAttachment(self, recs, mail):
        attachments = mail.Attachments
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        for rec in recs: #[('res.partner', 3, 'Agrolait')]
            obj = rec[0]
            obj_id = rec[1]
            res={}
            res['res_model'] = obj
            for i in xrange(1, attachments.Count+1):
                fn = attachments[i].FileName
                att_folder_path = os.path.abspath(os.path.dirname(__file__)+"\\dialogs\\resources\\attachments\\")
                attachments[i].SaveAsFile(os.path.join(att_folder_path, fn))
                att_path = os.path.join(att_folder_path,fn)
                f=open(att_path,"r")
                content = "".join(f.readlines()).encode('base64')
                f.close()
                res['name'] = attachments[i].DisplayName
                res['datas_fname'] = fn
                res['datas'] = content
                res['res_id'] = obj_id
                execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'ir.attachment','create',res)

    def CreateContact(self, sel, res):
        res['partner_id'] = self.partner_id_list[sel]
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner.address','create',res)
        return id

    def CreatePartner(self, res):
        conn = xmlrpclib.ServerProxy(self._uri+ '/xmlrpc/object')
        ids = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','search',[('name','=',res['name'])])
        if ids:
            return False
        id = execute(conn,'execute',self._dbname,int(self._uid),self._pwd,'res.partner','create',res)
        return id
