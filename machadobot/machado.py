# -*- coding: utf-8 -*-
import markovify
import spacy
import datetime
import time
import tweepy
import json
import sqlite3
import re
import random
import logging
import sys
# from os import path

logging.basicConfig(filename="docs\\log.log", level=logging.INFO,
                    filemode="w")
logger = logging.getLogger()
logger.info(datetime.datetime.now())
nlp = spacy.load('pt')

# first we read the configurations from the config file and set them
with open("config.json", encoding="utf-8") as json_data_file:
    data = json.load(json_data_file)


CONSUMER_KEY = data["SETTINGS"]["consumer_key"]
CONSUMER_SECRET = data["SETTINGS"]["consumer_secret"]
ACCESS_TOKEN_KEY = data["SETTINGS"]["access_token_key"]
ACCESS_TOKEN_SECRET = data["SETTINGS"]["access_token_secret"]
DB = data["SETTINGS"]["database"]
MODELS = data["SETTINGS"]["models"]
MAX_FAVS = data["SETTINGS"]["favsinrun"]
HASHTAGS = data["SETTINGS"]["hashtags"]
AVOID = data["SETTINGS"]["avoidthose"]
FULL_NAME = \
    {"Machado": 'Machado de Assis',
     "Sabino": 'Fernando Sabino',
     "Guimaraes": 'Guimarães Rosa',
     "Mario": 'Mário de Andrade',
     "Clarice": 'Clarice Lispector',
     "Graciliano": 'Graciliano Ramos',
     "Lobato": 'Monteiro Lobato'}
NON_BMP_MAP = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
# we have a sqlite3 database db.db for the posts
# "CREATE TABLE posts (id INTEGER PRIMARY KEY, body TEXT, date INTEGER)"
# there we store all the posts the bot has sucessfully made


class Database:
    def __init__(self, database=DB):
        self.database = database
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()

    def new_conn(self, database=DB):
        self.connection.commit()
        self.connection.close()
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        return self.connection, self.cursor

    def show_content(self):
        print("This is the content of the database:")
        matches = self.cursor.execute("SELECT * FROM "
                                      "posts ORDER BY id").fetchall()
        for row in matches:
            print(row)

    def adapt_datetime(self, ts):
        return int(time.mktime(ts.timetuple()))

    def add_to(self, post):
        logger.info("Adicionando à base de dados...")
        self.cursor.execute(
            "INSERT INTO posts (body, date) "
            "VALUES (?, ?)", (post,
                              self.adapt_datetime(
                                  datetime.date.today())))
        self.connection.commit()
        logger.info("Post added!!!!!!!!")

    def retrieve_msg(self):
        pass  # nothing for now


db = Database()

################################################################
# Spacy markovify wrapper and methods to create, save and
# load markov chain models
################################################################
nlp = spacy.load('pt')


class MarkovPT(markovify.Text):
    def word_split(self, sentence):
        return ["::".join((word.orth_, word.pos_)) for word in nlp(sentence)]

    def word_join(self, words):
        sentence = " ".join(word.split("::")[0] for word in words)
        return sentence


def save_model_as_json(text_model, file_name):
    model_json = text_model.to_json()
    with open('docs\\models\\' + file_name + '.json', 'w') as outfile:
        json.dump(model_json, outfile)


def load_model_from_json(file_name):
    logger.info("Opening model: {}".format(file_name))
    with open('docs\\models\\' + file_name + '.json') as json_file:
        return MarkovPT.from_json(json.load(json_file))


def model_and_save(file_name, state_size=4):  # also returns the model
    with open('docs\\samples\\' + file_name + '.txt',
              encoding="utf-8") as file:
        model = MarkovPT(file.read(), state_size=state_size)
    save_model_as_json(model, file_name)
    return model


def remodel_all():
    for name in MODELS:
        model_and_save(name)


# some factories for common models
def get_machado():
    return load_model_from_json('Machado')


def get_sabino():
    return load_model_from_json('Sabino')


def get_guimaraes():
    return load_model_from_json('Rosa')


################################################################
# Methods for creating the messages
################################################################
new_line_patt = re.compile(r'\n')
space_patt = re.compile(r'\s+')
flawed_utf_patt = re.compile(r'\\x\.*')
quote_patt = re.compile("\"")
n_patt = re.compile(r'\sn\s')
d_patt = re.compile(r'\sd\s')
a_patt = re.compile(r'\sà\ss\s')
ao_patt = re.compile(r'\sa\so\s')
aos_patt = re.compile(r'\sa\sos\s')
dots_patt = re.compile(r'\s\.\.\.')


def choose_model():
    model_name = random.choice(MODELS)
    model = load_model_from_json(model_name)
    return model, model_name


def format_msg(msg, model_name):
    msg = re.sub(new_line_patt, " ", msg)
    msg = re.sub(space_patt, " ", msg)
    msg = re.sub(flawed_utf_patt, "", msg)
    msg = re.sub(quote_patt, "", msg)
    msg = re.sub(n_patt, " n", msg)
    msg = re.sub(d_patt, " d", msg)
    msg = re.sub(a_patt, " às ", msg)
    msg = re.sub(ao_patt, " ao ", msg)
    msg = re.sub(aos_patt, " aos ", msg)
    msg = re.sub(dots_patt, "...", msg)
    msg = re.sub(u'\\s([?\\.!,;"](?:\\s|$))', r'\1', msg)
    hashtags = random.sample(HASHTAGS, 2)
    msg = "\"{}\"\n— {}\n#{} #{}".format(
        msg, FULL_NAME[model_name], hashtags[0], hashtags[1])
    return msg


def make_message(model, model_name):
    logger.info("Generating sentence: {}".format(model_name))
    min_size = 170
    max_size = 240
    entire_sentence = ""

    while len(entire_sentence) < min_size:
        if len(entire_sentence) != 0:
            entire_sentence += " "
        sentence = None
        while sentence is None:
            sentence = model.make_short_sentence(
                max_size - len(entire_sentence))

        if sentence[-1] == ",":
            sentence = sentence[:-1] + "."
        elif sentence[-1] not in ["?", "!", ".", "\""]:
            sentence = sentence + "."
        entire_sentence += sentence
    # the machado model has some accented
    # characters that for some reason don't
    # get formated nicely. In this step
    # we remove them and do some more formatting
    entire_sentence = format_msg(entire_sentence, model_name)
    return entire_sentence


################################################################
# Methods for logging in, posting, favoriting and following
################################################################
class FavListener(tweepy.StreamListener):
    def __init__(self, api, favs=MAX_FAVS):
        self.api = api
        self.me = api.me()
        self.num_tweets = 0
        self.max_favs = favs

    def on_status(self, tweet):
        logger.info(f"Processing tweet id {tweet.id}")
        if (tweet.in_reply_to_status_id is not None or
                tweet.user.id == self.me.id):
            # This tweet is a reply or I'm its author so, ignore it
            return
        if not tweet.favorited:
            # Mark it as Liked, since we have not done it yet
            logger.info(f"Liking tweet with id {tweet.id}")
            for word in AVOID:
                # lower() so i only need to list words in lowercase
                if word in tweet.text.lower():
                    logger.info("The following tweet had a"
                                " banned word:\n{}".format(tweet.text.lower()))
                    return  # don't do anything if the tweet is polemic
            try:
                tweet.favorite()
                self.num_tweets += 1
            except Exception as e:
                logger.critical(e)
        if self.num_tweets >= self.max_favs:
            return False  # this should stop the stream


def login():
    logger.info("Logging in...")
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth, wait_on_rate_limit=True,
                     wait_on_rate_limit_notify=True)
    try:
        api.verify_credentials()
    except Exception as e:
        logger.critical(e)
    logger.info("Logging succesful!")
    return api


def make_post(api):
    logger.info("Inside make_post")

    model, model_name = choose_model()
    msg = make_message(model, model_name)
    logger.info("Message:\n{}".format(msg))
    api.update_status(msg)
    db.add_to(msg)


def follow_followers(api):
    logger.info("Retrieving and following followers")
    for follower in tweepy.Cursor(api.followers).items():
        if not follower.following:
            try:
                logger.info("Following {}".format(
                    follower.name.translate(
                        NON_BMP_MAP)))
            except Exception as e:
                logger.info(e)
            try:
                follower.follow()
            except tweepy.error.TweepError:
                pass


def main():
    logging.info(datetime.datetime.now())
    logger.info("Initiating main method")
    api = login()
    make_post(api)
    follow_followers(api)
    # creates a listener object to fav tweets
    tweets_listener = FavListener(api)
    stream = tweepy.Stream(api.auth, tweets_listener)
    stream.filter(track=HASHTAGS, languages=["pt"])
    stream.disconnect()
    logger.info("End of script")
    logger.info(datetime.datetime.now())


################################################################
# unit tests, uncomment to run
################################################################


def test_each_model():
    for model_name in MODELS:
        model = load_model_from_json(model_name)
        print(make_message(model, model_name))


def test_login():
    api = login()
    timeline = api.home_timeline()
    for tweet in timeline:
        print(f"{tweet.user.name} said {tweet.text}")
    user = api.get_user("MikezGarcia")
    print("User details:")
    print(user.name)
    print(user.description)
    print(user.location)

    print("Followers:")
    for follower in user.followers():
        print(follower.name)


def test_make_post():
    api = login()
    make_post(api)
    db.show_content()


# test_each_model()
# test_login()
# test_make_post()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(e)
