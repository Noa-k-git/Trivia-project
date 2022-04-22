from chatlib import *  # To use chatlib functions or consts, use chatlib.****


SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
# logging.basicConfig(level=logging.WARNING)
# HELPER SOCKET METHODS
def build_and_send_message(conn : socket.socket, code, msg = ''):
	"""
	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.
	Paramaters: conn (socket object), code (str), msg (str)
	Returns: Nothing
	"""
	message = build_message(code, msg)
	logging.debug('Sending: {}'.format(message))
	conn.send(message.encode())
	

def recv_message_and_parse(conn) -> tuple:
	"""
	Receives a new message from given socket.
	Prints debug info, then parses the message.
	Paramaters: conn (socket object)
	Returns: cmd (str) and data (str) of the received message. 
	If error occured, will return None, None
	"""
	data = conn.recv(MAX_MSG_LENGTH).decode()
	cmd, msg = parse_message(data)
	# if cmd == chatlib.PROTOCOL_SERVER['error_msg']:
	# 	error_and_exit(msg)
	logging.debug('Received: {0}\n -- Parsed: > cmd - {1}  > msg - {2}'.format(data, cmd, msg))
	return cmd, msg
	

	
def build_send_recv_parse(conn, code, data = '') -> tuple:
    build_and_send_message(conn, code, data)
    return recv_message_and_parse(conn)
    
def connect():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((SERVER_IP, SERVER_PORT))
    return server_socket


def error_and_exit(msg):
    print(msg)
    exit()


def login(conn):
    username, password = user_info()
    cmd, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['login_msg'], join_args([username, password]))
    cancel = 'n'
    while cmd != PROTOCOL_SERVER['login_ok_msg']:
        print(msg, '\n')
        username, password = user_info()
        cmd, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['login_msg'], join_args([username, password]))
        logging.debug('cmd: {}'.format(cmd))

    print("You are logged in!")
    return True

def user_info(signup = False):
    username = input("Please enter username: \n")
    password = input("Please enter password: \n")
    if signup:
        verify_password = input("Please enter the password again:\n")
        while verify_password != password:
            print("\nThe passwords don't match, please try again.")
            password = input("Please enter password: \n")
            verify_password = input("Please enter the password again:\n")
    
    return username, password

def sign_up(conn):
    username, password = user_info(signup=True)
    print('Your info:\n  username: ' + username + '\n  password: ' + password)
    procceed = input("Would you like to procceed? (Y/n)\n").lower()
    while procceed != 'y' and procceed != 'n':
        procceed = input("Would you like to procceed? (Y/n)\n").lower()
        
    if procceed == 'n':
        return False
    
    cmd, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['signup_msg'], join_args([username, password]))
    while cmd != PROTOCOL_SERVER['signup_ok_msg']:
        print("{}\n".format(msg))
        to_exit = input("Would you like to exit? (Y/n)\n").lower()
        while to_exit != 'y' and to_exit != 'n':
            to_exit = input("Would you like to exit? (Y/n)\n").lower()
        if to_exit == 'y':
            return False
        username, password = user_info(signup=True)
        cmd, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['signup_msg'], join_args([username, password]))
        logging.debug('cmd: {}'.format(cmd))

    print("You are logged in!")
    return True
    
    
def enter_game(conn):
    inp = input("\nPlease Choose an option:\n1: sign_up\t\t2: login\n")
    while inp != "1" and inp != "2":
        inp = input("Please Choose an option:\n1: sign_up\t\t2: login\n")
    if inp == '1':
        success = sign_up(conn)
    else:
        success = login(conn)
    if not success:
        enter_game(conn)
    
        
def logout(conn):
    build_and_send_message(conn, PROTOCOL_CLIENT['logout_msg'])
    
def get_score(conn):
    msg_code, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['my_score_msg'])
    if msg_code == PROTOCOL_SERVER['your_score_msg']:
        print("Your Score: " + msg)
    else:
        print("Some Error Accured!")

def play_question(conn):
    msg_code, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['get_question_msg'])
    if msg_code == PROTOCOL_SERVER['no_questions_msg']:
        print('No more questions left!')
        return
    question = msg.split(ARGS_DELIMITER)
    logging.debug('question: {}'.format(question))
    answer = input('{0}) {1}\n  1) {2}\n  2) {3}\n  3) {4}\n  4) {5}\n\n'.format(*question))
    while answer != '1' and answer != '2' and answer != '3' and answer != '4':
        answer = input("\nInvalid value. Please answer the question with number between 1 and 4:\n\n  ")
    msg_code, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['send_answer_msg'], join_args((question[0], answer)))
    if msg_code == PROTOCOL_SERVER['correct_answer_msg']:
        print('\nCorrect answer!')
        get_score(conn)
    elif msg_code == PROTOCOL_SERVER['wrong_answer_msg']:
        print('\nWrong answer!\nThe correct answer was {} ({}).'.format(msg, question[int(msg) + 1]))
    else:
        error_and_exit(msg)
        
def get_highscore(conn):
    print(build_send_recv_parse(conn, PROTOCOL_CLIENT['highscore_msg'])[1])

def get_logged_users(conn):
    print(build_send_recv_parse(conn, PROTOCOL_CLIENT['logged_msg'])[1])
    
def main():
	server_socket = connect()
	enter_game(server_socket)
	user_options = {
	"h" : ("Get high score", get_highscore),
	"l" : ("Get logged users", get_logged_users),
	"m" : ("Get my score", get_score),
	"t" : ("Play a trivia question", play_question),
	"q" : ("quit", logout)}
	output = "Please Choose an option from the list below:\n\n"
	for i in user_options:
		output += '  ' + i + ') ' + user_options[i][0] + '\n'
	cmd = ''
	while 'q' not in cmd:
		cmd = input('\n' + output).lower()
		while cmd not in user_options.keys():
			cmd = input("\nUnrecognized command. \n\n" + output).lower()
		user_options[cmd][1](server_socket)
  

if __name__ == '__main__':
    main()
