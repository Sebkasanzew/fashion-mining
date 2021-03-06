#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import nltk
import json
import os
import sys
import gensim
import re
import texttable as tt
from gensim import corpora, models, similarities
from pprint import pprint
from os.path import join
import numpy as np
from multiprocessing import Pool, freeze_support
import itertools

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

# Global Paths TODO: improvement of dirs
PROJECT_DIR = os.path.dirname(__file__) + "/../../"
GLOVE_DIR = PROJECT_DIR + "data/tmp/"
threshold = 0.7


def word2vec(model):
    """
    executes the main logic of word2vec
    :param model: string
    :return: result-json with tagged words, indices and cosine distance
    """
    # Loading external files
    logging.info("Loading documents and dictionary...")
    # with open(PROJECT_DIR + "data/input_data/crawler_with_ids.json", "r") as documents_file:
    # with open(PROJECT_DIR + "data/input_data/crawler_with_ids_english_only.json", "r") as documents_file:
    with open(PROJECT_DIR + "data/input_data/example_docs/example_docs.json", "r") as documents_file:
        docs = json.load(documents_file)

    # To skip nltk tokenizing load this document and comment tokens = nltk_tokenizing at line 44 out
    # with open(PROJECT_DIR + "data/input_data/example_docs/example_docs_tokenized.json", "r") as documents_file:
    #    tokens = json.load(documents_file)

    with open(PROJECT_DIR + "data/dictionaries/entities.txt", "r") as dictionary_file:
        dictionary = json.load(dictionary_file)

    old_dictionary = list(dictionary)

    logging.info("NLTK Tokenizing...")
    # tokens = nltk_tokenizing(docs)

    ###########################################Multiprocessing###################################################
    '''
    Multiprocessing uses new processes instead of threads
    Set pool parameter for number of parallel processes
    '''
    p = Pool(4)
    tokens = p.map(nltk_tokenizing_parrallel, docs)
    # print(tokens)
    with open(PROJECT_DIR + "data/input_data/example_docs/example_docs_tokenized.json", "w") as example_docs_tags:
        json.dump(tokens, example_docs_tags, sort_keys=True, indent=4, ensure_ascii=False)
    ############################################END###############################################################


    # load model for word2vec
    logging.info("Loading " + model + " model...")
    model = load_model(model)

    logging.info("Determining similarity...")

    ###########################################Multiprocessing###################################################
    '''
    Multiprocessing uses new processes instead of threads
    Set pool parameter for number of parallel processes
    '''
    freeze_support()
    #use similarity_star class as wrapper
    result = p.map(similarity_star, itertools.izip(tokens, itertools.repeat(model), itertools.repeat(dictionary)))
    logging.info("Writing auto tagged json...")
    with open(PROJECT_DIR + "data/output_data/vector_words_tags.json", "w") as docs_tags:
        json.dump(result, docs_tags, sort_keys=True, indent=4, ensure_ascii=False)

    ############################################END###############################################################

    #logging.info(str(counter) + " new words added to dictionary!")
    logging.info("Writing new dictionary...")
    new_dictionary = add_to_dict(result, old_dictionary)

    with open(PROJECT_DIR + "data/dictionaries/entities_new.txt", "w") as new_dict_file:
        json.dump(new_dictionary, new_dict_file, sort_keys=True, indent=4, ensure_ascii=True)

    logging.info("Word2Vec finished!")
    return result

def nltk_tokenizing_parrallel(document):
    extracted_text = document["extracted_text"]
    sentences = nltk.sent_tokenize(extracted_text)

    entities = []
    indices = []
    token_words = []

    for s in sentences:

        for word in (nltk.ne_chunk(nltk.tag.pos_tag(nltk.word_tokenize(s)))):
            # TODO Raul: check your intention... type(word) is checked twice (in check_tag())
            if type(word) is tuple:
                if check_tag(word):
                    token_words.append(word[0])
            else:
                if check_tag(word):
                    word_list = []
                    for w in word:
                        word_list.append(w[0])
                    token_words.append(" ".join(word_list))
                    # print(token_words)

    dictionary = corpora.Dictionary([token_words])

    for word in dictionary:
        i_tmp = []
        contains = False

        # Match pipe or non-alphaNumeric chars
        if re.match(".*[\|].*|[^a-zA-Z\d\s:]", dictionary[word]) is None:
            # print("String matches: " + dictionary[word])

            for m in re.finditer(dictionary[word], extracted_text):
                try:
                    if not extracted_text[m.start() - 1].isalpha() and not extracted_text[m.end()].isalpha():
                        contains = True
                        i_tmp.append([m.start(), m.end()])
                except:
                    # print(document)
                    print("The word: " + dictionary[word] + " contains pipes and will not be processed")

            if contains:
                entities.append(dictionary[word].encode('utf-8'))
                indices.append(i_tmp)

    tmp = {"_id": document["_id"]["$oid"], "entities": entities, "indices": indices}

    return tmp

def similarity_parallel(document, model, dictionary):
    sim = 0

    logging.info(model)
    cos_dist = []
    word = ""
    word_dict = ""
    extracted_tokens = document["entities"]

    for token in extracted_tokens:
        for d in dictionary:
            try:
                if " " in token:
                    if " " in d:
                        cos = model.n_similarity(token.split(" "), d.split(" "))
                    else:
                        cos = 0
                else:
                    cos = max(model.similarity(token, d), model.similarity(token.lower(), d.lower()))

                if cos >= sim:
                    sim = cos
                    word = token
                    word_dict = d

            except:
                pass

        # appending JOIN-Partner
        try:

            if sim == 0:
                cos_dist.append(["None", "None"])
            else:
                cos_dist.append([str(word_dict), str(sim)])

                sim = 0

        except:
            cos_dist.append(["None", "None"])

    document["cos_dist"] = cos_dist
    return document

def similarity_star(a_b):
    return similarity_parallel(*a_b)

def add_to_dict(result, dict_old):

    dict_old = [x.encode("utf-8") for x in dict_old]

    for doc in result:
        i = 0
        entities = doc["entities"]
        cos_dist = doc["cos_dist"]
        for entity in entities:
            # add word to dictionary if exceeds threshold
            #logging.info("Try:  " + entity)
            #entity = entity.encode('utf-8')
            try:

                if not (str(entity) in dict_old) and float(cos_dist[i][1]) >= threshold:

                    dict_old.append(str(entity))
                else:
                    #    # print("Word" + str(word) + " already exists in dictionary")
                    pass

            except:
                pass

            i += 1

    return dict_old


def check_tag(word):
    if type(word) is tuple:
        return word[1] == "NN" or word[1] == "NNP" or word[1] == "NNPS" or word[1] == "NNS"
    else:
        for w in word:
            if w[1] == "NN" or w[1] == "NNP" or w[1] == "NNPS" or w[1] == "NNS":
                return True
        return False


def load_model(mod):
    """
    loads a model which depends on the given parameter
    :param mod: an string according to the model
        glove: Glove Model
        selftrained: Own Fashion Model created from Zalando Documents
    :type mod: string
    :return: path of model
    """
    if mod == "glove":
        '''
        Convert Glove Model to Gensim Word2Vec
        GloVe is another algorithm that creates vector representations of words similar to word2vec.
        GloVe transforms the neutral network problem into a word co-occurrence matrix so it should
        be faster to train but uses more memory.
        '''

        def any2unicode(text, encoding='utf8', errors='strict'):
            if isinstance(text, unicode):
                return text
            return unicode(text.replace('\xc2\x85', '<newline>'), encoding, errors=errors)

        gensim.models.utils.to_unicode = any2unicode

        return gensim.models.Word2Vec.load_word2vec_format(join(GLOVE_DIR, 'common.840B.300d.txt'), binary=False)

    if mod == "selftrained":
        return gensim.models.Word2Vec.load(PROJECT_DIR + 'data/models/fashion_model')

        # if x == 2:
        #    return gensim.models.Word2Vec.load_word2vec_format('/opt/word2vec/freebase_model_en.bin.gz', binary=True)


# TODO collecting table data
def collect_table_data(data):
    result = []
    row_array = []

    for line in data:
        # row_array.append(line[0][0])
        # row_array.append(line[0][1])
        # row_array.append(str(line[1][0][0]).encode('utf8'))
        # row_array.append(str(line[1][0][1]))
        # row_array.append(str(line[1][1][0]).encode('utf8'))
        # row_array.append(str(line[1][1][1]))
        # row_array.append(str(line[1][2][0]).encode('utf8'))
        # row_array.append(str(line[1][2][1]))
        # row_array.append(line[2])
        # result.append(row_array)
        row_array = []

    return result


# draws a table
def draw_table(tab_array):
    tab = tt.Texttable()
    tab.header(['Words', 'POS-Tag', 'Word1', 'Cos-Dist', 'Word2', 'Cos-Dist', 'Word3', 'Cos-Dist', 'JOIN-Partner'])

    for row in tab_array:
        tab.add_row(row)

    # tab.add_row(['Zalando', 'NN', 'H&M',	'0,6434', 'word2',	'0,6234', 'word3', '0,5324', 'shoe'])
    # tab.add_row(['is', 'VB', 'word2',	'0,6434', 'word2',	'0,6234', 'word3', '0,5324', 'blub'])
    # tab.add_row(['big', 'AD', 'word2',	'0,6434', 'word2',	'0,6234', 'word3', '0,5324', 'fubar'])

    tab.set_cols_width([15, 5, 15, 5, 15, 5, 15, 5, 15])
    tab.set_cols_align(['l', 'l', 'l', 'l', 'l', 'l', 'l', 'l', 'l'])
    tab.set_chars(['-', '|', '+', '='])

    print tab.draw()


def custom_public_function_reachable_from_outside():
    """define functions that can be accessed from main.py and other modules"""


if __name__ == "__main__":
    # Execute the main function if this file was executed from the terminal
    word2vec(model="selftrained")



