import markovify, nltk, datetime, time, twitter, json, sqlite3
import logging 
logging.basicConfig(filename="log.log", level=logging.INFO,
					filemode="w")


#first we read the configurations from the config file and set them
with open("config.json") as json_data_file:
	data = json.load(json_data_file)


CONSUMER_KEY = data["MACHADO"]["consumer_key"]
CONSUMER_SECRET= data["MACHADO"]["consumer_secret"]
ACCESS_TOKEN_KEY= data["MACHADO"]["access_token_key"]
ACCESS_TOKEN_SECRET= data["MACHADO"]["access_token_secret"]
DB = data["MACHADO"]["database"]


def login():
	api = twitter.Api(consumer_key= CONSUMER_KEY,
				  consumer_secret= CONSUMER_SECRET,
				  access_token_key= ACCESS_TOKEN_KEY,
				  access_token_secret= ACCESS_TOKEN_SECRET)
	return api


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
		matches = self.cursor.execute("SELECT * FROM posts ORDER BY id").fetchall()[0]
		for row in matches:
			print(row)

	def adapt_datetime(self,ts):
		return int(time.mktime(ts.timetuple()))

	def add_to(self, comment, completion):
		logging.info("Adding post to database...")
		self.cursor.execute("INSERT INTO posts (body, date) "\
			"VALUES (?, ?)", (comment.body,\
			self.adapt_datetime(datetime.date.today())))
		self.connection.commit()
		logging.info("Post added!!!!!!!!")


################################################################
#Here we will handle json models and define how to save
#and load these markov chain models into the file
################################################################

def save_model_as_json(text_model, file_name):
	model_json = text_model.to_json()
	with open('models\\' + file_name + 'json', 'w') as outfile:
		json.dump(model_json, outfile)

def load_model_from_json(file_name):
	with open('models\\' + file_name + 'json') as json_file:
		return markovify.Text.from_json(json.load(json_file))

def get_machado():
	return load_model_from_json('default')

def get_sabino():
	return load_model_from_json('sabino')

def model_and_save(file_name):#also returns the model
	with open('samples\\' + file_name + '.txt', encoding = 'utf-8') as file:
		model = markovify.Text(file.read(), state_size = 3)
	save_model_as_json(model, file_name)
	return model