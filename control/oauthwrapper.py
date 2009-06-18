# Copyright (c) 2008-2009 Cambridge Visual Networks
 
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.


import cgi
import datetime
import httplib
import os
import simplejson
import time
import urllib

from oauth import OAuthRequest, OAuthSignatureMethod_HMAC_SHA1, \
    OAuthConsumer, OAuthToken

from nabaztag import settings
from nabaztag.control.models import  *

##############################################################################
#        
def _data_to_dict(data):
    tuple_list = cgi.parse_qsl(data)
    d = {}
    for t in tuple_list:
        d[t[0]] = t[1]
    return d
#
##############################################################################


##############################################################################
#        
def _split_server_parts(url):
    
    request_type, rest = urllib.splittype(url)
    fullhost, path = urllib.splithost(rest)
    host, port = urllib.splitport(fullhost)
    
    port_default = {'http': '80', 'https': '443'}[request_type.lower()]
    
    return request_type, host, int(port or port_default), path
#
##############################################################################


##############################################################################
#        
def get_request_token():
    """Talk to the remote server to get an OAUTH REQUEST TOKEN"""
    
    url = settings.CODA_SERVER + 'oauth/request_token/'
    request_type, host, port, path = _split_server_parts(url)
    
    parameters = {
            'oauth_consumer_key': settings.CODA_KEY,
            'oauth_signature_method': 'PLAINTEXT',
            'oauth_signature': '%s&' % settings.CODA_SECRET,
            'oauth_timestamp': str(int(time.time())),
            'oauth_nonce': os.urandom(10).encode('hex'),
            'oauth_version': '1.0',
        }
        
    if request_type == 'http':
        conn = httplib.HTTPConnection(host, port)
    else:        
        conn = httplib.HTTPSConnection(host, port)
    conn.putrequest('POST', path)
    
    data = ''
    for key in parameters.keys():
        data += '%s=%s&' % (key, urllib.quote(parameters[key]))
    data = data[:-1]

    conn.putheader('content-length', str(len(data)))
    conn.endheaders()
    conn.send(data)
    conn.send('\n\r\n\r')
    
    resp = conn.getresponse()

    data = resp.read()
    
    if resp.status == 200:
        data = _data_to_dict(data)
        r = RequestToken.objects.create(key=data['oauth_token'],
                secret=data['oauth_token_secret'],
                created=datetime.datetime.now())
        r.save()
        
        return r
    else:
        return None
#
##############################################################################



##############################################################################
#        
def get_access_token(user, request_token):
    """Talk to the remote server to get an OAUTH AUTH TOKEN"""
    
    url = settings.CODA_SERVER + 'oauth/access_token/'
    request_type, host, port, path = _split_server_parts(url)
    
    
    parameters = {
        'oauth_consumer_key':  settings.CODA_KEY,
        'oauth_token': request_token.key,
        'oauth_signature_method': 'PLAINTEXT',
        'oauth_signature': '%s&%s' % (settings.CODA_SECRET, request_token.secret),
        'oauth_timestamp': str(int(time.time())),
        'oauth_nonce': os.urandom(10).encode('hex'),
        'oauth_version': '1.0',
        }
        
        
    # Request Tokens should only ever be used once, so kill the token now.
    request_token.delete()
        
        
    if request_type == 'http':
        conn = httplib.HTTPConnection(host, port)
    else:        
        conn = httplib.HTTPSConnection(host, port)
    conn.putrequest('POST', path)
    
    data = ''
    for key in parameters.keys():
        data += '%s=%s&' % (key, urllib.quote(parameters[key]))
    data = data[:-1]
    
    conn.putheader('content-length', str(len(data)))
    conn.endheaders()
    conn.send(data)
    conn.send('\n\r\n\r')
    
    resp = conn.getresponse()

    data = resp.read()
    
    if resp.status == 200:
        
        # we now have an auth token, so store that for future use
        
        data = _data_to_dict(data)
        
        # we need to stash this for the future
        access_token = RemoteToken.objects.create(key=data['oauth_token'],
            secret=data['oauth_token_secret'], user=user)
            
        # we no longer need the request token (which should be one time anyway)
        return access_token   
    else:
        return None
#
##############################################################################


##############################################################################
#
def make_api_request(access_token, url, data=None):
    
    # break down the url, as we'll need to later
    request_type, host, port, path = _split_server_parts(url)
    
    parameters = {
        'oauth_consumer_key': settings.CODA_KEY,
        'oauth_token': access_token.key,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(int(time.time())),
        'oauth_nonce': os.urandom(10).encode('hex'),
        'oauth_version': '1.0',
        'format': 'json',
        }
        
    # data should be a dict of things
    if data:
        for k in data.keys():
            parameters[k] = data[k]
        
    newurl = '%s://%s:%d%s' % (request_type, host, port, path)
    #newurl = '%s://%s%s' % (request_type, host, port, path)
        
    oauth_request = OAuthRequest.from_token_and_callback(access_token,  
        http_method="POST",
        http_url=newurl, 
        parameters=parameters)
    signature_method = OAuthSignatureMethod_HMAC_SHA1()
    consumer = OAuthConsumer(settings.CODA_KEY, settings.CODA_SECRET)
    access_token_t = OAuthToken(access_token.key, access_token.secret)
    signature = signature_method.build_signature(oauth_request, consumer,
        access_token_t)
    
    parameters['oauth_signature'] = signature
    
    if request_type == 'http':
        conn = httplib.HTTPConnection(host, port)
    else:        
        conn = httplib.HTTPSConnection(host, port)
    conn.putrequest('POST', path)

    data = ''
    for key in parameters.keys():
        data += '%s=%s&' % (key, urllib.quote(parameters[key]))
    data = data[:-1]

    print data

    conn.putheader('content-length', str(len(data)))
    conn.endheaders()
    conn.send(data)
    conn.send('\n\r\n\r')

    resp = conn.getresponse()

    data = resp.read()
        
    print data
        
    return simplejson.loads(data)    
#
##############################################################################


