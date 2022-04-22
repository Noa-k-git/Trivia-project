from chatlib import *

from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar

from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.popup import Popup

SERVER_IP = "127.0.0.1"  # The server run on the same computer as client
SERVER_PORT = 5678
# HELPER SOCKET METHODS
# HELPER SOCKET METHODS
def build_and_send_message(conn:socket.socket, code:str, msg = '') -> None:
	"""
 	Builds a new message using chatlib, wanted code and message. 
	Prints debug info, then sends it to the given socket.

	Args:
		conn (socket.socket): client's socket object.
		code (str): the message's code.
		msg (str, optional): the message's data. Defaults to ''.
	
	Returns: None
	"""
	message = build_message(code, msg)
	logging.debug('Sending: {}'.format(message))
	conn.send(message.encode())


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
	# if cmd == chatlib.PROTOCOL_SERVER['error_msg']:
	# 	error_and_exit(msg)
	logging.debug('Received: {0}\n -- Parsed: > cmd - {1}  > msg - {2}'.format(data, cmd, msg))
	return cmd, msg


def build_send_recv_parse(conn:socket.socket, code:str, data = '') -> tuple:
    """Receives server socket, message code and data, builds message and sends it using chatlib and receives and parse the response. 

    Args:
        conn (socket.socket): sever socket
        code (str): message code
        data (str, optional): data to send. Defaults to ''.

    Returns:
        cmd (str) and date (str) of the received message.
		If error occured, will return None, None
    """
    build_and_send_message(conn, code, data)
    return recv_message_and_parse(conn)


def connect()->socket.socket:
    """Builds a socket and connects it to server, returns the socket.

    Returns:
        socket.socket: socket connected to the sever.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((SERVER_IP, SERVER_PORT))
    return server_socket

# -----------------------------------------------------

class LoginScreen(Screen):
    """Defines Login screen.

    This class is used in the design file.
    """
    def login(self, conn:socket.socket)-> bool:
        """Receives server socket, sends a login message to server and receives its response.

        Args:
            conn (socket.socket): server socket.

        Returns:
            bool: If login was successful, returns True, otherwise returns False.
        """
        global g_username
        username, password = self.ids.username.text, self.ids.password.text
        if username == '' or password == '' :
            Snackbar(text = "Error! You have to enter values in all fields.").open()
            return False
        cmd, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['login_msg'], join_args([username, password]))
        for i in self.ids:
            self.ids[i].text = ''
        
        if cmd != PROTOCOL_SERVER['login_ok_msg']:
            Snackbar(text = msg).open()
            return False

        self.manager.screens[2].ids.username.text = username
        return True
   
   
class SignupScreen(Screen):
    """Defines Sign Up screen.
    
    This class is used in the design file."""
    def sign_up(self, conn:socket.socket)->bool:
        """Receives a server socket, sends a sign up request and Receives the response.

        Args:
            conn (socket.socket): server socket

        Returns:
            bool: return True if sign up succeeded, False otherwise.
        """
        global g_username
        username, password, verify = self.ids['username'].text, self.ids['password'].text, self.ids['verify_password'].text
        if username == '' or password == '' or verify == '':
            Snackbar(text = "Error! You have to enter values in all fields.").open()
            
        if password != verify:
            self.ids['verify_password'].text = ''
            Snackbar(text = "Error! The passwords don't match").open()
            return False
        
        for i in self.ids:
            self.ids[i].text = ''
        
        cmd, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['signup_msg'], join_args([username, password]))
        if cmd != PROTOCOL_SERVER['signup_ok_msg']:
            Snackbar(text = msg).open()
            return False
        
        self.manager.screens[2].ids.username.text = username
        return True

    
class HomeScreen(Screen):
    """Defines the home screen of the application.
    
    Used in the disgin file.
    """
    question = [] # will contain a question from server.
    def play_question(self, conn:socket.socket)-> bool:
        """Receives server socket and gets a question from server.
        If question received, show it in a popup window.

        Args:
            conn (socket.socket): server socket.

        Returns:
            bool: True if received a question, False otherwise.
        """
        msg_code, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['get_question_msg'])
        if msg_code == PROTOCOL_SERVER['no_questions_msg'] != msg_code == PROTOCOL_SERVER['error_msg']:
            Snackbar(text = msg).open()
            return False
        self.question = msg.split(ARGS_DELIMITER)
        popup_question = QuestionWindow(self.question) # Creates a popup window with the question.
        popup_question.open() # Opens the popup window
        return True
    

class QuestionWindow(Popup):
    """Defines a popup window for question.
    
    Used in the design file.
    """
    def __init__(self, question):
        """Initiolize the object.

        Args:
            question (list): a question from server.
        """
        self.question = question
        super().__init__()
        
    def send_answer(self, conn:socket.socket)-> bool:
        """Receives server socket and send to server ansewer from the user.

        Args:
            conn (socket.socket): server socket

        Returns:
            bool: True if answer is by protocol, False otherwise.
        """
        answer = self.user_answer.text
        if answer != '1' and answer != '2' and answer != '3' and answer != '4':
            Snackbar(text = 'Your answer must be a value between 1 and 4!').open() 
            return False
        msg_code, msg = build_send_recv_parse(conn, PROTOCOL_CLIENT['send_answer_msg'], join_args((self.question[0], answer)))
        if msg_code == PROTOCOL_SERVER['correct_answer_msg']:
            Snackbar(text='[color=#ddbb34]Correct![/color]', duration = .3).open()
        elif msg_code == PROTOCOL_SERVER['wrong_answer_msg']:
            Snackbar(text='[color=#ddbb34]Wrong answer! The correct answer was {} ({}).[/color]'.format(msg, self.question[int(msg) + 1])).open()
        else:
            Snackbar(text=msg)
        return True
    

class LoggedWindow(Popup):
    """Defines a popup window for logged users.
    
    Used in design file."""
    pass


class HighScoreWindow(Popup):
    """Defines a popup window for high scores.
    
    Used in design file."""
    pass
    
    
class MyScreenManager(ScreenManager):
    "Defines a screen manager, used in design file."
    pass


class MyTriviaApp(MDApp):
    """Creates the trivia app."""
    try:
        server_socket = connect() # server socket
    except ConnectionRefusedError:
        logging.error("\nConnectionRefusedError: No connection could be made, please try again later.")
        exit()
        
    def build(self):
        """Builds the upp by design file."""
        
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'BlueGray'

        return Builder.load_file('design.kv')
    
    def get_score(self):
        """Sends a get_score request to the server and display the response."""

        msg_code, msg = build_send_recv_parse(self.server_socket, PROTOCOL_CLIENT['my_score_msg'])
        if msg_code == PROTOCOL_SERVER['your_score_msg']:
            Snackbar(text='[color=#ddbb34]YOUR SCORE: {} [/color]'.format(msg)).open()
        else:
            Snackbar(text=msg).open()
    
    def get_highscore(self):
        """Sends a high score request to the server and display the response."""
        return build_send_recv_parse(self.server_socket, PROTOCOL_CLIENT['highscore_msg'])[1].replace(':', '  :  ')

    def get_logged_users(self):
        """Sends a logged users request to the server and display the response."""

        return build_send_recv_parse(self.server_socket, PROTOCOL_CLIENT['logged_msg'])[1].replace(',', ', ')
    
    def logout(self):
        """Sends a get_score request to the server."""
        build_and_send_message(self.server_socket, PROTOCOL_CLIENT['logout_msg'])
        self.server_socket = connect()


if __name__ == '__main__':
    MyTriviaApp().run()
