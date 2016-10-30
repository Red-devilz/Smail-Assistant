import json

from oauth2client import client
import httplib2

from api import *
from flask import Flask, redirect, request, session

import base64
import email

app = Flask(__name__)

flow = client.flow_from_clientsecrets(
    'client_secret.json',
    scope=[
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email'
    ],
    redirect_uri='http://localhost:8000/oauth2callback')
flow.params["access_type"] = "online"

data_path = "./data/"

def get_msg_body(mime_msg):

    messageMainType = mime_msg.get_content_maintype()

    # When the message contains multiple parts
    # we segregate just the text part, for now,
    # and append it to the body
    if messageMainType == 'multipart':
            for part in mime_msg.get_payload():
                    if part.get_content_maintype() == 'text':
                            return part.get_payload()
            return ""
    # Else we just add the text to the body
    elif messageMainType == 'text':
            return mime_msg.get_payload()

def get_message(service, user_id, msg_id):

    if user_id is None: user_id ='me'

    # Getting the specific message in raw format using the message id
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()

    # Base 64 to ASCII
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))


    mime_msg = email.message_from_bytes(msg_str)

    body = get_msg_body(mime_msg)

    date = email.utils.parsedate(mime_msg['Date'])

    #  Return None if Hangouts message
    #  if(date==None):
        #  return None

    day = date[2]
    month = date[1]
    year = date[0]

    subject = mime_msg['Subject']
    sender = mime_msg['Sender']
    if sender is None: sender = mime_msg['From']

    # The dictionary structure for each message
    msg = {}

    msg['body'] = body
    msg['date'] = str(day)+"-"+str(month)+"-"+str(year)
    msg['from'] = sender
    msg['id'] = msg_id

    return msg


def save(msg,cnt):
    filename = msg['id'] + "_" +str(cnt)
    f = open(data_path+filename,'w')
    f.write("From:\n"+msg['from']+"\n\n")
    f.write("Date:\n"+msg['date']+"\n\n")
    f.write("Body:\n"+msg['body']+"\n\n")
    f.close()

def get_all_mail(gservice):
    
    page_token = None
    tc = 0 #Total number of messages
    
    while True:

        msgs = list_gmail_messages(gservice,pageToken=page_token)  # get list of msgs
        
        c = msgs["resultSizeEstimate"]

        # Processing the messages batch by batch as they arrive
        print ('--------Processing batch of approx %d messages---------'%(c))

        # Processing each message and saving 
        # necessary data points in a file named 
        # with unique ID of the message
        for msg in msgs["messages"]:
            tc+=1
            msg = get_message(gservice,None,msg['id'])
            if(msg!=None):
                save(msg,tc)
                print ("Message %d saved"%(tc))
        
        # Checking if there is an another batch of message in line            
        if 'nextPageToken' in msgs:
            page_token = msgs['nextPageToken']
        else: break

    print ('------Processed %d messages in total--------'%(tc))


@app.route("/")
def root():
    if 'cred' in session:
        
        print("-----Already Have Credentials-----")
        credentials = client.OAuth2Credentials.from_json(session['cred'])  # get creds
        if credentials.access_token_expired:
            auth_uri = flow.step1_get_authorize_url()  # init oauth
            return redirect(auth_uri)
        http_auth = credentials.authorize(httplib2.Http())
        gservice = make_gmail_service(http_auth)

        get_all_mail(gservice)

    else:
        
        print("----- Getting auth -----")
        auth_uri = flow.step1_get_authorize_url()  # init oauth
        return redirect(auth_uri)


@app.route("/oauth2callback")
def oauth_handler():

    if 'error' in request.args:
        del session['cred']
        return 'error'

    else:
        auth_code = request.args['code']
        credentials = flow.step2_exchange(auth_code)
        session['cred'] = credentials.to_json()  # store credentials in session
        return redirect('/')

    return "----- Got credentials -----"


@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.secret_key = 'sldakjhbp8263qweuq;eq612e817'
    app.run(debug=True, port=8000)
