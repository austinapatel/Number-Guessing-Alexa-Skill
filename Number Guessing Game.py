# Number guessing game Amazon Alexa skill developed by Austin Patel

# Imports
from math import copysign, sqrt

# Variables
LOWER, UPPER = 1, 100

NUMBER_LIST_KEY, LAST_QUESTION_KEY, LAST_EXTENSION_KEY, NUM_QUESTIONS_KEY = 'number list', 'last question', \
                                                                         'last extension', 'num questions'

FOUND_NUMBER_SPEECH = 'I have determined that your number is '
UNEXPECTED_ANSWER_SPEECH = 'I was not expecting you to say that right now.'
WELCOME_SPEECH = 'Think of a number between 1 and 100, and I am going to figure it out. \
                 Answer each question with yes, or no.  Then, I am going to \
                 say numbers which you respond with lower, higher, or correct, based on your number. Let\'s begin... '

PRIME_QUESTION, NO_QUESTION = 'Is your number prime', 'No question, this should not be spoken.'
PRIME_QUESTION_HELP = 'A number is prime if it is greater than 1 and does not divide evenly with any number besides 1 and itself.  \
                      Answer this question with yes, or no.'
NUMBER_GUESS_QUESTION = ''
NUMBER_GUESS_QUESTION_HELP = 'I am going to say numbers and you respond with lower, higher, or correct \
                             based on the number you thought of.'

HELP_MESSAGES = {PRIME_QUESTION: PRIME_QUESTION_HELP,
                 NUMBER_GUESS_QUESTION: NUMBER_GUESS_QUESTION_HELP}

REPEAT_QUESTIONS = list(HELP_MESSAGES.values()) + [UNEXPECTED_ANSWER_SPEECH]

HIGHER_INTENT, LOWER_INTENT, NO_INTENT, YES_INTENT, START_INTENT = 'Higher', 'Lower', 'No', 'Yes', 'Start'
HELP_INTENT, CANCEL_INTENT, STOP_INTENT = 'AMAZON.HelpIntent', 'AMAZON.CancelIntent', 'AMAZON.StopIntent'

LAUNCH_REQUEST, INTENT_REQUEST, SESSION_ENDED_REQUEST = 'LaunchRequest', 'IntentRequest', 'SessionEndedRequest'


session_attributes = {}


# Initialization
def on_session_start():
    """ Initializes session attributes when the session is started """
    session_attributes[NUMBER_LIST_KEY] = [LOWER + i for i in range(UPPER - LOWER + 1)]
    session_attributes[LAST_QUESTION_KEY] = NO_QUESTION
    session_attributes[LAST_EXTENSION_KEY] = ''
    session_attributes[NUM_QUESTIONS_KEY] = 0


# Speech
def say(output='', reprompt_text='', title='', should_end_session=True):
    """ Builds a spoken response and will end the session by default """
    if reprompt_text == '':
        reprompt_text = output

    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'card': {
                'type': 'Simple',
                'title': title,
                'content': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }
    }


def question(question_base, extension='', intro=''):
    """ Asks a question and prepares the users response """
    session_attributes[LAST_QUESTION_KEY] = question_base
    session_attributes[LAST_EXTENSION_KEY] = extension
    # don't add to counter for repeat questions
    if intro not in REPEAT_QUESTIONS:
        session_attributes[NUM_QUESTIONS_KEY] += 1

    if extension != '':
        extension = ' ' + str(extension)

    question_text = question_base + extension + '?'

    return say(output=intro + ' ' + question_text, reprompt_text=question_text, should_end_session=False)


def welcome():
    """ Welcomes the user with a message and randomly picks a question to ask the user about their number """
    on_session_start()
    return question(PRIME_QUESTION, intro=WELCOME_SPEECH)


def help():
    """ Helps the user based on where they currently are in the program """
    last_question = session_attributes[LAST_QUESTION_KEY]
    last_extension = session_attributes[LAST_EXTENSION_KEY]

    if last_question == NO_QUESTION:
        return welcome()
    else:
        return question(last_question, extension=last_extension, intro=HELP_MESSAGES[last_question])


def end():
    """ Terminates the current session """
    return say()


def unexpected_response():
    """Returns the unexpected response speech."""
    return say(UNEXPECTED_ANSWER_SPEECH)


# Helper
def get_middle():
    """ Returns the middle item in the number list (by position not value) picks lower middle index if number
    is even
    """
    num_list = session_attributes[NUMBER_LIST_KEY]
    return num_list[round(len(num_list) / 2) - 1]  # Subtract 1 since arrays start at 0


def round(x):
    """ Rounds a number up if the decimal portion of the number is >= 0.5 """
    return int(x + copysign(0.5, x))


def is_prime(n):
    if n <= 1:
        return False

    for i in range(2, int(sqrt(n)) + 1):
        if n % i == 0:
            return False

    return True


# Game logic
def question_answer(response):
    """ Handles the users response to a given question and the scenario in which this
    intent is called even though there was no question given

    Parameters:
        response: a string that is the name of an intent
    """
    # handle answers to previous questions
    last_question = session_attributes[LAST_QUESTION_KEY]
    last_extension = session_attributes[LAST_EXTENSION_KEY]

    try:
        keep_in_numbers(get_filter(last_question, last_extension, response))
    except Exception:
        return question(last_question, last_extension, intro=UNEXPECTED_ANSWER_SPEECH)

    # check to see if the number was determined
    num_list = session_attributes[NUMBER_LIST_KEY]

    if len(num_list) == 1:
        speech = FOUND_NUMBER_SPEECH + str(num_list[0]) + ', it took me ' + \
                 str(session_attributes[NUM_QUESTIONS_KEY]) + ' questions to figure it out.'
        return say(speech, should_end_session=True)

    # ask the next question
    return question(NUMBER_GUESS_QUESTION, extension=get_middle())


def get_filter(last_question, last_extension, response):
    if last_question == PRIME_QUESTION:
        if response == YES_INTENT:
            return lambda n: is_prime(n)
        elif response == NO_INTENT:
            return lambda n: not is_prime(n)
    elif last_question == NUMBER_GUESS_QUESTION:
        if response == HIGHER_INTENT:
            return lambda n: n > last_extension
        elif response == LOWER_INTENT:
            return lambda n: n < last_extension
        elif response == YES_INTENT:
            return lambda n: n == last_extension

    raise Exception


def keep_in_numbers(predicate):
    """ Keeps or remove each number in the number list that returns a true value for a given predicate function.
    Defaults to keeping the number
    """
    session_attributes[NUMBER_LIST_KEY] = [n for n in session_attributes[NUMBER_LIST_KEY] if predicate(n)]


# Event handlers and related variables
def handle_intent(intent_name):
    """ Called when the user specifies an intent for this skill """
    if intent_name in name_to_handler:
        return name_to_handler[intent_name]()
    else:
        return question_answer(intent_name)


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    # Have to add 'attributes' entry into the event session since it could not find
    # it from a physical device even though it worked in the online testing
    if 'attributes' not in event['session']:
        event['session']['attributes'] = {}

    global session_attributes
    session_attributes = event['session']['attributes']

    if event['session']['new']:
        on_session_start()

    return request_to_handler[event['request']['type']](event)


name_to_handler = {HELP_INTENT: help,
                   CANCEL_INTENT: end,
                   STOP_INTENT: end,
                   START_INTENT: welcome}

request_to_handler = {LAUNCH_REQUEST: lambda event: welcome(),
                      INTENT_REQUEST: lambda event: handle_intent(event['request']['intent']['name']),
                      SESSION_ENDED_REQUEST: lambda event: end()}
