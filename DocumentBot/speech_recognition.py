import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import os

load_dotenv(r".\environment.env")

SPEECH_KEY = os.getenv("SPEECH_KEY")

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region="westeurope")
speech_config.speech_recognition_language = "it-IT" 
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

def recognize_from_microphone():
    
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config= audio_config)

    print("parla al microfono")
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Riconosciuto: {}".format(speech_recognition_result.text))
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")

def chatbot_speak(answer):
    speech_config.speech_synthesis_voice_name='fr-FR-VivienneMultilingualNeural'
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config= audio_config)
    speech_synthesizer.speak_text_async(answer).get()
