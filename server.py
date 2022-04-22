from chatlib import *
import random
import select
# GLOBALS
users = {} # dictionary of users with their data
questions = {} # dictionary of questions
logged_users = {} # a dictionary of client hostnames to usernames

ERROR_MSG = "Error! "
USERS_PATH = 'users.txt'
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"

messages_to_send = [] # a list of all massages that the server needs to send to the client [tuple of socket and message]

# HELPER SOCKET METHODS
def build_and_send_message(conn:socket.socket, code:str, msg = '') -> None:
	"""
 	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then adds it to the list of messages to send.

	Args:
		conn (socket.socket): client's socket object.
		code (str): the message's code.
		msg (str, optional): the message's data. Defaults to ''.
	
	Returns: None
	"""
 
	global messages_to_send
	message = build_message(code, msg)
	logging.debug('Sending: {}'.format(message))
	messages_to_send.append((conn, message.encode()))


def recv_message_and_parse(conn: socket.socket) -> tuple:
	"""
 	Receives a new message from given socket.
	Prints debug info, then parses the message.

	Args:
		conn (socket.socket): client's socket object.

	Returns: 
		cmd (str) and date (str) of the received message.
		If error occured, will return None, None

	"""

	data = conn.recv(MAX_MSG_LENGTH).decode()
	cmd, msg = parse_message(data)
	if cmd == None:
		return "", ""		
	logging.debug('Received: {0}\n -- Parsed: > cmd - {1}  > msg - {2}'.format(data, cmd, msg))
	return cmd, msg
	
 
def send_waiting_messages(wlist:list)-> None:
	"""
	Receives a list of sockets that masseges can be sent to.

	Args:
		wlist (list): a list of sockets that masseges can be sent to.
	
	Returns: None
	"""	
	global messages_to_send
	print(wlist)
	for message in messages_to_send: 
		current_socket, data = message 
		if current_socket in wlist:     
			current_socket.send(data)  
		messages_to_send.remove(message)

# Data Loaders #

def load_questions(filename:str)-> dict:
	"""
	Receives the filename of the questions file and loads the questions bank from file.

	Args:
		filename (str): the filename of the questions file
	
	Returns: the questions from the file (dict)
 	"""

	with open(filename, 'r') as f: 
		count = 1
		for line in f:
			temp = line.split('|')
			questions[count] = {'question': temp[0], 'answers':temp[1:-1], 'correct':int(temp[-1])}
			count += 1

	return questions


def load_user_database(filename)->dict:
	"""
	Receives the filename of the users file and loads users list from file.

	Args:
		filename (str): the filename of the users file
	
	Returns: user dictionary
	"""

	users = {}
	with open(filename, 'r') as f: 
		for line in f:
			print(f)
			temp = line.split('|')
			temp[-1] = temp[-1].replace('\n', '')
			if temp[-1] == '':
				asked = []
			else:
				asked = [int(n) for n in temp[-1].split(',')]
			users[temp[0]] = {'password': temp[1], 'score':int(temp[2]), 'questions_asked':asked}

	return users

# DATA SAVING
def add_user(filename:str, username:str, password:str) -> None:
	"""
 	Receives the file name of the user database, new username and password, and add the user to the user's database.

	Args:
		filename (str): the filename of the users database.
		username (str): new user's name.
		password (str): new user's password.
	
	Returns: None
	"""
	global users
	users[username] = {'password': password, 'score': 0, 'questions_asked': []}
	with open(filename, 'a') as f:
		f.write('{}|{}|0|\n'.format(username, password))


def save_users(filename:str)-> None:
	"""
 	Receives the filename of the users database and updates the file.

	Args:
		filename (str): the filename of the users database.

	Returns: None
	"""
	global users
	with open(filename, 'w') as f:
		for user in users:
			print(user)
			f.write('{}|{}|{}|{}\n'.format(user, users[user]['password'], users[user]['score'], str(users[user]['questions_asked']).replace('[', '').replace(']', '')))
##

def create_random_question(username:str) -> list:
	"""
 	Receives a username and return a random question that the user didn't answer to.

	Args:
		username (str): user's username

	Returns:
		list: a list that contains the question data.
	"""
	global questions, users
	questions_asked = users[username]['questions_asked']
	questions_left = questions.copy()
	for q in questions_left.copy():
		if q in questions_asked:
			del questions_left[q]
	if questions_left == {}:
		return None
       
	question = random.choice(list(questions_left))
	users[username]['questions_asked'].append(question)
	return join_args((question, questions[question]['question'], *questions[question]['answers']))
	
# SOCKET CREATOR

def setup_socket() -> socket.socket:
	"""
	Creates new listening socket and returns it
	Args: -
	Returns: the socket object
	"""
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.bind((SERVER_IP, SERVER_PORT))
	print('Server is up on port {}!'.format(SERVER_PORT))
	sock.listen(1)
	return sock


def send_error(conn : socket.socket, error_msg: str) -> None:
	"""
	Received a client socket and error message and send an error message/

	Args:
		conn (socket.socket object): client's socket
		error_msg (str): error message
  
	Returns: None
	"""
	build_and_send_message(conn, PROTOCOL_SERVER['error_msg'], ERROR_MSG + error_msg)

	
def print_client_sockets()-> None:
	"""
	Prints all keys in logged users
	
	Args: -
	Returns: None
	"""
	global logged_users
	for user in logged_users:
		print(user)

	
##### MESSAGE HANDLING


def handle_getscore_message(conn:socket.socket, username: str) -> None:
	"""Receives a client's socket and his username and sends his score.

	Args:
		conn (socket.socket): client's socket
		username (str): client's username
  
	Returns: None
	"""
	global users
	build_and_send_message(conn, PROTOCOL_SERVER['your_score_msg'], users[username]['score'])


def handle_logged_message(conn:socket.socket) -> None:
	"""Receives a client's socket and sends all logged users.

	Args:
		conn (socket.socket): client's socket

	Returns: None
	"""
	global logged_users
	build_and_send_message(conn, PROTOCOL_SERVER['logged_answer_msg'], ','.join(logged_users.values()))


def handle_highscore_message(conn:socket.socket) -> None:
	"""
	Receives a client's socket and send highscores data

	Args:
		conn (socket.socket): client's socket
  
	Returns: None
	"""
	global users
	highscore = [(user, str(users[user]['score'])) for user in users]
	highscore.sort(key=lambda x: int(x[1]), reverse=True)
	print('\n'.join(list(map(lambda i:':'.join(i), highscore))))
	build_and_send_message(conn, PROTOCOL_SERVER['all_score_msg'], '\n'.join(list(map(lambda i:':'.join(i), highscore))))
  
    
def handle_question_message(conn:socket.socket, username: str) -> None:
	"""Receives client socket and username and sends a question."

	Args:
		conn (socket.socket): client's socket
		username (str): user's username
	
	Returns: None
	"""
	msg = create_random_question(username)
	if msg == None:
		build_and_send_message(conn, PROTOCOL_SERVER['no_questions_msg'], 'No questions left for you!')
	else:
		build_and_send_message(conn, PROTOCOL_SERVER['your_question_msg'], msg)


def handle_answer_message(conn:socket.socket, username:str, answer:str) -> None:
	"""Receives a client's socket, username and answer from the client and sends whether its a correct answer or not.

	Args:
		conn (socket.socket): a client's socket.
		username (str): user's username
		answer (str): data from client
	"""
    
	global users, questions
	id, choice = split_args(answer)
	if str(questions[int(id)]['correct']) == choice:
		users[username]['score'] += 5
		save_users(USERS_PATH)
		build_and_send_message(conn, PROTOCOL_SERVER['correct_answer_msg'])
	else:
		build_and_send_message(conn, PROTOCOL_SERVER['wrong_answer_msg'], questions[int(id)]['correct'])


def handle_signup_message(conn:socket.socket, data:str)-> None:
	"""Receives a client's socket and data from client and sends confirmation message.

	Args:
		conn (socket.socket): client's socket
		data (str): data from signup message
  
	Returns: None
	"""
	global logged_users
	args = split_args(data)
	logging.debug('handle_signup_message -- args: {}'.format(args))
	if args[0] not in users:
		add_user(USERS_PATH, *args)
		logged_users[conn.getpeername()] = args[0]
		build_and_send_message(conn, PROTOCOL_SERVER['signup_ok_msg'])
	else:
		send_error(conn, 'There is already a user with this username!')
    
    
def handle_logout_message(conn : socket.socket) -> None:
	"""Receives a client socket and removes it from logged_users dictioary

	Args:
		conn (socket.socket): client's socket
  
	Returns: None
	"""

	global logged_users
	try:
		del logged_users[conn.getpeername()]
	except KeyError:
		return


def handle_login_message(conn : socket.socket, data: str) -> None:
	"""Receives socket and message data of login message. Checks user and pass exists and match.
	If all ok, sends OK message and adds user and address to logged_users. If not - sends error message.
	Args:
		conn (socket.socket): client's socket
		data (str): data from login message
  
	Returns: None
	"""

	global users  # This is needed to access the same users dictionary from all functions
	global logged_users	 # To be used later
	
	args = split_args(data)
	logging.debug('handle_login_message -- args: {}'.format(args))
	msg = ''
	if args[0] in users:
		if args[1] == users[args[0]]['password']:
			if args[0] in logged_users.values():
				msg = 'You cannot login twice with the same user!'
			else:
				build_and_send_message(conn, PROTOCOL_SERVER['login_ok_msg'])
				logged_users[conn.getpeername()] = args[0]
				return
		else:
			msg = 'Incorrect password!'
	else:
		msg = "Username doesn't exist in the system!"
	send_error(conn, msg)


def handle_client_message(conn:socket.socket, cmd:str, data:str)-> None:
	"""Gets message code and data, and calls the right function to handle command

	Args:
		conn (socket.socket): client's socket
		cmd (str): message code
		data (data): message data
  
	Returns: None
	"""

	global logged_users	 # To be used later
	p_name = conn.getpeername()
	if cmd == PROTOCOL_CLIENT['login_msg']:
		handle_login_message(conn, data)
	elif cmd == PROTOCOL_CLIENT['signup_msg']:
		handle_signup_message(conn, data)
	elif conn.getpeername() in logged_users:
		if cmd == PROTOCOL_CLIENT['my_score_msg']:
			handle_getscore_message(conn, logged_users[p_name])
		elif cmd == PROTOCOL_CLIENT['get_question_msg']:
			handle_question_message(conn, logged_users[p_name])
		elif cmd == PROTOCOL_CLIENT['send_answer_msg']:
			handle_answer_message(conn, logged_users[p_name], data)
		elif cmd == PROTOCOL_CLIENT['logged_msg']:
			handle_logged_message(conn)
		elif cmd == PROTOCOL_CLIENT['highscore_msg']:
			handle_highscore_message(conn)
		else:
			send_error(conn, "Unknown command!")
	else:
		send_error(conn, "Command isn't available! Please login first")


def main():
	# Initializes global users and questions dicionaries using load functions
	global users
	global questions
	global messages_to_send
	open_client_sockets = []
	print("Welcome to Trivia Server!")
	
	users = load_user_database(USERS_PATH)
	questions = load_questions("questions.txt")
	server_socket = setup_socket()
 
	# Handling clients
	while True:
		rlist, wlist, xlist = select.select([server_socket] + open_client_sockets, open_client_sockets, [])
		for current_socket in rlist:
			if current_socket is server_socket:
				(new_socket, address) = server_socket.accept()
				print("New socket connected to server: ", new_socket.getpeername())
				open_client_sockets.append(new_socket)
			else:
				try:
					print ('New data from client {}!'.format(current_socket.getpeername()))
					data = current_socket.recv(MAX_MSG_LENGTH).decode()
					cmd, msg = parse_message(data)
				except ConnectionResetError:
					data, cmd, msg = '', '', ''
				p_id = current_socket.getpeername()
    
				if data == '' or cmd == PROTOCOL_CLIENT['logout_msg']:
					open_client_sockets.remove(current_socket)
					handle_logout_message(current_socket)
					print (f"Connection with client {p_id} closed.")
				else:
					handle_client_message(current_socket, cmd, msg)
		send_waiting_messages(wlist)


if __name__ == '__main__':
	main()

		
	