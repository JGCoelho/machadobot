# -*- coding: utf-8 -*-
import markovify, spacy, datetime
import time, tweepy, json, sqlite3
import re, random, logging
nlp = spacy.load('pt')
from os import path
logging.basicConfig(filename="docs\\log.log", level=logging.INFO,
					filemode="w")

#first we read the configurations from the config file and set them
with open("config.json") as json_data_file:
	data = json.load(json_data_file)


CONSUMER_KEY = data["SETTINGS"]["consumer_key"]
CONSUMER_SECRET= data["SETTINGS"]["consumer_secret"]
ACCESS_TOKEN_KEY= data["SETTINGS"]["access_token_key"]
ACCESS_TOKEN_SECRET= data["SETTINGS"]["access_token_secret"]
DB = data["SETTINGS"]["database"]
MODELS = data["SETTINGS"]["models"]
FULL_NAME = {
	"Machado" : 'Machado de Assis',
	"Sabino" : 'Fernando Sabino',
	"Guimaraes" : 'Guimarães Rosa',
	"Mario" : 'Mário de Andrade',
	"Clarice" : 'Clarice Linspector',
	"Graciliano" : 'Graciliano Ramos'
}

#we have a sqlite3 database db.db for the posts
#"CREATE TABLE posts (id INTEGER PRIMARY KEY, body TEXT, date INTEGER)"
#there we store all the posts the bot has sucessfully made
class Database:
	def __init__(self, database = DB):
		self.database = database
		self.connection = sqlite3.connect(database)
		self.cursor = self.connection.cursor()
		
	def new_conn(self, database = DB):
		self.connection.commit()
		self.connection.close()
		self.connection = sqlite3.connect(database)
		self.cursor = self.connection.cursor()
		return self.connection, self.cursor
	
	def show_content(self):
		print("This is the content of the database:")
		matches = self.cursor.execute("SELECT * FROM posts ORDER BY id").fetchall()
		for row in matches:
			print(row)

	def adapt_datetime(self,ts):
		return int(time.mktime(ts.timetuple()))

	def add_to(self, post):
		logging.info("Adicionando à base de dados...")
		self.cursor.execute("INSERT INTO posts (body, date) "\
			"VALUES (?, ?)", (post,\
			self.adapt_datetime(datetime.date.today())))
		self.connection.commit()
		logging.info("Post added!!!!!!!!")
	
	def retrieve_msg(self):
		pass#nothing for now

db = Database()

################################################################
#Spacy markovify wrapper and methods to create, save and 
#load markov chain models
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
	logging.info("Opening model: {}".format(file_name))
	with open('docs\\models\\' + file_name + '.json') as json_file:
		return MarkovPT.from_json(json.load(json_file))

def model_and_save(file_name, state_size = 4):#also returns the model
	with open('docs\\samples\\' + file_name + '.txt', encoding = "utf-8") as file:
		model = MarkovPT(file.read(), state_size = state_size)
	save_model_as_json(model, file_name)
	return model

def remodel_all():
	for name in MODELS:
		model_and_save(name)

#some factories for common models
def get_machado():
	return load_model_from_json('Machado')

def get_sabino():
	return load_model_from_json('Sabino')

def get_guimaraes():
	return load_model_from_json('Rosa')

################################################################
#Methods for logging, using the api and making posts.
################################################################
flawed_utf_patt = re.compile(r'\\x\.*')
quote_patt = re.compile("\"")
space_patt = re.compile(r'\s+')
n_bug_patt = re.compile(r'\sn\s')
d_bug_patt = re.compile(r'\sd\s')
a_bug_patt = re.compile(r'\sà\ss\s')
ao_bug_patt = re.compile(r'\sa\so\s')

def choose_model():
	model_name = random.choice(MODELS)
	model = load_model_from_json(model_name)
	return model, model_name

def format_msg(msg, model_name):
	msg = re.sub(space_patt, " ", msg)
	msg = re.sub(flawed_utf_patt, "", msg)
	msg = re.sub(quote_patt,"", msg)
	msg = re.sub(n_bug_patt," n", msg)
	msg = re.sub(d_bug_patt," d", msg)
	msg = re.sub(a_bug_patt," às ", msg)
	msg = re.sub(ao_bug_patt," ao ", msg)
	msg = re.sub(u'\\s([?\\.!,;"](?:\\s|$))', r'\1', msg)
	msg = "\"{}\"\n\t— {}\n#livros #literatura".format(msg, FULL_NAME[model_name])
	return msg

def make_message(model, model_name):
	logging.info("Generating sentence: {}".format(model_name))
	min_size = 200
	max_size = 240
	entire_sentence = ""
	
	while len(entire_sentence) < min_size:
		if len(entire_sentence) != 0:
			entire_sentence += " "
		sentence = None
		while sentence == None:
			sentence = model.make_short_sentence(max_size - len(entire_sentence))

		if sentence[-1] == ",":
			sentence = sentence[:-1] + "."
		elif sentence[-1] not in ["?","!",".","\""]:
			sentence = sentence + "."
		entire_sentence += sentence
	#the machado model has some accented
	#characters that for some reason don't
	#get formated nicely. In this step
	# we remove them and do some more formatting
	entire_sentence = format_msg(entire_sentence, model_name)
	return entire_sentence

def login():
	logging.info("Logging in...")
	auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
	auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
	api = tweepy.API(auth, wait_on_rate_limit=True,
    	wait_on_rate_limit_notify=True)
	try:
		api.verify_credentials()
	except Exception as e:
		logging.critical(e)
	logging.info("Logging succesful!")
	return api

def make_post():
	logging.info("Inside make_post")
	api = login()
	model, model_name = choose_model()
	msg = make_message(model, model_name)
	logging.info("Message:\n{}".format(msg))
	api.update_status(msg)
	db.add_to(msg)

################################################################
#unit tests, uncomment to run
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

	print("Last 20 Followers:")
	for follower in user.followers():
		print(follower.name)

def test_make_post():
	make_post()
	db.show_content()

#test_each_model()
#test_login()
#test_make_post()


make_post()
time.sleep(5)