import re
from bs4 import BeautifulSoup
import sys
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

#  Path where data is to be stored
data_path = "./data/"

def visible(element):
    """
    Helper function for HTML, Checks if elements is a text element in HTML
        Input  : 'element' is a string
        Return : boolean answer indicating if html text element
    """
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True

def get_msg_body(mime_msg):
    """
    Gets the body of the message in mime format
    input  : mime string
    return : string of the body
    """

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

def convert_txt_html(txt):
    """
    Extracts Text from HTML 
    """

    soup = BeautifulSoup(txt, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = list(filter(visible, texts))

    final_txt = " ".join(visible_texts)
    final_txt = str(final_txt.encode('ascii','ignore'))

    final_txt = re.sub(r'\\n', "", final_txt)
    final_txt = re.sub(r'\\r', "", final_txt)

    return final_txt

def parse_body(text):
    """
    Parse the body to get only a set of useful strings, removing unnecessary strings
    input : 'body' of text as string
    output : modified 'body' of text
    """

    #  if html then extract the text from it
    ans = re.search('<[hH][tT][mM][lL]>' , text)
    if ans:
       text = convert_txt_html(text)

    #  Remove =20, space characters
    text = re.sub(r'=([0-9]*)', "", text)

    #  remove URL's
    text = re.sub(r'<http://[a-zA-Z0-9_\-/:.?]*>', "", text)
    text = re.sub(r'http://[a-zA-Z0-9_\-/:.?]*', "", text)
    text = re.sub(r'<https://[a-zA-Z0-9_\-/:.?]*>', "", text)
    text = re.sub(r'https://[a-zA-Z0-9_\-/:.?]*', "", text)

    #  Remove any <> html tags
    text = re.sub(r'<^[><]*>', "", text)

    #  Replace all carriage returns
    text = re.sub(r'\r',"", text)

    #  Remove > angle brackets from Threads
    text = re.sub(r'>', "", text)

    #  Remove bold text 
    text = re.sub(r'\*', "", text)

    #  Remove -- header lines
    text = re.sub(r'-+', "", text)

    # Remove text for facebook , google ,etc...
    text = re.sub(r'| *Twitter', "", text)
    text = re.sub(r'| *Google\+', "", text)
    text = re.sub(r'| *Facebook', "", text)
    text = re.sub(r'| *Youtube', "", text)


    return text

def get_message(service, user_id, msg_id):
    """
    Get the message with corresponding message ID
    """

    if user_id is None: user_id ='me'

    # Getting the specific message in raw format using the message id
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()

    # Base 64 to ASCII
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

    mime_msg = email.message_from_bytes(msg_str)

    body = get_msg_body(mime_msg)

    body = parse_body(body)

    date = email.utils.parsedate(mime_msg['Date'])

    #  Return None if Hangouts message
    #  if(date==None):
        #  return None

    day = date[2]
    month = date[1]
    year = date[0]

    threadid = message['threadId']
    subject = mime_msg['Subject']
    To = mime_msg['To']
    sender = mime_msg['Sender']
    if sender is None: sender = mime_msg['From']

    # The dictionary structure for each message
    msg = {}

    msg['body'] = body
    msg['date'] = str(day)+"-"+str(month)+"-"+str(year)
    msg['from'] = sender
    msg['id'] = msg_id
    msg['to'] = To
    msg['subject'] = subject
    msg['threadid'] = threadid

    return msg

def save(msg,cnt):
    """
    Save the msg into a file

    """
    filename = str(cnt) + "_" +msg['id']
    f = open(data_path+filename,'w')
    if(msg['from']!=None):
        f.write("From:\n"+msg['from']+"\n\n")
    if(msg['to']!=None):
        f.write("To:\n"+msg['to']+"\n\n")
    if(msg['date']!=None):
        f.write("Date:\n"+msg['date']+"\n\n")
    if(msg['threadid']!=None):
        f.write("Thread ID:\n"+msg['threadid']+"\n\n")
    if(msg['subject']!=None):
        f.write("Subject:\n"+msg['subject']+"\n\n")
    if(msg['body']!=None):
        f.write("Body:\n"+msg['body']+"\n\n")
    f.close()

    print("-----------------------------------")
    print(msg['subject'])
    print(msg['to'])
    print(msg['date'])
    print(msg['from'])
    print("-----------------------------------")
    print(msg['body'])

def get_all_mail(gservice):
    """
    Process ALL-mail of a specific user(not inbox)
    """

    page_token = None
    tc = 1600 #Total number of messages

    batch = 0
    
    while True:
        batch = batch + 1

        msgs = list_gmail_messages(gservice,pageToken=page_token)  # get list of msgs
        
        c = msgs["resultSizeEstimate"]

        # Processing the messages batch by batch as they arrive
        print ('--------Processing batch of approx %d messages---------'%(c))

        # Processing each message and saving 
        # necessary data points in a file named 
        # with unique ID of the message
        if(batch>=16):
            for msg in msgs["messages"]:
                tc+=1
                msg = get_message(gservice,None,msg['id'])
                if(msg!=None):
                    save(msg,tc)
                    print ("Message %d saved"%(tc))
            
            #  Get Only 4 messages for simplicity(This is for testing on 10 messages)
            #  if(tc==4):
                #  sys.exit(0);
        
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
