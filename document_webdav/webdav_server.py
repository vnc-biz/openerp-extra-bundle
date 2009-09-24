import BaseHTTPServer
import DAV
import os

from xml.dom import ext

import netsvc
from dav_auth import tinyerp_auth
from dav_fs import tinyerp_handler
from tools.config import config

from tools.misc import ustr,exception_to_unicode
import threading
import pooler

class dav_server(threading.Thread):
    def __init__(self):
        super(dav_server,self).__init__()
        self.host = config.get('webdav_host','localhost')
        self.port = int(config.get('webdav_port',8008))
        self.db_name = config.get('webdav_db_name',False)
        self.directory_id = config.get('webdav_directory_id',False)

    def log(self,level,msg):
        """ An independent log() that will release the logger upon return
        """
        logger = netsvc.Logger()
        logger.notifyChannel('webdav', level, msg)
        
    def run(self):
        server = BaseHTTPServer.HTTPServer
        handler = tinyerp_auth
        handler.db_name = self.db_name
        handler.IFACE_CLASS  = tinyerp_handler( self.host,self.port,  True )
        handler.IFACE_CLASS.parent = self
        handler.verbose = config.get('webdav_verbose',True)
        handler.debug = config.get('webdav_debug',True)
        try:
            self.log(netsvc.LOG_INFO,"Starting WebDAV service at %s:%d" % (self.host,self.port))
            runner = server( (self.host, self.port), handler )
            runner.serve_forever()
        except Exception, e:
            raise

try:
    if (config.get('webdav_enable',True)):
        ds = dav_server()
        ds.start()
except Exception, e:
    logger = netsvc.Logger()
    logger.notifyChannel('webdav', netsvc.LOG_ERROR, 'Cannot launch webdav: %s' % exception_to_unicode(e))

