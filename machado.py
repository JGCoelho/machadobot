import markovify, nltk, datetime, time, twitter, json
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


