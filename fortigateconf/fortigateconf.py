#!/usr/bin/env python

###################################################################
#
# fortiosconf.py aims at simplyfing the configuration and 
# integration of Fortgate configuration using the restapi
#
# A Python module to abstract configuration using FortiOS REST API 
#
###################################################################

import requests
#Disable warnings.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import json
# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

# create logger
LOG = logging.getLogger('fortinetconflib')

class FortiOSConf(object):
    def __init__(self):
        self._https = True
        self._session = requests.session() # use single session

    def logging(self, response):
        LOG.debug("Request : %s on url : %s  ",response.request.method,
                      response.request.url) 
        LOG.debug("Response : http code %s  reason : %s  ", response.status_code,response.reason)
        
        content=response.content
        if content is not 'null':
            if content is not None:
                try:
                    j = json.loads(content)
                except (ValueError,TypeError):
                    LOG.debug("Response raw content:  %s ", content)
                else:
                    if response.status_code is 200 :
                        LOG.debug("Response results content:  %s ", j['results'])
                    else:
                        LOG.debug("Response results content:  %s ", j)
                        
    def debug(self, status):
        if status == 'on':
          LOG.setLevel(logging.DEBUG)
      
    def https(self, status):
        if status == 'on':
          self._https = True
        if status == 'off':
          self._https = False

    def update_cookie(self):
        # Retrieve server csrf and update session's headers
        for cookie in self._session.cookies:
            if cookie.name == 'ccsrftoken':
                csrftoken = cookie.value[1:-1] # token stored as a list
                LOG.debug("csrftoken before update  : %s ", cookie) 
                self._session.headers.update({'X-CSRFTOKEN': csrftoken})
                LOG.debug("csrftoken after update  : %s ", cookie) 

    def login(self,host,username,password):
        self.host = host
        if self._https is True:
            self.url_prefix = 'https://' + self.host
        else:
            self.url_prefix = 'http://' + self.host
        url = self.url_prefix + '/logincheck'
        res = self._session.post(url,
                                data='username='+username+'&secretkey='+password,
                                verify=False)
        self.logging(res)

        # Update session's csrftoken
        self.update_cookie()

    def logout(self):
        url = self.url_prefix + '/logout'
        res = self._session.post(url,verify=False)

        self.logging(res)


    def cmdb_url(self, path, name, vdom, mkey):
      
        # return builded URL
        url_postfix = '/api/v2/cmdb/' + path + '/' + name
        if vdom:
            url_postfix += '/?vdom=' + vdom
        if mkey:
            url_postfix = url_postfix + '/' + str(mkey)
        url = self.url_prefix + url_postfix
        return url

    def get_webui(self, url_postfix, parameters=None):
        url = self.url_prefix + url_postfix
        res = self._session.get(url,params=parameters)
        self.logging(res)        
        return res.content    

    def get(self, path, name, vdom=None, mkey=None, parameters=None):
        url = self.cmdb_url(path, name, vdom, mkey)
        res = self._session.get(url,params=parameters)
        self.logging(res)
        return res.content

    def schema(self, path, name, vdom=None, mkey=None, parameters=None):
        url = self.cmdb_url(path, name, vdom, mkey)+"?action=schema"
        res = self._session.get(url,params=parameters)
        self.logging(res)
        if res.status_code is 200 :
            return json.loads(res.content)['results']
        else:
            return json.loads(res)
       

    def post(self, path, name, vdom=None, mkey=None, parameters=None, data=None):
        url = self.cmdb_url(path, name, vdom, mkey)
        res = self._session.post(url,params=parameters,data=json.dumps(data),verify = False)            
        self.logging(res)
        return res.content

    def put(self, path, name, vdom=None, mkey=None, parameters=None, data=None):
        url = self.cmdb_url(path, name, vdom, mkey)
        res = self._session.put(url,params=parameters,data=json.dumps(data),verify=False)            
        self.logging(res) 
        return res.content

    def delete(self, path, name, vdom=None, mkey=None, parameters=None, data=None):
        url = self.cmdb_url(path, name, vdom, mkey)
        res = self._session.delete(url,params=parameters,data=json.dumps(data))            
        self.logging(res)
        return res.content
# Set will try to post if err code is 424 will try put (ressource exists)
#may add a force option to delete and redo if troubles.

    def set(self, path, name, vdom=None, mkey=None, parameters=None, data=None):
        url = self.cmdb_url(path, name, vdom, mkey)
        res = self._session.post(url,params=parameters,data=json.dumps(data))            
        self.logging(res)
        return res.content
