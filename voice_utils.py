import json

import pygame
import speech_recognition as sr
import requests
from pydub import AudioSegment
import io
from io import BytesIO
import os
from tempfile import NamedTemporaryFile
from gpt3_module import generate_text
import time


YANDEX_API_KEY = "AQVN04O1SbWI-Dgpg2tfNEmtQL58HhHTLUjqRjQB"

def recognize_speech(audio_file, api_key):
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    headers = {
        "Authorization": f"Api-Key {api_key}"
    }

    with open(audio_file, "rb") as f:
        data = f.read()

    response = requests.post(url, headers=headers, data=data)
    result = json.loads(response.text)

    print("Yandex SpeechKit API Response:", result)

    return result.get("result")

def recognize_speech_from_mic(recognizer, microphone, api_key):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
        except sr.WaitTimeoutError:
            return None

    audio_segment = AudioSegment.from_file(BytesIO(audio.get_wav_data(convert_rate=16000)))
    audio_data = audio_segment.export(format="ogg", codec="opus", parameters=["-strict", "-2"])

    with NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        audio_data.seek(0)
        f.write(audio_data.read())
        temp_file_name = f.name

    try:
        recognized_text = recognize_speech(temp_file_name, api_key)
    finally:
        os.remove(temp_file_name)

    return recognized_text

def synthesize_speech(text, api_key):
    url = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"

    headers = {
        "Authorization": f"Api-Key {api_key}"
    }

    data = {
        "text": text,
        "lang": "ru-RU",
        "format": "oggopus",
        "voice": "jane",
        "emotion": "good"
    }

    response = requests.post(url, headers=headers, data=data)
    if response.status_code != 200:
        raise RuntimeError("Yandex SpeechKit API error: " + str(response.status_code))

    audio_data = io.BytesIO(response.content)
    audio_segment = AudioSegment.from_file(audio_data, format="ogg")
    with NamedTemporaryFile(suffix=".ogg", delete=False) as f:
        audio_segment.export(f, format="ogg")
        temp_file_name = f.name

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(temp_file_name)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    finally:
        pygame.mixer.quit()
        time.sleep(2)  # добавьте эту строку
        os.remove(temp_file_name)

def process_query(text, api_key, answer_mode="voice"):
    if answer_mode == "text" or "текстовый ответ" in text.lower():
        text = text.replace("текстовый ответ", "").strip()
        response_text = generate_text(text)
        print(f"GPT-3.5-turbo response: {response_text}")
    else:
        response_text = generate_text(text)
        synthesize_speech(response_text, api_key)

if __name__ == "__main__":
    recognizer = sr.Recognizer()
    microphone = sr.Microphone(chunk_size=1024, sample_rate=16000)

    recognized_text = recognize_speech_from_mic(recognizer, microphone, YANDEX_API_KEY)
    if recognized_text is None:
        print("Error: No text recognized.")
    else:
        print(f"Recognized text: {recognized_text}")
        if "голосовой ответ" in recognized_text.lower():
            recognized_text = recognized_text.replace("голосовой ответ", "").strip()
            process_query(recognized_text, YANDEX_API_KEY, answer_mode="voice")
        elif "текстовый ответ" in recognized_text.lower():
            recognized_text = recognized_text.replace("текстовый ответ", "").strip()
            process_query(recognized_text, YANDEX_API_KEY, answer_mode="text")
        else:
            process_query(recognized_text, YANDEX_API_KEY, answer_mode="voice")