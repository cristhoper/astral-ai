import kerykeion
import json

import heapq
import re
import nltk
import csv
from unicodedata import normalize
import os
import time

from flask import Flask, request
from wtforms import Form, StringField, TextAreaField, validators, StringField, SubmitField


# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

def get_astral_summary(year, month, day, hour, minute, city='Santiago', country='CL', name="ANY"):
    astral_data = kerykeion.AstrologicalSubject(name, year, month, day, hour, minute,city='Santiago', nation='CL')

    with open('planet_data.json') as datafile:
        planet_data = json.load(datafile)
    with open('houses_data.json') as datafile:
        house_data = json.load(datafile)

    astral_text = ""
    planet_degrees = []
    element = {
        'Fire': 0,
        'Earth': 0,
        'Air': 0,
        'Water': 0,
    }


    for astral_detail in astral_data.planets_names_list:
        if planet_data['planets'].get(astral_detail.lower(), None) is not None:
            astral_planet = astral_data.get(astral_detail.lower())
            astral_text += planet_data['planets'][astral_detail.lower()][astral_planet.sign.lower()]
            planet_degrees.append((astral_detail.lower(),astral_planet.abs_pos, astral_planet.emoji))
        if astral_detail.lower() in ['sun', 'moon']:
            element[astral_planet.element] += 2
        else:
            element[astral_planet.element] += 1

    for astral_detail in astral_data.houses_names_list:
        if house_data['houses'].get(astral_detail.lower(), None) is not None:
            astral_house = astral_data.get(astral_detail.lower())
            astral_text += house_data['houses'][astral_detail.lower()][astral_house.sign.lower()]
            if astral_detail.lower() == 'firsth_house':
                planet_degrees.append(('asc',astral_house.abs_pos, 'A'))
                element[astral_detail.element] += 1
    t = 0
    for k in element.keys():
        t += element[k]
    for k in element.keys():
        element[k] = 100*element[k]/t

    astral_text = re.sub(
        r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+",
        r"\1", normalize( "NFD", astral_text), 0, re.I)

    astral_text = normalize( 'NFC', astral_text)
    formatted_astral_text = re.sub('[^a-zA-Z]', ' ', astral_text )
    formatted_astral_text = re.sub(r'\s+', ' ', formatted_astral_text)

    return element, planet_degrees, astral_text, formatted_astral_text


def process_texts(astral_text, formatted_astral_text):
    sentence_list = nltk.sent_tokenize(astral_text)

    stopwords = nltk.corpus.stopwords.words('spanish')

    word_frequencies = {}
    for word in nltk.word_tokenize(formatted_astral_text):
        if word not in stopwords:
            if word not in word_frequencies.keys():
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1

    maximum_frequency = max(word_frequencies.values())

    for word in word_frequencies.keys():
        word_frequencies[word] = (word_frequencies[word]/maximum_frequency)

    sentence_scores = {}
    for sent in sentence_list:
        for word in nltk.word_tokenize(sent.lower()):
            if word in word_frequencies.keys():
                if len(sent.split(' ')) < 30:
                    if sent not in sentence_scores.keys():
                        sentence_scores[sent] = word_frequencies[word]
                    else:
                        sentence_scores[sent] += word_frequencies[word]

    summary_sentences = heapq.nlargest(5, sentence_scores, key=sentence_scores.get)
    return summary_sentences

def justify_text_2_lines(sentences_list, fixed_chars):
    formatted_text = ""
    for sentence in sentences_list:
        for i in range(0, len(sentence), fixed_chars):
            formatted_text += sentence[i:i+fixed_chars]+'\n'
    return formatted_text

import fpdf
import math
WIDTH = 152
HEIGHT = 78


def send_to_printer(sentence_list, planet_degrees, elements):
    pdf = fpdf.FPDF('landscape','mm',(HEIGHT,WIDTH))
    pdf.add_page()
    pdf.set_font("courier", size = 9)
    pdf.set_line_width(0.5)
    pdf.dashed_line(0,0,0,HEIGHT)
    pdf.dashed_line(WIDTH,0,WIDTH,HEIGHT)
    pdf.set_margin(15)

    pdf.add_font(fname="ttf/DejaVuSans.ttf")

    sentence = ' '.join(sentence_list)
    pdf.write(text=sentence)

    i = 0
    line_len = HEIGHT/4.5
    offset = 0
    x_offset = WIDTH/2
    y_offset = 3*HEIGHT/4
    pdf.set_font("DejaVuSans", size=4)
    for (planet, degree, emoji) in planet_degrees:
        line_len_i = line_len-i
        pdf.set_draw_color(r=20*i+20, g=20*i+20, b=20*i+20)
        x2 = x_offset+line_len_i*math.sin(degree-offset)
        y2 = y_offset+line_len_i*math.cos(degree-offset)
        #pdf.text(x=x2, y=y2, text="{}".format(emoji))
        pdf.line(x1=x_offset, y1=y_offset, x2=x2, y2=y2)
        i += 1

    pdf.text(x=9*WIDTH/12, y=7*HEIGHT/8, text="@unacasaclub")
    stamp = time.time()
    output_filename = "./out/astral.{}.pdf".format(stamp)
    pdf.output(output_filename)
    #os.system("lpr {}".format(output_filename))

@app.route("/", methods=['GET', 'POST'])
def post_astral_data():

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        current_read = json.loads(request.data)
        elements, planet_degrees, astral_text, formatted_astral_text = get_astral_summary(current_read['year'], current_read['month'], current_read['day'], current_read['hour'], current_read['minute'])
        resume_list = process_texts(astral_text, formatted_astral_text)
        summary = justify_text_2_lines(resume_list,1050)
        send_to_printer(resume_list, planet_degrees, elements)
        return summary
    else:
        return 'Content-Type not supported!'


if __name__ == "__main__":
    app.run(host="0.0.0.0")