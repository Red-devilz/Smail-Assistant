import json
from oauth2client import client
import httplib2
from flask import Flask, redirect, request, session
import base64
import email
from .api import *


def get_message(service, user_id, msg_id):
    """
    Get the message and return in MiMe format along with thread ID
    """

    if user_id is None:
        user_id = 'me'

    # Getting the specific message in raw format using the message id
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()

    # Base 64 to ASCII
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

    mime_msg = email.message_from_bytes(msg_str)
    thread_id = message['threadId']

    return (mime_msg, thread_id)


def get_mails(gservice, num_mails=-1):
    """
    Process ALL-mail of a specific user(not inbox)
    args   : gservice  - object
             num       - number of mails to fetch(-ve number if fetch all mails)
    return :  list of four elements (id_list, body_list, label_list, threadId_list)
    """

    label_list = []
    body_list = []
    id_list = []
    thread_list = []

    page_token = None
    tc = 0  # Total number of messages

    while True:

        msgs = list_gmail_messages(gservice, pageToken=page_token)  # get list of msgs

        c = msgs["resultSizeEstimate"]

        # Processing the messages batch by batch as they arrive
        for msg in msgs["messages"]:

            #  Return if required number of mails are fetched
            if(tc == num_mails):
                return (id_list, body_list, label_list, thread_list)

            #  Get message
            id_list.append(msg['id'])
            msg, thread_id = get_message(gservice, None, msg['id'])

            #  Append info objects
            label_list.append('Sample_label')
            body_list.append(msg)
            thread_list.append(thread_id)

            #  counter of messages
            tc += 1

        # Checking if there is an another batch of message in line
        if 'nextPageToken' in msgs:
            page_token = msgs['nextPageToken']
        else:
            break

    return (id_list, body_list, label_list, thread_list)
