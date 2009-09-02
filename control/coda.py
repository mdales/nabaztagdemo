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


from nabaztag import settings
from nabaztag.control.oauthwrapper import *

BASE_CODA_URL="https://coda.camvine.com/external/json/"


##############################################################################
#        
def get_display_list(access_token):
    
    reply = make_api_request(access_token,
            BASE_CODA_URL + "getDisplays/")
        
    if reply['result'] == 'OK':            
        response = reply['response']
        response.sort(key=lambda x: x['name'])
        return response
    else:
        return []
#
##############################################################################


##############################################################################
#        
def get_source_list(access_token):
    
    reply = make_api_request(access_token,
            BASE_CODA_URL + "getSources/")
        
    if reply['result'] == 'OK':            
        response = reply['response']
        response.sort(key=lambda x: x['name'])
        return response
    else:
        return []
#
##############################################################################


##############################################################################
#        
def set_source_for_display(access_token, source_uuid, display_uuid):
    reply = make_api_request(access_token, BASE_CODA_URL + "assignSource/",
        {'display_uuid': display_uuid, 'source_uuid': source_uuid})
    return reply
#
##############################################################################

