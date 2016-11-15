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

categoryCount = {}

categoryMap = {
    'cat0': 'Seminars',
    'cat1': 'Sports',
    'cat2': 'Hostel Affairs',
    'cat3': 'Cultural/Literary',
    'cat4': 'Academic',
    'cat5': 'Moodle',
    'cat6': 'Research Affairs',
    'cat7': 'General',
    'cat8': 'Hostel Mail',
    'cat9': 'Miscellaneous',
    'cat10': 'Announcements',
    'cat11': 'CSE IITM',
}


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
        'mails_list': list([dict({'from': msg.sender, 'subject': msg.subject, 'snippet': msg.snippet, 'msg_id': msg.msg_id}) for msg in all_mails if msg.sender != '']),
        'categoryCount': categoryCount,
        'categoryMap': categoryMap,
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
    label_dict, mail_dict = get_all_mail(gmail_service, 15)
    print(label_dict)
    for x in label_dict.keys():
        categoryCount['cat' + x] = len(label_dict[x])
    for category in label_dict.keys():
        for key in label_dict[category]:
            check_mail = Mails.objects.filter(user=cur_user, msg_id=key)
            if(len(check_mail) > 0):
                old_mail = Mails.objects.get(user=cur_user, msg_id=key)
                old_mail.message = mail_dict[key]['raw']['raw']
                old_mail.category = category
                old_mail.snippet = mail_dict[key]['raw']['snippet']
                old_mail.sender = mail_dict[key]['processed']['from']
                old_mail.subject = mail_dict[key]['processed']['subject']
                old_mail.save()
            else:
                new_mail = Mails(user=cur_user, msg_id=key, message=mail_dict[key]['raw']['raw'], category=category, snippet=mail_dict[
                                 key]['raw']['snippet'], sender=mail_dict[key]['processed']['from'], subject=mail_dict[key]['processed']['subject'])
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
        'mails_list': list([dict({'from': msg.sender, 'subject': msg.subject, 'snippet': msg.snippet, 'msg_id': msg.msg_id}) for msg in cur_mails if msg.sender != '']),
        'category': category_id,
        'categoryCount': categoryCount,
        'categoryMap': categoryMap,
    }
    # cur_mail = Mails.objects.get(msg_id='15867d7f152bc9ff')
    # print(cur_mail, get_html_message(cur_mail.message))
    return HttpResponse(template.render(context, request))


def display(request, msg_id):
    if 'cred' not in request.session:
        return redirect('login')
    credentials = client.OAuth2Credentials.from_json(request.session['cred'])
    if credentials.access_token_expired:
        return redirect('login')
    cur_mail = Mails.objects.get(msg_id=msg_id)
    template = loader.get_template('mails/singlemail.html')
    if msg_id == '15867d7f152bc9ff':
        print(cur_mail, get_html_message(cur_mail.message))
    context = {
        'mail': get_html_message(cur_mail.message),
        'categoryCount': categoryCount,
        'categoryMap': categoryMap,
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
