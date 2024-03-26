import azure.functions as func
import logging
import mimetypes
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import requests
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

    logging.info('Getting an authorization token for use with cognitive services.')

    token_url = "https://eastus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {
        "Ocp-Apim-Subscription-Key": os.getenv("SPEECH_API_KEY"),
        "Host": "eastus.api.cognitive.microsoft.com",
        "Content-type": "application/x-www-form-urlencoded",
        "Content-Length": "0"
    }

    response = requests.post(token_url, headers=headers)

    logging.info(f"Status code: {response.status_code}")

    access_token = response.text

    logging.info('Generate audio')

    # Generate the audio file using the SSML content
    tts_url = "https://eastus.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
        "Content-Type": "application/ssml+xml",
        "Content-Length": str(len(ssml)),
        "Host": "eastusa.tts.speech.microsoft.com",
        "Authorization": "Bearer " + access_token,
        "User-Agent": "talktome"
    }

    # Generate the audio file using the SSML content
    response = requests.post(tts_url, headers=headers, data=ssml, stream=False)

    logging.info(f"Status code: {response.status_code}")

    return func.HttpResponse(response.content, mimetype="audio/mpeg")