import azure.functions as func
import logging
import mimetypes
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import azure.cognitiveservices.speech as speechsdk

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="GenerateConversation")
def GenerateConversation(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Starting conversation function.')

    host = "Brian"
    guest = "Emma"
    
    logging.info('Loading environment variables.')
    load_dotenv()
    
    logging.info('Retrieving content from request.')
    content = req.params.get('content')
    
    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        content = req_body.get('content')    
    
    logging.info('Creating Azure Open AI')
    client = AzureOpenAI(azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"), api_version="2023-07-01-preview", api_key=os.getenv("OPENAI_API_KEY"))
    
    logging.info('Constructing prompt')
    message_text = [
        {"role":"system","content":"""
            You're going to create a transcript for an engaging conversation between Brian and Andrew, based on the content below. They should ask each other questions and respond to each other.
            Do not talk about any other topic.
            Transform the text to the Speech Syntheses Markup Language.  
            - [Brian] should use the voice with name en-US-BrianNeural
            - [Andrew] should use the voice with name en-US-AndrewNeural
            - There is no need for introductions anymore. No "welcome" needed.
            - The output should be XML.
            - Make sure that every line is wrapped between <voice> and </voice> element.                
            - Finally, make sure there is the following element at the start: <speak xmlns""http://www.w3.org/2001/10/synthesis"" xmlns:mstts=""http://www.w3.org/2001/mstts"" xmlns:emo=""http://www.w3.org/2009/10/emotionml"" version=""1.0"" xml:lang=""en-US"">
            - End the XML document with the following element: </speak>
            - Delete [Brian]: and [Andrew]: from the transcript.
            ------------""" + content},
        {"role":"user","content":"generate the conversation"}
    ]
    
    logging.info('Calling GPT model')
    completion = client.chat.completions.create(
        model="gpt-35-turbo-16k", # gpt-4-32k also possible
        messages = message_text,
        temperature=0.8,
        max_tokens=8000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    
    ssml = completion.choices[0].message.content
    
    logging.info('Transforming ssml into speech')

    service_region = "eastus"
    speech_key = os.getenv("SPEECH_API_KEY")
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio24Khz96KBitRateMonoMp3)  

    filename = "conversation.mp3"
    file_config = speechsdk.audio.AudioOutputConfig(filename=filename)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=file_config)  
    result = speech_synthesizer.speak_ssml_async(ssml).get()
    
    logging.info('Done with conversation function.')
    
    with open(filename, 'rb') as f:
        mimetype = mimetypes.guess_type(filename)
        return func.HttpResponse(f.read(), mimetype=mimetype[0])