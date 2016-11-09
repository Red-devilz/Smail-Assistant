import re
from bs4 import BeautifulSoup
import sys
import json

from oauth2client import client
import httplib2

from .api import *

import base64
import email

import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
import nltk
import os
import glob
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer


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
# load nltk's English stopwords as variable called 'stopwords'
stopwords = nltk.corpus.stopwords.words('english')

# load nltk's SnowballStemmer as variabled 'stemmer'
stemmer = SnowballStemmer("english")
all_messages = []


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
    final_txt = str(final_txt.encode('ascii', 'ignore'))

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
    ans = re.search('<[hH][tT][mM][lL]>', text)
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
    text = re.sub(r'\r', "", text)

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

    if user_id is None:
        user_id = 'me'

    # Getting the specific message in raw format using the message id
    message = service.users().messages().get(userId=user_id, id=msg_id, format='raw').execute()
    all_messages.append(message)
    # Base 64 to ASCII
    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))

    mime_msg = email.message_from_bytes(msg_str)

    body = get_msg_body(mime_msg)

    body = parse_body(body)

    date = email.utils.parsedate(mime_msg['Date'])

    #  Return None if Hangouts message
    if(date == None):
        return None

    day = date[2]
    month = date[1]
    year = date[0]

    threadid = message['threadId']
    subject = mime_msg['Subject']
    To = mime_msg['To']
    sender = mime_msg['Sender']
    if sender is None:
        sender = mime_msg['From']

    # The dictionary structure for each message
    msg = {}

    msg['body'] = body
    msg['date'] = str(day) + "-" + str(month) + "-" + str(year)
    msg['from'] = sender
    msg['id'] = msg_id
    msg['to'] = To
    msg['subject'] = subject
    msg['threadid'] = threadid

    return msg


def save(msg, cnt):
    """
    Save the msg into a file

    """
    filename = str(cnt) + "_" + msg['id']
    f = open(data_path + filename, 'w')
    f.write("From:\n" + msg['from'] + "\n\n")
    f.write("To:\n" + msg['to'] + "\n\n")
    f.write("Date:\n" + msg['date'] + "\n\n")
    f.write("Thread ID:\n" + msg['threadid'] + "\n\n")
    f.write("Subject:\n" + msg['subject'] + "\n\n")
    f.write("Body:\n" + msg['body'] + "\n\n")
    f.close()

    print("-----------------------------------")
    print(msg['subject'])
    print(msg['to'])
    print(msg['date'])
    print(msg['from'])
    print("-----------------------------------")
    print(msg['body'])


def tokenize_and_stem(text):
    """
    Stem every word and return the unique stemmed tokens for text
    """
    # first tokenize by sentence, then by word to ensure that punctuation is
    # caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []

    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        # Only include words which start with a letter and have alpha numeric
        # characters. Max words size = 12
        if re.match('^[a-zA-Z][a-zA-Z0-9]*$', token) and len(token) < 12 and (token not in stopwords):
            token = token.lower()
            filtered_tokens.append(token)

    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems


def get_all_mail(gservice, max_mails):
    """
    Process ALL-mail of a specific user(not inbox)
    """

    page_token = None
    tc = 0  # Total number of messages
    flag = 0
    all_text = []
    all_mails = []
    totalvocab_stemmed = set()
    while True:

        msgs = list_gmail_messages(gservice, pageToken=page_token)  # get list of msgs

        c = msgs["resultSizeEstimate"]

        # Processing the messages batch by batch as they arrive
        print ('--------Processing batch of approx %d messages---------' % (c))

        # Processing each message and saving
        # necessary data points in a file named
        # with unique ID of the message
        for msg in msgs["messages"]:
            tc += 1
            msg = get_message(gservice, None, msg['id'])
            if(msg != None):
                all_mails.append(msg['id'])
                message_str = ""
                if(msg['id']):
                    message_str += msg['id'] + "\n"
                if(msg['from']):
                    message_str += "From:\n" + msg['from'] + "\n\n"
                if(msg['to']):
                    message_str += "To:\n" + msg['to'] + "\n\n"
                if(msg['date']):
                    message_str += "Date:\n" + msg['date'] + "\n\n"
                if(msg['subject']):
                    message_str += "Subject:\n" + msg['subject'] + "\n\n"
                if(msg['body']):
                    message_str += "Body:\n" + msg['body'] + "\n\n"
                all_text.append(message_str)
                allwords_stemmed = tokenize_and_stem(message_str)
                totalvocab_stemmed.update(allwords_stemmed)

            #  Get Only 4 messages for simplicity(This is for testing on 10 messages)
            if(tc == max_mails):
                flag = 1
                break
        if(flag == 1):
            break
        # Checking if there is an another batch of message in line
        if 'nextPageToken' in msgs:
            page_token = msgs['nextPageToken']
        else:
            break

    # Implement featurisation here
    tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,
                                       min_df=0.05, stop_words='english',
                                       use_idf=True, tokenizer=tokenize_and_stem, ngram_range=(1, 3))
    tfidf_matrix = tfidf_vectorizer.fit_transform(all_text)
    # print("The shape of the matrix is" + str(tfidf_matrix.shape))
    terms = tfidf_vectorizer.get_feature_names()
    # print("size of smaller vocabulary is" + str(len(terms)))

    # kmeans
    km = KMeans(n_clusters=10)
    km.fit(tfidf_matrix)

    # Constructing dictionary
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]

    data = {}
    msg_labels = km.labels_
    mesg_dict = {}
    for i in range(msg_labels.shape[0]):

        key = str(msg_labels[i])

        if key in data:
            data[key].append(all_mails[i])
        else:
            data[key] = [all_mails[i]]

    for j in range(len(all_mails)):
        mesg_dict[all_mails[j]] = all_messages[j]
    # print(mesg_dict)

    print ('------Processed %d messages in total--------' % (tc))
    return (data, mesg_dict)
