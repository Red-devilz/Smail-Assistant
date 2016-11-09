import sys
import numpy as np
from sklearn.cluster import KMeans
import pandas as pd
import nltk
import re
import os
import glob
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
import json



# load nltk's English stopwords as variable called 'stopwords'
stopwords = nltk.corpus.stopwords.words('english')

# load nltk's SnowballStemmer as variabled 'stemmer'
stemmer = SnowballStemmer("english")

def tokenize_and_stem(text):
    """ 
    Stem every word and return the unique stemmed tokens for text
    """
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
    filtered_tokens = []

    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        #  Only include words which start with a letter and have alpha numeric characters. Max words size = 12
        if re.match('^[a-zA-Z][a-zA-Z0-9]*$', token) and len(token)<12 and (token not in stopwords):
            token = token.lower()
            filtered_tokens.append(token)

    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems

all_text = []
all_mails = []

def vocab_find():
    """ 
    Find the vocabulary of the set
    """

    path = './data/'
    totalvocab_stemmed = set()

    for infile in glob.glob( os.path.join(path, '*') ):
        i = open(infile).read()
        msg_id  = os.path.splitext(os.path.basename(infile))[0].split('_')[1]
        all_mails.append(msg_id)
        all_text.append(i)
        allwords_stemmed = tokenize_and_stem(i) 
        totalvocab_stemmed.update(allwords_stemmed) #extend the 'totalvocab_stemmed' list

    print("The vocabulary size is " + str(len((totalvocab_stemmed))))

def cluster_featurize():
    """
    Convert the data into a matrix form
    Only words that occurs in between  max_df% and min_df% of documents are considered
    """

    #define vectorizer parameters
    tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000,
                                     min_df=0.05, stop_words='english',
                                     use_idf=True, tokenizer=tokenize_and_stem, ngram_range=(1,3))

    tfidf_matrix = tfidf_vectorizer.fit_transform(all_text) 
    print("The shape of the matrix is" + str(tfidf_matrix.shape))
    terms = tfidf_vectorizer.get_feature_names()
    print("size of smaller vocabulary is" + str(len(terms)))

    return (tfidf_matrix,terms)


num_clusters = 10
def kmeans_clustering(feat_vec, labels):
    """
    Cluster the data into x Clusters
    """
    km = KMeans(n_clusters=num_clusters)

    km.fit(feat_vec)
    clusters = km.labels_.tolist()

    return(km)

def print_cluster(mod_obj, labels):
    """
    Find words representative of the cluster after kmeans clustering
    """

    #sort cluster centers by proximity to centroid

    order_centroids = mod_obj.cluster_centers_.argsort()[:, ::-1] 

    data = {}
    msg_labels = mod_obj.labels_

    for i in range(msg_labels.shape[0]):

        key = str(msg_labels[i])

        if key in data:
            data[key].append(all_mails[i])
        else:
            data[key] = [all_mails[i]]

    for i in range(num_clusters):
        print("\nCluster %d words:" % i)
        for ind in order_centroids[i, :10]: #replace 6 with n words per cluster
            print(' %s' % labels[ind], end=',')

    with open('sample_data.json', 'w') as f:
        json.dump(data, f)


vocab_find()
mat_vec,words = cluster_featurize()
km_obj = kmeans_clustering(mat_vec,words)
print_cluster(km_obj, words)
