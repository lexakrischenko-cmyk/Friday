import datetime
import time
import os
import re
import numpy as np
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import torch
import warnings

# Отключаем лишние предупреждения в консоли
os.environ["PYTHONWARNINGS"] = "ignore"
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
warnings.filterwarnings("ignore", category=UserWarning, module="speechbrain")

# ==================== НАСТРОЙКА SILERO TTS (ЧИСТЫЙ РУССКИЙ) ====================
print("⏳ Загрузка голосовой модели Silero...")
VOICE_LOADED = False
model = None
engine_tts = None

try:
    # Загружаем официальную русскую модель v3
    model, _ = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_tts',
        language='ru',
        speaker='ru_v3',
        verbose=False
    )
    model.to(torch.device('cpu'))
    VOICE_LOADED = True
    print("✅ Голосовая модель Silero загружена")
except Exception as e:
    print(f"❌ Ошибка загрузки Silero: {e}")
    print("⏳ Загрузка резервного TTS (pyttsx3)...")
    import pyttsx3
    engine_tts = pyttsx3.init()
    voices = engine_tts.getProperty('voices')
    for voice in voices:
        if 'russian' in voice.name.lower() or 'русский' in voice.name.lower():
            engine_tts.setProperty('voice', voice.id)
            break
    engine_tts.setProperty('rate', 165)
    engine_tts.setProperty('volume', 0.7)

# ==================== СЛОВАРЬ ЧИСЕЛ ДЛЯ ТЕКСТА ====================
NUMBERS = {
    0: 'ноль', 1: 'один', 2: 'два', 3: 'три', 4: 'четыре',
    5: 'пять', 6: 'шесть', 7: 'семь', 8: 'восемь', 9: 'девять',
    10: 'десять', 11: 'одиннадцать', 12: 'двенадцать',
    13: 'тринадцать', 14: 'четырнадцать', 15: 'пятнадцать',
    16: 'шестнадцать', 17: 'семнадцать', 18: 'восемнадцать',
    19: 'девятнадцать', 20: 'двадцать', 30: 'тридцать',
    40: 'сорок', 50: 'пятьдесят', 60: 'шестьдесят',
    70: 'семьдесят', 80: 'восемьдесят', 90: 'девяносто',
    100: 'сто', 200: 'двести', 300: 'триста',
    400: 'четыреста', 500: 'пятьсот', 600: 'шестьсот',
    700: 'семьсот', 800: 'восемьсот', 900: 'девятьсот'
}

def number_to_words(n):
    if n in NUMBERS: return NUMBERS[n]
    if 21 <= n <= 99:
        tens = (n // 10) * 10
        ones = n % 10
        if ones == 0: return NUMBERS[tens]
        return NUMBERS[tens] + ' ' + NUMBERS[ones]
    if 101 <= n <= 999:
        hundreds = (n // 100) * 100
        rest = n % 100
        if rest == 0: return NUMBERS[hundreds]
        return NUMBERS[hundreds] + ' ' + number_to_words(rest)
    return str(n)

def time_to_words(hours, minutes):
    if hours == 0: hours_str = 'ноль'
    elif hours in NUMBERS: hours_str = NUMBERS[hours]
    else: hours_str = number_to_words(hours)
    
    if hours == 1 or hours == 21: hour_word = 'час'
    elif 2 <= hours <= 4 or 22 <= hours <= 24: hour_word = 'часа'
    else: hour_word = 'часов'
    
    if minutes == 0:
        return f"Сейчас {hours_str} {hour_word} ровно"
    elif minutes in NUMBERS: minutes_str = NUMBERS[minutes]
    else: minutes_str = number_to_words(minutes)
    
    if minutes % 10 == 1 and minutes % 100 != 11: minute_word = 'минута'
    elif 2 <= minutes % 10 <= 4 and not (12 <= minutes % 100 <= 14): minute_word = 'минуты'
    else: minute_word = 'минут'
    
    return f"Сейчас {hours_str} {hour_word} {minutes_str} {minute_word}"

def convert_text_to_speech(text: str) -> str:
    def replace_number(match):
        try:
            num = int(match.group(0))
            if num > 999999: return match.group(0)
            return number_to_words(num)
        except: return match.group(0)
    
    text = re.sub(r'\b\d+\b', replace_number, text)
    
    def replace_time(match):
        try:
            parts = match.group(0).split(':')
            hours, minutes = int(parts[0]), int(parts[1])
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                return time_to_words(hours, minutes)
        except: pass
        return match.group(0)
    
    text = re.sub(r'\b\d{1,2}:\d{2}\b', replace_time, text)
    text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1 минус \2', text)
    text = re.sub(r'([а-яА-Яa-zA-Z]+)-(\d+)', r'\1 \2', text)
    text = re.sub(r'([а-яА-Яa-zA-Z]+)-([а-яА-Яa-zA-Z]+)', r'\1 \2', text)
    text = re.sub(r'^-+|-+$', '', text)
    text = re.sub(r'--+', ' ', text)
    
    replacements = {
        '°C': ' градусов по Цельсию', '°': ' градусов', '%': ' процентов',
        'км': ' километров', 'кг': ' килограмм', '+': ' плюс ', '=': ' равно ', '№': ' номер ',
    }
    for key, value in replacements.items():
        text = text.replace(key, value)
    
    return re.sub(r'\s+', ' ', text).strip()

# ==================== ОСНОВНАЯ ФУНКЦИЯ ОЗВУЧКИ ====================
def speak(audio):
    audio = convert_text_to_speech(audio)
    print(f"[ПЯТНИЦА] {audio}")
    
    if VOICE_LOADED and model:
        try:
            # Используем приятный русский голос 'baya' вместо роботоподобных старых вариантов
            audio_data = model.apply_tts(
                text=audio,
                speaker='baya',
                sample_rate=48000,
                put_accent=True,
                put_yo=True
            )
            sd.play(audio_data, 48000)
            time.sleep(len(audio_data) / 48000 + 0.1)
            sd.stop()
            print("[TTS] ✅ Silero (Чистый русский)")
            return
        except Exception as e:
            print(f"[TTS] ❌ Silero не сработал: {e}")
    
    if engine_tts:
        try:
            engine_tts.say(audio)
            engine_tts.runAndWait()
            print("[TTS] ✅ pyttsx3 (резерв)")
            return
        except Exception as e:
            print(f"[TTS] ❌ pyttsx3 не сработал: {e}")
    
    print(f"[ОШИБКА TTS] Не удалось озвучить: {audio}")

# ==================== ОПТИМИЗИРОВАННОЕ ПРОСЛУШИВАНИЕ ====================
def listen_continuously():
    r = sr.Recognizer()
    
    # Настройки для мгновенной реакции без ошибок
    r.pause_threshold = 0.6          
    r.non_speaking_duration = 0.5    
    r.phrase_threshold = 0.3         
    
    with sr.Microphone() as source:
        print("🎤 Слушаю...")
        r.adjust_for_ambient_noise(source, duration=0.7)
        
        try:
            audio = r.listen(source, timeout=15, phrase_time_limit=30)
        except sr.WaitTimeoutError:
            return None, False
        except Exception as e:
            print(f"[ОШИБКА МИКРОФОНА] {e}")
            return None, False
        
        try:
            query = r.recognize_google(audio, language="ru-RU")
            print(f"[РАСПОЗНАНО] {query}")
            return query.lower(), True
        except sr.UnknownValueError:
            return None, False
        except sr.RequestError:
            speak("Ошибка соединения с сервисом распознавания.")
            return None, False
        except Exception as e:
            print(f"[ОШИБКА РАСПОЗНАВАНИЯ] {e}")
            return None, False
