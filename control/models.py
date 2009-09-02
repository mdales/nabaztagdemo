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
 

from django.db import models
from django.contrib.auth.models import User

##############################################################################
#
class RequestToken(models.Model):
    """A token for the initial OAuth request. Stored in db as it needs to 
    survive past a call back invocation, but shouldn't last long."""
    
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    
    # keep a note of this, as failed callbacks may require GCing
    created = models.DateTimeField()
    
    def __unicode__(self):
        return "token %s/%s made at %s" % (self.key, self.secret, self.created)
#
##############################################################################


##############################################################################
#
class RemoteToken(models.Model):
    """This is the OAuth Access Token. In this system we associate it with 
    a particular user."""
    
    user = models.ForeignKey(User)
    
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)
    
    def __unicode__(self):
       return "token %s for user %s" % (self.key, self.user.username)
#
##############################################################################


##############################################################################
#   
class RFIDTag(models.Model):
    """Here we record the Nabaztag tag id and its name - we need to tell the
    user what URL to paste in the Nabaztag website to ensure we get the info
    that we want."""
    
    user = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=32)
    
    def __unicode__(self):
        return "tag %s for user %s" % (self.name, self.user.username)
#
##############################################################################


##############################################################################
#   
class OneDisplay(models.Model):
    uuid = models.CharField(max_length=36)
#
##############################################################################


##############################################################################
#   
class TagDisplaySourceMapping(models.Model):
    """This maps a Tag to a Display/Source mapping. There may be multiple
    mappings per tag."""
    
    tag = models.ForeignKey(RFIDTag)
    token = models.ForeignKey(RemoteToken)
    
    # Here we store the id's that CODA gives us for the sources and displays
    displays = models.ManyToManyField(OneDisplay)
    source_uuid = models.CharField(max_length=36)
#
##############################################################################
