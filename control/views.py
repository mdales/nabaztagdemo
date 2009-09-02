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


from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils.encoding import DjangoUnicodeDecodeError
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django import forms

from nabaztag.control.models import RFIDTag, TagDisplaySourceMapping, RemoteToken, OneDisplay

from nabaztag.control.oauthwrapper import *
from nabaztag.control.coda import *

##############################################################################
#
def tag_access(request):

    tagid = request.GET['serial']
    tagname = request.GET['tag']
    username = request.GET['username']

    user = get_object_or_404(User, username=username)

    # does this tag exist in our system? is, make stuff happen, if not,
    # add it to the database
    try:
        tag = RFIDTag.objects.get(serial_number=tagid)

        binding_list = TagDisplaySourceMapping.objects.filter(tag=tag)

        for binding in binding_list:
            for display in binding.displays.all():
                set_source_for_display(binding.token, binding.source_uuid,
                                       display.uuid)

    except RFIDTag.DoesNotExist:

        # not seen this tag before, so record its existance
        tag = RFIDTag.objects.create(user=user,
            name=tagname,
            serial_number=tagid)
        tag.save()

    # violet.com don't mind what you send back
    return HttpResponse('hello, world\n')
#
##############################################################################


##############################################################################
#
@login_required
def status(request):


    user = request.user

    # does the user have any tags?
    tag_list = RFIDTag.objects.filter(user=user)

    # have they registered with CODA yet?
    token_list = RemoteToken.objects.filter(user=user)


    return render_to_response('status.html',
        {'tag_list': tag_list,
        'token_list': token_list,
        'auth': len(token_list) > 0},
        context_instance=RequestContext(request))
#
##############################################################################


##############################################################################
#
@login_required
def instructions(request):
    return render_to_response('add_tag.html',
        {},
        context_instance=RequestContext(request))
#
##############################################################################


##############################################################################
#
@login_required
def coda_pre_auth(request):

    return render_to_response('preauth.html',
        {},
        context_instance=RequestContext(request))

#
##############################################################################


##############################################################################
#
def coda_auth(request):

    # when we get here we start the auth process with the CODA Server
    request_token = get_request_token()

    if request_token != None:

        request = 'oauth_token=%s&oauth_callback=%s' % (request_token.key,
                urllib.quote('%s/auth/done/' % settings.OAUTH_CALLBACK))

        return HttpResponseRedirect("%soauth/authorize/?%s" % (settings.CODA_SERVER, request))
    else:
        return render_to_response('preauthfail.html',
            {},
            context_instance=RequestContext(request))
#
##############################################################################


##############################################################################
#
def coda_auth_done(request):

    # we get the request token passed as a GET param
    token_key = request.GET['oauth_token']

    request_token = get_object_or_404(RequestToken, key=token_key)

    access_token = get_access_token(request.user, request_token)

    if access_token:
        return render_to_response('authwin.html', {},
            context_instance=RequestContext(request))
    else:
        return render_to_response('preauthfail.html',
            {},
            context_instance=RequestContext(request))
#
##############################################################################


##############################################################################
#
class TagSettingsForm(forms.Form):
    source = forms.ChoiceField(required=False)
    displays = forms.MultipleChoiceField(required=False,
                                        widget=forms.CheckboxSelectMultiple)

def tag_setup(request, tag_id):

    # what we do now depends on whether we have a token to access CODA
    try:
        access_token = RemoteToken.objects.filter(user=request.user)[0]
    except IndexError:
        return render_to_response('tag_info.html', {'tag': tag},
            context_instance=RequestContext(request))

    # get the tag in question
    tag = get_object_or_404(RFIDTag, pk=tag_id)

    try:
        tag_mapping = TagDisplaySourceMapping.objects.get(tag=tag)
    except TagDisplaySourceMapping.DoesNotExist:
        tag_mapping = None

    if request.method == "POST":

        form = TagSettingsForm(request.POST)

        display_list = get_display_list(access_token)
        source_list = get_source_list(access_token)
        form.fields['displays'].choices = [(x['display_uuid'], x['name']) for x in display_list]
        form.fields['source'].choices = [(x['source_uuid'], x['name']) for x in source_list]

        if form.is_valid():
            display_uuids = form.cleaned_data['displays']
            source_uuid = form.cleaned_data['source']

            if not tag_mapping:
                tag_mapping = TagDisplaySourceMapping.objects.create(token=access_token,
                                                                     tag=tag,
                                                                     source_uuid=source_uuid)
            else:
                tag_mapping.source_uuid = source_uuid

            tag_mapping.displays.clear()
            for uuid in display_uuids:
                d, _ = OneDisplay.objects.get_or_create(uuid=uuid)
                tag_mapping.displays.add(d)

            tag_mapping.save()
            print tag_mapping

            return HttpResponseRedirect("/")

    else:

        # now we need to get a list of displays that the user can use
        # and a list of sources they can use

        if tag_mapping:
            form = TagSettingsForm(initial={'displays': [d.uuid for d in tag_mapping.displays.all()],
                                            'source': tag_mapping.source_uuid})
            print [d.uuid for d in tag_mapping.displays.all()]

        else:
            form = TagSettingsForm()


        display_list = get_display_list(access_token)
        source_list = get_source_list(access_token)
        form.fields['displays'].choices = [(x['display_uuid'], x['name']) for x in display_list]
        form.fields['source'].choices = [(x['source_uuid'], x['name']) for x in source_list]

    return render_to_response("tag_edit.html",
        {'tag': tag,
        'form': form},
        context_instance=RequestContext(request))

#
##############################################################################
