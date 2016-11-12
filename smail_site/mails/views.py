from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader

from oauth2client import client
import httplib2

from classifier.api import *
from classifier.minified_classifier import get_mails
from classifier.main import get_all_mail, get_html_message
import json


def index(request):
    if 'cred' not in request.session:
        return redirect('login')
    credentials = client.OAuth2Credentials.from_json(request.session['cred'])
    if credentials.access_token_expired:
        return redirect('login')
    # get emails
    http_auth = credentials.authorize(httplib2.Http())
    gmail_service = make_gmail_service(http_auth)
    label_dict, mail_dict = get_all_mail(gmail_service, 20)
    # msgs = list_gmail_messages(gmail_service)
    # msgs = list_gmail_messages(gmail_service)  # get list of msgs
    # s = []
    # s.append('Displaying first %d messages' % (msgs["resultSizeEstimate"]))
    # for msg in msgs["messages"]:
    #     msg = get_gmail_message(gmail_service, msg["id"])
    #     s.append("Message:\n %s" %(msg['snippet']))  # print msg.snippet
    template = loader.get_template('mails/index.html')
    json.dump([label_dict, mail_dict], open("mails.json", "w"))
    context = {
        'mails_list': list([get_html_message(msg["raw"]["raw"]) for msg in mail_dict.values()]),
    }

    return HttpResponse(template.render(context, request))

flow = client.flow_from_clientsecrets(
    'client_secret.json',
    scope=[
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ],
    redirect_uri='http://localhost:8000/mails/oauth2callback')
flow.params['access_type'] = 'offline'


def login(request):
    auth_uri = flow.step1_get_authorize_url()  # init oauth
    return redirect(auth_uri)


def oauth2callback(request):
    auth_code = request.GET['code']
    print('got code', auth_code)
    credentials = flow.step2_exchange(auth_code)
    print('cred', credentials)
    request.session['cred'] = credentials.to_json()
    return redirect('index')


def logout(request):
    del request.session['cred']
    return redirect('index')
