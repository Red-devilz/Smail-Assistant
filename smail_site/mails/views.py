from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader

from oauth2client import client
import httplib2

from classifier.api import *
from classifier.minified_classifier import get_mails
from classifier.main import get_all_mail, get_html_message, get_mails_from_db, get_mails_by_class
import json

from mails.models import GoogleUser, Mails


def index(request):
    if 'cred' not in request.session:
        return redirect('login')
    credentials = client.OAuth2Credentials.from_json(request.session['cred'])
    if credentials.access_token_expired:
        return redirect('login')
    # get emails
    # http_auth = credentials.authorize(httplib2.Http())
    # gmail_service = make_gmail_service(http_auth)
    # label_dict, mail_dict = get_all_mail(gmail_service, 10)
    # msgs = list_gmail_messages(gmail_service)
    # msgs = list_gmail_messages(gmail_service)  # get list of msgs
    # s = []
    # s.append('Displaying first %d messages' % (msgs["resultSizeEstimate"]))
    # for msg in msgs["messages"]:
    #     msg = get_gmail_message(gmail_service, msg["id"])
    #     s.append("Message:\n %s" %(msg['snippet']))  # print msg.snippet
    all_mails = get_mails_from_db(credentials.id_token['email'])
    template = loader.get_template('mails/index.html')
    # json.dump([label_dict, mail_dict], open("mails.json", "w"))
    context = {
        'mails_list': list([get_html_message(msg) for msg in all_mails]),
    }

    return HttpResponse(template.render(context, request))

flow = client.flow_from_clientsecrets(
    'client_secret.json',
    scope=[
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/calendar'
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
    cur_email = credentials.id_token['email']
    users = GoogleUser.objects.filter(email=cur_email)
    if(len(users) == 0):
        new_user = GoogleUser(email=cur_email, google_id=cur_email.split('@')[0])
        new_user.save()
    cur_user = GoogleUser.objects.get(email=cur_email)
    http_auth = credentials.authorize(httplib2.Http())
    gmail_service = make_gmail_service(http_auth)
    label_dict, mail_dict = get_all_mail(gmail_service, 20)
    for category in label_dict.keys():
        for key in label_dict[category]:
            new_mail = Mails(user=cur_user, msg_id=key, message=mail_dict[
                             key]['raw']['raw'], category=category)
            new_mail.save()
    request.session['cred'] = credentials.to_json()
    return redirect('index')


def logout(request):
    del request.session['cred']
    return redirect('index')


def classify(request, category_id):
    if 'cred' not in request.session:
        return redirect('login')
    credentials = client.OAuth2Credentials.from_json(request.session['cred'])
    if credentials.access_token_expired:
        return redirect('login')
    cur_mails = get_mails_by_class(credentials.id_token['email'], category_id)
    template = loader.get_template('mails/categories.html')
    context = {
        'mails_list': list([get_html_message(msg) for msg in cur_mails]),
        'category': category_id,
    }

    return HttpResponse(template.render(context, request))


def addCal(request):
    credentials = client.OAuth2Credentials.from_json(request.session['cred'])
    cal_service = make_calender_service(http_auth=credentials.authorize(httplib2.Http()))
    # events = list_calendar_events(cal_service)
    data = {
        "name": "Endsem",
        "start": "2016-11-15T09:30:00+05:30",
        "end": "2016-11-15T12:30:00+05:30"
    }
    events = create_calendar_event(cal_service, data)
    return HttpResponse(str(events))
