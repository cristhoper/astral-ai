from kerykeion import AstrologicalSubject
import json

import heapq
import re
import nltk
import csv
from unicodedata import normalize
import os


birth_info = {
    'name':"Nombre",
    'year': 1984,
    'month': 1,
    'day': 2,
    'hour': 6,
    'min': 30,
    'city': "Santiago, Chile",
    'country':'CL'
}

astral_data = AstrologicalSubject(
    birth_info.get('name'),
    birth_info.get('year'),
    birth_info.get('month'),
    birth_info.get('day'),
    birth_info.get('hour'),
    birth_info.get('min'),
    birth_info.get('city'),
    birth_info.get('country'),

    )
with open('planet_data.json') as datafile:
    planet_data = json.load(datafile)

astral_text = ''

for astral_detail in astral_data.planets_names_list:
    if planet_data['planets'].get(astral_detail.lower(), None) is not None:
        astral_planet = astral_data.get(astral_detail.lower())
        astral_text += planet_data['planets'][astral_detail.lower()][astral_planet.sign.lower()]

astral_text = re.sub(
    r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+",
    r"\1", normalize( "NFD", astral_text), 0, re.I)

astral_text = normalize( 'NFC', astral_text)
formatted_astral_text = re.sub('[^a-zA-Z]', ' ', astral_text )
formatted_astral_text = re.sub(r'\s+', ' ', formatted_astral_text)

sentence_list = nltk.sent_tokenize(astral_text)

#EN ESTA PARTE ENCUENTRA LA FRECUENCIA DE CADA PALABRA
stopwords = nltk.corpus.stopwords.words('spanish')

word_frequencies = {}
for word in nltk.word_tokenize(formatted_astral_text):
    if word not in stopwords:
        if word not in word_frequencies.keys():
            word_frequencies[word] = 1
        else:
            word_frequencies[word] += 1

maximum_frequncy = max(word_frequencies.values())

for word in word_frequencies.keys():
    word_frequencies[word] = (word_frequencies[word]/maximum_frequncy)

sentence_scores = {}
for sent in sentence_list:
    for word in nltk.word_tokenize(sent.lower()):
        if word in word_frequencies.keys():
            if len(sent.split(' ')) < 40:
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word]
                else:
                    sentence_scores[sent] += word_frequencies[word]

summary_sentences = heapq.nlargest(8, sentence_scores, key=sentence_scores.get)

summary = ' '.join(summary_sentences)

print(summary)
