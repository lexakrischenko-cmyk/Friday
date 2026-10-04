import os
import glob
import datetime
import subprocess
import random
import webbrowser as wb
import pyautogui
import wikipedia
import asyncio
import requests
import json
import threading
import time
import speech_recognition as sr
from telethon import TelegramClient
from config import VIVALDI_PATH, API_ID, API_HASH, CONTACT_ALIASES
import pygetwindow as gw

# ==================== TELEGRAM ====================
async def send_telegram_message_async(contact_name, message_text):
    try:
        client = TelegramClient('session', API_ID, API_HASH)
        await client.start()
        real_name = contact_name
        contact_name_lower = contact_name.lower()
        if contact_name_lower in CONTACT_ALIASES:
            real_name = CONTACT_ALIASES[contact_name_lower]
        entity = None
        if real_name.startswith('@'):
            try:
                entity = await client.get_entity(real_name)
            except:
                pass
        if not entity:
            async for dialog in client.iter_dialogs():
                if dialog.name and real_name.lower() in dialog.name.lower():
                    entity = dialog.entity
                    break
        if entity:
            await client.send_message(entity, message_text)
            await client.disconnect()
            return True, real_name
        else:
            await client.disconnect()
            return False, real_name
    except Exception as e:
        print(f"[TELEGRAM] Ошибка: {e}")
        return False, contact_name

def send_telegram_message(contact_name, message_text):
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, name = loop.run_until_complete(
            send_telegram_message_async(contact_name, message_text)
        )
        loop.close()
        return success, name
    except Exception as e:
        print(f"[TELEGRAM] Ошибка: {e}")
        return False, contact_name

async def send_telegram_voice_async(contact_name, audio_path):
    try:
        client = TelegramClient('session', API_ID, API_HASH)
        await client.start()
        entity = None
        if contact_name.startswith('@'):
            try:
                entity = await client.get_entity(contact_name)
            except:
                pass
        if not entity:
            async for dialog in client.iter_dialogs():
                if dialog.name and contact_name.lower() in dialog.name.lower():
                    entity = dialog.entity
                    break
        if entity:
            await client.send_file(entity, audio_path, voice_note=True)
            await client.disconnect()
            return True
        else:
            await client.disconnect()
            return False
    except Exception as e:
        print(f"[TELEGRAM VOICE] Ошибка асинхронной отправки: {e}")
        return False

def send_telegram_voice(contact_name: str) -> str:
    """
    Записывает голосовое сообщение до первой паузы,
    конвертирует его через FFmpeg в формат OGG (Opus)
    и отправляет контакту в Telegram как настоящее голосовое.
    """
    WAV_FILENAME = "temp_voice.wav"
    OGG_FILENAME = "telegram_voice_msg.ogg"
    r = sr.Recognizer()
    
    r.pause_threshold = 0.8          
    r.non_speaking_duration = 0.6    
    r.phrase_threshold = 0.3         
    
    try:
        print("[ГОЛОСОВОЕ] Микрофон включен. Записываю речь...")
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = r.listen(source, timeout=10, phrase_time_limit=None)
            
        print("[ГОЛОСОВОЕ] Пауза обнаружена. Сохраняю временный файл...")
        with open(WAV_FILENAME, "wb") as f:
            f.write(audio_data.get_wav_data())
            
        print("[ГОЛОСОВОЕ] Конвертирую в формат голосового сообщения Telegram...")
        # Используем FFmpeg для принудительного кодирования в ogg/opus (стандарт Telegram)
        # Отключаем логирование ffmpeg (-y -loglevel quiet) для чистоты консоли Пятницы
        os.system(f'ffmpeg -y -i "{WAV_FILENAME}" -c:a libopus -b:a 32k -loglevel quiet "{OGG_FILENAME}"')
        
        print("[ГОЛОСОВОЕ] Файл готов. Начинаю отправку в Telegram...")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(send_telegram_voice_async(contact_name, OGG_FILENAME))
        loop.close()
        
        # Очищаем за собой оба временных файла
        if os.path.exists(WAV_FILENAME):
            os.remove(WAV_FILENAME)
        if os.path.exists(OGG_FILENAME):
            os.remove(OGG_FILENAME)
            
        if success:
            return f"Голосовое сообщение для {contact_name} отправлено."
        else:
            return f"Не удалось найти контакт {contact_name} для отправки голосового."
        
    except sr.WaitTimeoutError:
        return "Запись отменена, так как вы ничего не сказали."
    except Exception as e:
        # Чистим файлы в случае любой непредвиденной ошибки
        for file in [WAV_FILENAME, OGG_FILENAME]:
            if os.path.exists(file):
                os.remove(file)
        print(f"[ГОЛОСОВОЕ] Ошибка: {e}")
        return f"Не удалось отправить голосовое сообщение: {str(e)[:50]}"

# ==================== ПРИЛОЖЕНИЯ ====================
def open_application(app_name):
    app_name = app_name.lower().strip()
    sites = {
        "ютуб": "https://youtube.com", "youtube": "https://youtube.com",
        "вк": "https://vk.com", "гугл": "https://google.com",
        "google": "https://google.com", "почта": "https://gmail.com",
        "gmail": "https://gmail.com", "ватсап": "https://whatsapp.com",
        "whatsapp": "https://whatsapp.com", "телеграм": "https://telegram.org",
        "telegram": "https://telegram.org", "кинопоиск": "https://kinopoisk.ru",
        "ivi": "https://ivi.ru", "rutube": "https://rutube.ru"
    }
    for key, url in sites.items():
        if key in app_name:
            os.system(f'start "" "{VIVALDI_PATH}" "{url}"')
            return f"Открываю {key}"
    apps = {
        "блокнот": "notepad.exe", "калькулятор": "calc.exe", "проводник": "explorer.exe",
        "браузер": VIVALDI_PATH, "эксель": "start excel.exe", "excel": "start excel.exe",
        "ворд": "start winword.exe", "word": "start winword.exe", "паинт": "mspaint.exe", "paint": "mspaint.exe",
    }
    for key, cmd in apps.items():
        if key in app_name:
            if key == "браузер":
                os.system(f'start "" "{cmd}"')
            else:
                os.system(cmd)
            return f"Открываю {key}"
    if "дискорд" in app_name or "discord" in app_name:
        try:
            discord_exe = os.path.expanduser("~\\AppData\\Local\\Discord\\app-*\\Discord.exe")
            files = glob.glob(discord_exe)
            if files:
                subprocess.Popen([files[0]])
                return "Открываю Дискорд"
        except:
            pass
    if "стим" in app_name or "steam" in app_name:
        os.system("start steam://open")
        return "Открываю Стим"
    if "танки" in app_name or "tanki" in app_name:
        try:
            tanki_path = r"C:\Games\Tanki"
            if os.path.exists(tanki_path):
                files = os.listdir(tanki_path)
                exe_files = [f for f in files if f.lower().endswith('.exe')]
                if exe_files:
                    os.startfile(os.path.join(tanki_path, exe_files[0]))
                    return "Открываю Танки"
        except:
            pass
    if "спотифай" in app_name or "spotify" in app_name:
        os.system("start spotify.exe")
        return "Открываю Споттифай"
    return f"Не знаю приложение {app_name}"

# ==================== МУЗЫКА ====================
def play_music(track=""):
    if track and len(track) > 2:
        search_url = f"https://yandex.ru{track.replace(' ', '+')}"
        os.system(f'start "" "{VIVALDI_PATH}" "{search_url}"')
        return f"Ищу {track}"
    else:
        os.system(f'start "" "{VIVALDI_PATH}" "https://yandex.ru"')
        return "Включаю Мою волну"
# ==================== УПРАВЛЕНИЕ ВИДЕО В БРАУЗЕРЕ ====================
def video_play_pause():
    pyautogui.press('playpause')
    return "Пауза"

def video_play():
    pyautogui.press('playpause')
    return "Продолжаю"

def video_pause():
    pyautogui.press('playpause')
    return "Пауза"

def video_forward(seconds=10):
    presses = max(1, seconds // 5)
    pyautogui.press('right', presses=presses)
    return f"Перемотал вперёд на {seconds} секунд"

def video_rewind(seconds=10):
    presses = max(1, seconds // 5)
    pyautogui.press('left', presses=presses)
    return f"Перемотал назад на {seconds} секунд"

def video_fullscreen():
    pyautogui.press('f')
    return "Включил полноэкранный режим"

def video_exit_fullscreen():
    pyautogui.press('esc')
    return "Вышел из полноэкранного режима"

def video_volume_up():
    pyautogui.press('volumeup', presses=5)
    return "Громче"

def video_volume_down():
    pyautogui.press('volumedown', presses=5)
    return "Тише"

def video_mute():
    pyautogui.press('volumemute')
    return "Звук выключен"

def video_speed_up():
    pyautogui.hotkey('shift', '.')
    return "Увеличил скорость"

def video_speed_down():
    pyautogui.hotkey('shift', ',')
    return "Уменьшил скорость"

def video_subtitles():
    pyautogui.press('c')
    return "Переключил субтитры"

# ==================== ВРЕМЯ И ДАТА ====================
def get_time():
    now = datetime.datetime.now()
    from voice import time_to_words
    return time_to_words(now.hour, now.minute)

def get_date():
    now = datetime.datetime.now()
    months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
              'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
    from voice import number_to_words
    return f"Сегодня {number_to_words(now.day)} {months[now.month-1]} {number_to_words(now.year)} года"

# ==================== ВИКИПЕДИЯ ====================
def search_wikipedia(query):
    try:
        wikipedia.set_lang("ru")
        result = wikipedia.summary(query, sentences=2)
        return result
    except:
        return "Не удалось найти информацию."

# ==================== СКРИНШОТ ====================
def take_screenshot():
    try:
        img = pyautogui.screenshot()
        img_path = os.path.expanduser(
            "~\\Pictures\\screenshot_" + 
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        )
        img.save(img_path)
        return f"Скриншот сохранён в {img_path}"
    except:
        return "Не удалось сделать скриншот"
# ==================== ШУТКИ ====================
def tell_joke():
    jokes = [
        "Почему программисты не ходят в спортзал? Потому что они предпочитают работать с багами, а не с мышцами!",
        "Что сказал один компьютер другому? Не смотри на меня, я тоже не понял этот код!",
        "Как отличить экстраверта-программиста от интроверта? Экстраверт смотрит на твои ботинки, когда говорит с тобой.",
        "Что такое 404? Это когда ты ищешь свою мотивацию на работе.",
        "Почему хакеры не играют в прятки? Потому что они всегда находят уязвимости!"
    ]
    return random.choice(jokes)

# ==================== ГРОМКОСТЬ ====================
def control_volume(direction):
    if direction == "громче":
        pyautogui.press('volumeup', presses=5)
        return "Громче"
    elif direction == "тише":
        pyautogui.press('volumedown', presses=5)
        return "Тише"
    elif direction == "выключить звук":
        pyautogui.press('volumemute')
        return "Звук выключен"
    return "Неизвестная команда"

# ==================== СИСТЕМА ====================
def system_control(action):
    if action == "выключить":
        os.system("shutdown /s /f /t 3")
        return "Выключаю компьютер"
    elif action == "перезагрузить":
        os.system("shutdown /r /f /t 3")
        return "Перезагружаю компьютер"
    elif action == "заблокировать":
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Блокирую компьютер"
    return "Неизвестное действие"

# ==================== ПОГОДА ====================
def get_weather(city="Минск"):
    try:
        url = f"https://wttr.in{city}?format=%C+%t&lang=ru"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return f"В {city} сейчас {response.text}"
        else:
            return "Не удалось узнать погоду."
    except:
        return "Ошибка соединения с сервисом погоды."

# ==================== НАПОМИНАНИЯ И ЗАМЕТКИ ====================
REMINDERS_FILE = "reminders.json"

def load_reminders():
    try:
        with open(REMINDERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_reminders(reminders):
    with open(REMINDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)

def add_reminder(text: str, time_str: str = None):
    reminders = load_reminders()
    reminder = {
        "text": text,
        "created": datetime.datetime.now().isoformat(),
        "done": False
    }
    if time_str:
        parsed_time = parse_time(time_str)
        if parsed_time:
            reminder["time"] = parsed_time.isoformat()
            schedule_reminder(reminder)
        else:
            return f"Не поняла время. Скажи, например: 'завтра в 10 утра' или 'через 5 минут'."
    reminders.append(reminder)
    save_reminders(reminders)
    return f"✅ Запомнила: {text}" + (f" (напомню {time_str})" if time_str else "")

def parse_time(time_str: str):
    time_str = time_str.lower().strip()
    now = datetime.datetime.now()
    time_mappings = {
        "сейчас": 0, "через минуту": 1, "через 5 минут": 5, "через 10 минут": 10,
        "через 15 минут": 15, "через полчаса": 30, "через час": 60, "через 2 часа": 120,
    }
    for phrase, minutes in time_mappings.items():
        if phrase in time_str:
            return now + datetime.timedelta(minutes=minutes)
    import re
    match = re.search(r'через\s+(\d+)\s*(минут|час|часа|часов|мин|ч)', time_str)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if 'час' in unit or 'ч' == unit:
            num *= 60
        return now + datetime.timedelta(minutes=num)
    match = re.search(r'в\s+(\d{1,2})[:.](\d{2})', time_str)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        target = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        if target < now:
            target = target + datetime.timedelta(days=1)
        return target
    match = re.search(r'(сегодня|завтра|послезавтра)\s+в\s+(\d{1,2})\s*(утра|дня|вечера|ночи)?', time_str)
    if match:
        day_offset = 0
        day_word = match.group(1)
        if day_word == "завтра":
            day_offset = 1
        elif day_word == "послезавтра":
            day_offset = 2
        hours = int(match.group(2))
        if "вечера" in time_str and hours < 12:
            hours += 12
        elif "ночи" in time_str and hours < 12:
            hours += 12
        elif "дня" in time_str and hours < 12:
            hours += 12
        target = now.replace(hour=hours, minute=0, second=0, microsecond=0) + datetime.timedelta(days=day_offset)
        if target < now:
            target = target + datetime.timedelta(days=1)
        return target
    return None

def schedule_reminder(reminder):
    if "time" not in reminder:
        return
    target_time = datetime.datetime.fromisoformat(reminder["time"])
    def check_reminder():
        while True:
            now = datetime.datetime.now()
            if now >= target_time:
                from voice import speak
                speak(f"🔔 Напоминание: {reminder['text']}")
                reminders = load_reminders()
                for r in reminders:
                    if r.get("time") == reminder["time"] and r["text"] == reminder["text"]:
                        r["done"] = True
                        break
                save_reminders(reminders)
                break
            time.sleep(30)
    thread = threading.Thread(target=check_reminder, daemon=True)
    thread.start()

def get_reminders():
    reminders = load_reminders()
    active = [r for r in reminders if not r.get("done", False)]
    if not active:
        return "У тебя нет активных напоминаний."
    result = "📋 Твои напоминания:\n"
    for i, r in enumerate(active, 1):
        text = r["text"]
        if "time" in r:
            time_str = datetime.datetime.fromisoformat(r["time"]).strftime("%d.%m %H:%M")
            result += f"{i}. {text} (напомнить {time_str})\n"
        else:
            result += f"{i}. {text}\n"
    return result

def clear_reminders():
    reminders = load_reminders()
    active = [r for r in reminders if not r.get("done", False)]
    save_reminders(active)
    return "🗑️ Все выполненные напоминания удалены."

# ==================== УПРАВЛЕНИЕ DISCORD ====================
def focus_discord():
    try:
        windows = gw.getWindowsWithTitle('Discord')
        if windows:
            win = windows[0]
            if win.isMinimized:
                win.restore()
            win.activate()
            time.sleep(0.3)
            return True
        else:
            return False
    except Exception as e:
        print(f"[DISCORD] Не удалось найти окно: {e}")
        return False

def discord_toggle_mute():
    if not focus_discord():
        return "Не удалось найти окно Discord. Убедись, что он открыт."
    try:
        pyautogui.hotkey('ctrl', 'shift', 'm')
        return "Переключила микрофон в Discord"
    except Exception as e:
        return f"Не удалось переключить микрофон: {e}"

def discord_toggle_deafen():
    if not focus_discord():
        return "Не удалось найти окно Discord. Убедись, что он открыт."
    try:
        pyautogui.hotkey('ctrl', 'shift', 'd')
        return "Переключила звук в Discord"
    except Exception as e:
        return f"Не удалось переключить звук: {e}"

def discord_mute_all():
    if not focus_discord():
        return "Не удалось найти окно Discord. Убедись, что он открыт."
    try:
        pyautogui.hotkey('ctrl', 'shift', 'd')
        return "Отключила микрофон и звук в Discord"
    except Exception as e:
        return f"Не удалось отключить: {e}"

def discord_unmute_all():
    if not focus_discord():
        return "Не удалось найти окно Discord. Убедись, что он открыт."
    try:
        pyautogui.hotkey('ctrl', 'shift', 'd')
        return "Включила микрофон и звук в Discord"
    except Exception as e:
        return f"Не удалось включить: {e}"
# ==================== ПОИСК В ИНТЕРНЕТЕ ====================
def search_web(query: str, engine="google"):
    """
    Выполняет поисковый запрос в браузере Vivaldi.
    """
    engines = {
        "google": f"https://google.com{query.replace(' ', '+')}",
        "yandex": f"https://yandex.ru{query.replace(' ', '+')}",
        "youtube": f"https://youtube.com{query.replace(' ', '+')}",
        "wikipedia": f"https://wikipedia.org{query.replace(' ', '_')}",
        "kinopoisk": f"https://kinopoisk.ru{query.replace(' ', '+')}"
    }
    url = engines.get(engine, engines["google"])
    os.system(f'start "" "{VIVALDI_PATH}" "{url}"')
    return f"Ищу {query} в {engine}"
