# Number guessing game Amazon Alexa skill developed by Austin Patel

# Imports
from math import copysign, sqrt

# Variables
LOWER, UPPER = 1, 100

NUMBER_LIST_KEY, LAST_QUESTION_KEY, LAST_NUMBER_KEY, NUM_QUESTIONS_KEY = 'number list', 'last question', \
                                                                         'last number', 'num questions'

START_SPEECH = 'Think of a number between 1 and 100, inclusive.  Now I am going to attempt to guess your number.'
HELP_SPEECH = 'Once you have thought of a number between 1 and 100, I am going to ask you some questions ' \
              'and figure out what number you thought of.'
FOUND_NUMBER_SPEECH = 'I have determined that your number is '
UNEXPECTED_ANSWER_SPEECH = 'I was not expecting you to say that right now.'
WELCOME_SPEECH = 'Welcome to the number game.  Think of a number between 1 and 100, and I am going to figure' \
                 'out what number you are thinking of, by asking you a few questions. Let\'s begin... '

LESS_THAN_QUESTION, GREATER_THAN_QUESTION,  = 'Is your number less than', 'Is your number greater than'
PRIME_QUESTION, NO_QUESTION = 'Is your number prime', ''
PLAY_NOW_QUESTION = 'Would you like to play the game now'

session_attributes = {}


# Initialization
def on_session_start():
    """ Initializes session attributes when the session is started """
    session_attributes[NUMBER_LIST_KEY] = [LOWER + i for i in range(UPPER - LOWER + 1)]
    session_attributes[LAST_QUESTION_KEY] = NO_QUESTION
    session_attributes[LAST_NUMBER_KEY] = -1
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
    session_attributes[LAST_NUMBER_KEY] = extension
    session_attributes[NUM_QUESTIONS_KEY] += 1

    if extension != '':
        extension = ' ' + str(extension)

    question_text = question_base + extension + '?'

    return say(output=intro + ' ' + question_text, reprompt_text=question_text, should_end_session=False)


def welcome():
    """ Welcomes the user with a message and randomly picks a question to ask the user about their number """
    on_session_start()
    return question(PRIME_QUESTION, intro=WELCOME_SPEECH)


def end():
    """ Terminates the current session """
    return say()


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
def question_answer(is_yes):
    """ Handles the users response to a given question and the scenario in which this
    intent is called even though there was no question given
    """
    last_question = session_attributes[LAST_QUESTION_KEY]
    last_number = session_attributes[LAST_NUMBER_KEY]

    if last_question == PLAY_NOW_QUESTION:
        if is_yes:
            on_session_start()
            return question(PRIME_QUESTION)
        else:
            return end()
    elif last_question == NO_QUESTION:
        return say(UNEXPECTED_ANSWER_SPEECH)
    else:
        keep_in_numbers(get_filter(last_question, last_number), keep=is_yes)

    num_list = session_attributes[NUMBER_LIST_KEY]

    if len(num_list) == 1:
        speech = FOUND_NUMBER_SPEECH + str(num_list[0]) + ', it took me ' + \
                 str(session_attributes[NUM_QUESTIONS_KEY]) + ' questions to figure it out.'
        return say(speech, should_end_session=True)

    # Alternate between the less than or greater than questions, and don't pick the less than question if there
    # are only two items in the number list because middle will return the lower of those values and it doesn't
    # make sense to ask if the number is less than the lowest possible value left since it cannot be
    if last_question == GREATER_THAN_QUESTION and len(num_list) > 2:
        return question(LESS_THAN_QUESTION, get_middle())
    else:
        return question(GREATER_THAN_QUESTION, get_middle())


def get_filter(last_question, last_number):
    if last_question == PRIME_QUESTION:
        return lambda n: is_prime(n)
    elif last_question == GREATER_THAN_QUESTION:
        return lambda n: n > last_number
    elif last_question == LESS_THAN_QUESTION:
        return lambda n: n < last_number


def keep_in_numbers(predicate, keep=True):
    """ Keeps or remove each number in the number list that returns a true value for a given predicate function.
    Defaults to keeping the number
    """
    session_attributes[NUMBER_LIST_KEY] = [n for n in session_attributes[NUMBER_LIST_KEY]
                                           if (predicate(n) if keep else not predicate(n))]


# Event handlers and related variables
def handle_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """
    intent_name = intent_request['intent']['name']

    if intent_name in name_to_handler:
        return name_to_handler[intent_name]()
    else:
        raise ValueError('Invalid intent')


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


name_to_handler = {'AMAZON.HelpIntent': lambda: question(PLAY_NOW_QUESTION, intro=HELP_SPEECH),
                   'AMAZON.CancelIntent': end,
                   'AMAZON.StopIntent': end,
                   'Yes': lambda: question_answer(True),
                   'No': lambda: question_answer(False),
                   'Start': welcome}

request_to_handler = {'LaunchRequest': lambda event: welcome(),
                      'IntentRequest': lambda event: handle_intent(event['request'], event['session']),
                      'SessionEndedRequest': lambda event: end()}
