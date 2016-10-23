import json

from oauth2client import client
import httplib2

from api import *
from flask import Flask, redirect, request, session

app = Flask(__name__)

flow = client.flow_from_clientsecrets(
    'client_secret.json',
    scope=[
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ],
    redirect_uri='http://localhost:8000/oauth2callback')
flow.params["access_type"] = "online"


@app.route("/")
def root():
    if 'cred' in session:
        print("have creds")
        credentials = client.OAuth2Credentials.from_json(session['cred'])  # get creds
        if credentials.access_token_expired:
            auth_uri = flow.step1_get_authorize_url()  # init oauth
            return redirect(auth_uri)
        http_auth = credentials.authorize(httplib2.Http())
        gservice = make_gmail_service(http_auth)
        msgs = list_gmail_messages(gservice)  # get list of msgs
        s = 'got %d messages<br>' % (msgs["resultSizeEstimate"])
        for msg in msgs["messages"]:
            msg = get_gmail_message(gservice, msg["id"])
            s = s + ("message.snippet: %s<br/>" % (msg['snippet']))  # print msg.snippet
        return s
    else:
        print("getting auth")
        auth_uri = flow.step1_get_authorize_url()  # init oauth
        return redirect(auth_uri)


@app.route("/oauth2callback")
def oauth_handler():
    print(request.args)
    if 'error' in request.args:
        del session['cred']
        return 'error'
    else:
        auth_code = request.args['code']
        credentials = flow.step2_exchange(auth_code)
        session['cred'] = credentials.to_json()  # store credentials in session
        return redirect('/')
    return "got it"


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.secret_key = 'sldakjhbp8263qweuq;eq612e817'
    app.run(debug=True, port=8000)
