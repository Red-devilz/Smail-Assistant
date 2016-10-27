from django.http import HttpResponse
from django.shortcuts import render, redirect

from oauth2client import client


def index(request):
    return HttpResponse("Click <a href='/mails/login'>here</a> to  login.")

flow = client.flow_from_clientsecrets(
    'client_secret.json',
    scope=[
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ],
    redirect_uri='http://localhost:8000/mails/oauth2callback')
flow.params['access_type'] = 'offline'


def login(request):
    if 'cred' in request.session:
        credentials = client.OAuth2Credentials.from_json(request.session['cred'])
        return HttpResponse("session %s" % request.session['cred'])
    print("oauth")
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
