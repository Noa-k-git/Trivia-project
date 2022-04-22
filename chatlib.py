import socket
import logging, coloredlogs
coloredlogs.install(level='DEBUG')
coloredlogs.install(level='ERROR')

# Protocol Constants
CMD_FIELD_LENGTH = 16	# Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
ARGS_DELIMITER = '#'
# Protocol Messages 
# In this dictionary we will have all the client and server command names
logging.basicConfig(level=logging.DEBUG)
PROTOCOL_CLIENT = {
"login_msg" : "LOGIN",
"signup_msg" : "SIGNUP",
"logout_msg" : "LOGOUT",
"logged_msg" : "LOGGED",
"get_question_msg" : "GET_QUESTION",
"send_answer_msg" : "SEND_ANSWER",
"my_score_msg" : "MY_SCORE",
"highscore_msg" : "HIGHSCORE",
}


PROTOCOL_SERVER = {
"login_ok_msg" : "LOGIN_OK",
"signup_ok_msg" : "SIGNUP_OK",
"logged_answer_msg" : "LOGGED_ANSWER",
"correct_answer_msg" : "CORRECT_ANSWER",
"wrong_answer_msg" : "WRONG_ANSWER",
"your_score_msg" : "YOUR_SCORE",
"your_question_msg" : "YOUR_QUESTION",
"all_score_msg" : "ALL_SCORE",
"error_msg" : "ERROR",
"no_questions_msg" : "NO_QUESTIONS",

}


# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd:str, data:str)->str:
    """
    Receives command name and data field and creates a valid protocol message

    Args:
        cmd (str): command name
        data (str): data

    Returns:
        str: a valid protocol message or None if error occured.
    """
    message_lst = []
    if cmd in PROTOCOL_CLIENT:
        message_lst.append(PROTOCOL_CLIENT[cmd])
    elif cmd in PROTOCOL_SERVER:
        message_lst.append(PROTOCOL_SERVER[cmd])
    elif cmd in PROTOCOL_CLIENT.values() or cmd in PROTOCOL_SERVER.values():
        message_lst.append(cmd)
    else:
        message_lst.append(None)
    
    if message_lst[0] != None:
        message_lst[0] = message_lst[0] + ' ' * (CMD_FIELD_LENGTH - len(message_lst[0]))
    
    length = len(str(data))
    if length <= MAX_DATA_LENGTH:
        message_lst.append('0' * (LENGTH_FIELD_LENGTH - len(str(length))) + str(length))
    else:
        message_lst.append(None)
    
    message_lst.append(data)
    for i in message_lst:
        if i == None:
            return None   
    
    full_msg = join_msg(message_lst)
    return full_msg


def parse_message(data : str) -> tuple:
    """Receives data, parses protocol message and returns command name and data field.

    Args:
        data (str): message.

    Returns:
        tuple: cmd (str), data (str). If some error occured, returns None, None
    """
    cmd, x, msg = split_msg(data, 3)
    if cmd == None:
        return cmd, msg
    return cmd.replace(' ', ''), msg

	
def split_msg(msg:str, expected_fields:int)-> list:
    """Helper method. Receives a string and number of expected fields in it. Splits the string 
	using protocol's delimiter (|) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occured, returns list of None

    Args:
        msg (str): a message.
        expected_fields (int): expected fields in the message.

    Returns:
        list of fields if all ok. If some error occured, returns list of None.
    """
    error_message = [ERROR_RETURN] * 3
    if msg.count(DELIMITER) < expected_fields - 1:
        return error_message
    
    lst = msg.split(DELIMITER, expected_fields - 1)
    try:
        if int(lst[1]) != len(lst[2]):
            return error_message
    except:
        return error_message
   
    return lst


def split_args(args:str, delimiter = ARGS_DELIMITER)-> str:
    """	Helper method. Gets a list, joins all of it's fields to one string divided by the args' delimiter. 

    Args:
        args (str): strings of arguments.
        delimiter (str, optional): the delimiter between each argument. Defaults to ARGS_DELIMITER.

    Returns:
        str: string that looks like arg1#arg2#arg3
    """
    return args.split(delimiter)


def join_msg(msg_fields:list)->str:
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the delimiter. 
    Args:
        msg_fields (list): list to join.
    Returns: 
        str: string that looks like cell1|cell2|cell3
    """
    msg_fields = (str(field) for field in msg_fields)
    return DELIMITER.join(msg_fields)


def join_args(args:list, delimiter = ARGS_DELIMITER)->str:
    """
	Helper method. Gets a list, joins all of it's fields to one string divided by the args' delimiter. 
    Args:
        args (list): list of arguments to join.
        delimiter (str, optional): the delimiter to join between each argument. Defaults to ARGS_DELIMITER.
	Returns: 
        str: string that looks like arg1#arg2#arg3
	"""
    args = (str(arg) for arg in args)
    return delimiter.join(args)
