# -*- coding: utf-8 -*-

"""
Copyright (C) 2013 Dariusz Suchojad <dsuch at gefira.pl>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
from unittest import TestCase

# anyjson
from anyjson import dumps, loads

# lxml
from lxml import etree, objectify

# nose
from nose.tools import eq_

# Zato
from zato.common import common_namespaces, ZATO_OK
from zato.common.test import rand_bool, rand_int, rand_object, rand_string
from zato.common.util import new_cid
from zato.client import AnyServiceInvoker, JSONClient, JSONSIOClient, RawDataClient, \
     _Response, SOAPClient, SOAPSIOClient,  _StructuredResponse, XMLClient
     
# - AnyServiceInvoker
# + JSONClient
# + JSONSIOClient
# + RawDataClient
# + SOAPClient
# + SOAPSIOClient
# + XMLClient

# ##############################################################################

class FakeInnerResponse(object):
    def __init__(self, headers, ok, text, status_code):
        self.headers = headers
        self.ok = ok
        self.text = text
        self.status_code = status_code

class FakeSession(object):
    def __init__(self, response=None):
        self.response = response
        
    def post(self, address, request, headers):
        return self.response
    
# ##############################################################################

class _Base(TestCase):
    client_class = None
    
    def setUp(self):
        self.url = rand_string()
        self.auth = None
        self.path = rand_string()
        self.session = FakeSession()
        self.to_bunch = rand_bool()
        self.max_response_repr = 10000
        self.max_cid_repr = rand_int()
        self.logger = rand_object()
        
    def get_client(self, response):
        self.session.response = response
        
        return self.client_class(self.url, self.auth, self.path, self.session,
            self.to_bunch, self.max_response_repr, self.max_cid_repr)

# ##############################################################################
            
class JSONClientTestCase(_Base):
    client_class = JSONClient
    
    def test_client(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        text = dumps({rand_string(): rand_string()})
        status_code = rand_int()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke()
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(response.data.items(), loads(text).items())
        eq_(response.has_data, True)
        eq_(response.cid, cid)
        
class XMLClientTestCase(_Base):
    client_class = XMLClient
    
    def test_client(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        text = '<abc>{}</abc>'.format(rand_string())
        status_code = rand_int()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke()
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(etree.tostring(response.data), text)
        eq_(response.has_data, True)
        eq_(response.cid, cid)
        
class SOAPClientTestCase(_Base):
    client_class = SOAPClient
    
    def test_client_ok(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        _rand = rand_string()
        soap_action = rand_string()
        
        text = """
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
             <soapenv:Body>
              <abc>{}</abc>
             </soapenv:Body>
            </soapenv:Envelope>""".format(_rand).strip()
        status_code = rand_int()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke(soap_action)

        expected_response_data = """
            <abc xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">{}</abc>
            """.format(_rand).strip()
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(etree.tostring(response.data), expected_response_data)
        eq_(response.has_data, True)
        eq_(response.cid, cid)
        
    def test_client_no_soap_response(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = False
        soap_action = rand_string()
        
        text = '<abc/>'
        status_code = rand_int()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke(soap_action)
        
        eq_(response.ok, ok)
        eq_(response.details, 'No /soapenv:Envelope/soapenv:Body/*[1] in SOAP response')
        eq_(response.inner.text, text)
        eq_(response.has_data, False)
        eq_(response.cid, cid)
        
# ##############################################################################
        
class JSONSIOClientTestCase(_Base):
    client_class = JSONSIOClient
    
    def test_client(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        
        env = {
            'details': rand_string(),
            'result': ZATO_OK,
            'cid': cid
        }
        
        sio_payload_key = rand_string()
        sio_payload = {rand_string(): rand_string()}
        
        sio_response = {
            'zato_env': env,
            sio_payload_key: sio_payload
        }
        
        text = dumps(sio_response)
        status_code = rand_int()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke()
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(response.data.items(), sio_response[sio_payload_key].items())
        eq_(response.has_data, True)
        eq_(response.cid, cid)
        eq_(response.cid, sio_response['zato_env']['cid'])
        eq_(response.details, sio_response['zato_env']['details'])
        
class SOAPSIOClientTestCase(_Base):
    client_class = SOAPSIOClient
    
    def test_client_ok(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        status_code = rand_int()
        rand_id, rand_name, soap_action = rand_string(), rand_string(), rand_string()

        sio_response = """<zato_outgoing_amqp_edit_response xmlns="http://gefira.pl/zato">
           <zato_env>
            <cid>{}</cid>
            <result>ZATO_OK</result>
           </zato_env>
           <item>
            <id>{}</id>
            <name>crm.account</name>
           </item>
          </zato_outgoing_amqp_edit_response>
        """.format(cid, rand_id, rand_name)

        text = """<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns="http://gefira.pl/zato">
             <soap:Body>
              {}
             </soap:Body>
            </soap:Envelope>""".format(sio_response).strip()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke(soap_action)
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(response.has_data, True)
        eq_(response.cid, cid)

        path_items = (
            ('zato_env', 'cid'),
            ('zato_env', 'result'),
            ('item', 'id'),
            ('item', 'name'),
        )
        
        for items in path_items:
            path = '//zato:zato_outgoing_amqp_edit_response/zato:' + '/zato:'.join(items)
            xpath = etree.XPath(path, namespaces=common_namespaces)
            
            expected = xpath(etree.fromstring(text))[0].text
            actual = xpath(response.data)[0]
            
            self.assertEquals(expected, actual)
            
    def test_client_soap_fault(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = False
        status_code = rand_int()
        soap_action = rand_string()

        text = b"""<?xml version='1.0' encoding='UTF-8'?>
 <SOAP-ENV:Envelope
   xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
   xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance"
   xmlns:xsd="http://www.w3.org/1999/XMLSchema">
    <SOAP-ENV:Body>
      <SOAP-ENV:Fault>
      <faultcode>SOAP-ENV:Client</faultcode>
 <faultstring><![CDATA[cid [K68438211212681798524426103126], faultstring
 [Traceback (most recent call last):
File
"/opt/zato/code/zato-server/src/zato/server/connection/http_soap/
channel.py", line 126, in dispatch
  service_info, response = handler.handle(cid, wsgi_environ, payload, transport,
  worker_store, self.simple_io_config, data_format, path_info)
File
"/opt/zato/code/zato-server/src/zato/server/connection/http_soap/
channel.py", line 227, in handle
  service_instance.handle()
File
"/opt/zato/code/zato-server/src/zato/server/service/internal/
definition/amqp.py", line 174, in handle
  filter(ConnDefAMQP.id==self.request.input.id).\
File
"/opt/zato/code/eggs/SQLAlchemy-0.7.9-py2.7-linux-x86_64.egg/sqlalchemy/
orm/query.py", line 2190, in one
  raise orm_exc.NoResultFound("No row was found for one()")
NoResultFound: No row was found for one()
]]]></faultstring>
       </SOAP-ENV:Fault>
   </SOAP-ENV:Body>
 </SOAP-ENV:Envelope>"""
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke(soap_action)
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(response.has_data, False)
        eq_(response.cid, cid)
        eq_('NoResultFound: No row was found for one()' in response.details.getchildren()[1].text, True)

# ##############################################################################

class AnyServiceInvokerTestCase(_Base):
    client_class = AnyServiceInvoker
    
    def test_client(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        status_code = rand_int()
        
        service_name = rand_string()
        service_response_name = '{}_response'.format(service_name)
        service_response_payload = {'service_id':5207, 'has_wsdl':True}
        service_response_dict = {'zato_service_has_wsdl_response':service_response_payload}
        service_response = dumps(service_response_dict).encode('base64')
        
        text = dumps({
            'zato_env':{'result':ZATO_OK, 'details':''},
            service_response_name: {
                'response':service_response
            }
        })
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke(service_name)
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(response.data.items(), service_response_payload.items())
        eq_(response.has_data, True)
        eq_(response.cid, cid)
        
# ##############################################################################

class RawDataClientTestCase(_Base):
    client_class = RawDataClient
    
    def test_client(self):

        cid = new_cid()
        headers = {'x-zato-cid':cid}
        ok = True
        text = rand_string()
        status_code = rand_int()
        
        client = self.get_client(FakeInnerResponse(headers, ok, text, status_code))
        response = client.invoke()
        
        eq_(response.ok, ok)
        eq_(response.inner.text, text)
        eq_(response.data, text)
        eq_(response.has_data, True)
        eq_(response.cid, cid)

# ##############################################################################

class NotImplementedErrorTestCase(_Base):
    
    def test_not_implemented_error(self):
        inner = FakeInnerResponse({}, rand_int(), rand_string(), rand_int())
        response_data = (inner, rand_bool(), rand_int(), rand_int())
        
        self.assertRaises(NotImplementedError, _Response, *response_data)
        self.assertRaises(NotImplementedError, _StructuredResponse(*response_data).load_func)
        self.assertRaises(NotImplementedError, _StructuredResponse(*response_data).set_has_data)