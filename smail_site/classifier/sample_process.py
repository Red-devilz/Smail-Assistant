import re
from bs4 import BeautifulSoup
import sys
import json

import base64
import email

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

def print_content(msg, num):
    """
    Prints the current message object
    """
    print("===========================")
    print("Printing Message Number " + str(num))
    print("===========================\n")

    print("Message ID is    : " + msg['id'])
    print("Message Label is : " + msg['label'] + "\n")

    print("date      : " + msg['date'])
    print("from      : " + msg['from'])
    print("to        : " + msg['to'])
    print("subject   : " + msg['subject'])
    print("threadid  : " + msg['threadid'])

    print("\nbody:")
    print(msg['body'])

def sample_print(id_l, body_l, label_l, thread_l):
    """
    Sample function illustrating how to handle Mime Object
    """

    iter_len = len(id_l)

    for i in range(iter_len):
        #  Get the objects
        mime_msg = body_l[i]
        id_cur = id_l[i]
        label_cur = label_l[i]
        thread_cur = thread_l[i]

        #  Extract Detail of Mail object
        body = get_msg_body(mime_msg)

        date = email.utils.parsedate(mime_msg['Date'])

        day = date[2]
        month = date[1]
        year = date[0]

        threadid = thread_cur
        subject = mime_msg['Subject']
        To = mime_msg['To']
        sender = mime_msg['Sender']
        if sender is None: sender = mime_msg['From']

        # The dictionary structure for each message
        msg = {}

        msg['id'] = id_cur
        msg['label'] = label_cur

        msg['body'] = body
        msg['date'] = str(day)+"-"+str(month)+"-"+str(year)
        msg['from'] = sender
        msg['to'] = To
        msg['subject'] = subject
        msg['threadid'] = threadid
        
        #  Prints the message in terminal
        print_content(msg, i)


