from __future__ import print_function
import json
import boto3

config_file = open('lambda_config.json', 'r')
config = json.loads(config_file.read())
sqs_url = config['sqs_url']
sqs = boto3.client('sqs')

def lambda_handler(event, context):

    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

def send_message(body, attributes):
    response = sqs.send_message(
        QueueUrl=sqs_url,
        MessageBody=body,
        MessageAttributes=attributes)
    return response

def on_launch(request, session):
    output = "Please tell me a song you would like to hear"
    title = "Welcome"
    reprompt = None
    should_end_session = True
    return build_response({}, build_speechlet_response(title, output, reprompt, should_end_session))

def on_intent(request, session):

    # Defaults
    should_end_session = True
    reprompt_text = None
    title = ''
    output = ''

    if request['intent']['name'] == 'sendAudioIntent':
        query = request['intent']['slots']['Query']['value']
        output = "Ok. You asked me to play %s" % query
        title = "Chromecast Play"
        send_message(
            query,
            {
                'query': {
                    'StringValue': query,
                    'DataType': 'String'
                },
                'type': {
                    'StringValue': 'query',
                    'DataType': 'String'
                }
            })

    if request['intent']['name'] == 'AMAZON.StopIntent':
        title = "Chromecast Stop"
        output = "Stopping"
        send_message(
            'Stop Request',
            {
                'type': {
                    'StringValue': 'stop_request',
                    'DataType': 'String'
                }
            })

    if request['intent']['name'] == 'AMAZON.PauseIntent':
        title = "Chromecast Pause"
        output = "Pausing"
        send_message(
            'Pause Request',
            {
                'type': {
                    'StringValue': 'pause_request',
                    'DataType': 'String'
                }
            })

    if request['intent']['name'] == 'AMAZON.ResumeIntent':
        title = "Chromecast Resume"
        output = "Resuming"
        send_message(
            'Resume Request',
            {
                'type': {
                    'StringValue': 'resume_request',
                    'DataType': 'String'
                }
            })

    return build_response({}, build_speechlet_response(title, output, reprompt_text, should_end_session))

def on_session_started(request, session):
    pass
def on_session_ended(request, session):
    pass

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    if output == None:
        return {
            'shouldEndSession': should_end_session
        }
    elif title == None:
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'reprompt': {
                'outputSpeech': {
                    'type': 'PlainText',
                    'text': reprompt_text
                }
            },
            'shouldEndSession': should_end_session
        }
    else:
        return {
            'outputSpeech': {
                'type': 'PlainText',
                'text': output
            },
            'card': {
                'type': 'Simple',
                'title':  title,
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


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }

