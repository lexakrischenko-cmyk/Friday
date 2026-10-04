import os
import time
import re
from voice import speak, listen_continuously
from ai_core_ollama import AICore
# Импортируем ваши псевдонимы прямо из файла конфигурации
from config import CONTACT_ALIASES, MAX_HISTORY
from functions import (
    send_telegram_message, send_telegram_voice, open_application, play_music,
    video_play_pause, video_play, video_pause, video_forward, video_rewind,
    video_fullscreen, video_exit_fullscreen,
    video_volume_up, video_volume_down, video_mute,
    video_speed_up, video_speed_down, video_subtitles,
    search_web,
    get_time, get_date, search_wikipedia, take_screenshot,
    tell_joke, control_volume, system_control, get_weather,
    add_reminder, get_reminders, clear_reminders,
    discord_toggle_mute, discord_toggle_deafen,
    discord_mute_all, discord_unmute_all
)

# Разворачиваем сгруппированные псевдонимы из config.py в плоскую базу
EXTENDED_CONTACTS = {}
for aliases, real_name in CONTACT_ALIASES.items():
    if isinstance(aliases, (list, tuple)):
        for alias in aliases:
            if isinstance(alias, str):
                EXTENDED_CONTACTS[alias.lower().strip()] = real_name
    elif isinstance(aliases, str):
        EXTENDED_CONTACTS[aliases.lower().strip()] = real_name

def get_real_name_and_contact(text: str):
    """Сканирует текст запроса, находит псевдоним и возвращает реальное имя"""
    words = re.findall(r'[а-яА-Яa-zA-Z0-9❤️]+', text.lower())
    for word in words:
        if word in EXTENDED_CONTACTS:
            real_name = EXTENDED_CONTACTS[word]
            return real_name
    return None

class FunctionDispatcher:
    @staticmethod
    def execute(function_name: str, arguments: dict) -> str:
        if function_name == "send_telegram_message":
            contact = arguments.get("contact") or arguments.get("chat_id") or ""
            message = arguments.get("message") or arguments.get("text") or ""
            
            if contact.lower() in EXTENDED_CONTACTS:
                contact = EXTENDED_CONTACTS[contact.lower()]
            
            success, name = send_telegram_message(contact, message)
            display_name = name if name else (contact if contact else "контакта")
            if success:
                return f"Сообщение для {display_name} отправлено"
            else:
                return f"Не удалось отправить сообщение для {display_name}"
                
        elif function_name == "send_telegram_voice":
            contact = arguments.get("contact_name") or arguments.get("contact") or ""
            if contact.lower() in EXTENDED_CONTACTS:
                contact = EXTENDED_CONTACTS[contact.lower()]
            return send_telegram_voice(contact)
                
        elif function_name == "open_application":
            return open_application(arguments.get("app_name", ""))
        elif function_name == "play_music":
            return play_music(arguments.get("track", ""))
        
        # ============ УПРАВЛЕНИЕ ВИДЕО ============
        elif function_name == "video_play_pause":
            return video_play_pause()
        elif function_name == "video_play":
            return video_play()
        elif function_name == "video_pause":
            return video_pause()
        elif function_name == "video_forward":
            return video_forward(arguments.get("seconds", 10))
        elif function_name == "video_rewind":
            return video_rewind(arguments.get("seconds", 10))
        elif function_name == "video_fullscreen":
            return video_fullscreen()
        elif function_name == "video_exit_fullscreen":
            return video_exit_fullscreen()
        elif function_name == "video_volume_up":
            return video_volume_up()
        elif function_name == "video_volume_down":
            return video_volume_down()
        elif function_name == "video_mute":
            return video_mute()
        elif function_name == "video_speed_up":
            return video_speed_up()
        elif function_name == "video_speed_down":
            return video_speed_down()
        elif function_name == "video_subtitles":
            return video_subtitles()
        
        # ============ ПОИСК В ИНТЕРНЕТЕ ============
        elif function_name == "search_web":
            return search_web(arguments.get("query", ""), arguments.get("engine", "google"))
        
        # ============ НАПОМИНАНИЯ ============
        elif function_name == "add_reminder":
            return add_reminder(arguments.get("text", ""), arguments.get("time_str", None))
        elif function_name == "get_reminders":
            return get_reminders()
        elif function_name == "clear_reminders":
            return clear_reminders()
        
        # ============ УПРАВЛЕНИЕ DISCORD ============
        elif function_name == "discord_toggle_mute":
            return discord_toggle_mute()
        elif function_name == "discord_toggle_deafen":
            return discord_toggle_deafen()
        elif function_name == "discord_mute_all":
            return discord_mute_all()
        elif function_name == "discord_unmute_all":
            return discord_unmute_all()
        
        # ============ ОСТАЛЬНЫЕ ФУНКЦИИ ============
        elif function_name == "get_time":
            return get_time()
        elif function_name == "get_date":
            return get_date()
        elif function_name == "search_wikipedia":
            return search_wikipedia(arguments.get("query", ""))
        elif function_name == "take_screenshot":
            return take_screenshot()
        elif function_name == "tell_joke":
            return tell_joke()
        elif function_name == "control_volume":
            return control_volume(arguments.get("direction", ""))
        elif function_name == "system_control":
            return system_control(arguments.get("action", ""))
        elif function_name == "get_weather":
            return get_weather(arguments.get("city", "Минск"))
        else:
            return f"Неизвестная функция: {function_name}"

def main():
    speak("С возвращением.")
    
    ai = AICore()
    listening = True
    running = True
    
    print("🎤 Ассистент запущен и слушает...")
    
    while running:
        if not listening:
            try:
                command, voice_ok = listen_continuously(silent=True)
            except TypeError:
                command, voice_ok = listen_continuously()
                
            if not voice_ok or not command:
                continue
            
            if any(word in command for word in ["можешь слушать", "включайся", "слушай", "продолжай слушать", "ты здесь?"]):
                listening = True
                speak("Слушаю.")
                print("🔊 Прослушивание включено")
                continue
            else:
                continue
        
        command, voice_ok = listen_continuously()
        
        if not voice_ok or not command:
            continue
        
        if any(word in command for word in ["не подслушивай", "хватит слушать", "заткнись", "не слушай", "отключись"]):
            listening = False
            speak("Молчу.")
            print("🔇 Прослушивание выключено")
            continue
        
        if any(word in command for word in ["замолкни", "хватит", "выключись", "до свидания", "пока"]):
            speak("До свидания! Буду ждать.")
            running = False
            break
        
        if any(word in command for word in ["перезагрузи", "перезапусти", "обнови", "рестарт"]):
            speak("Перезагружаюсь...")
            time.sleep(0.5)
            print("🔄 Пятница перезагружена!")
            speak("Готова к работе!")
            ai.clear_history()
            continue
            
        # УМНЫЙ ПЕРЕХВАТ ДЛЯ TELEGRAM (ОБЫЧНЫЕ ТЕКСТОВЫЕ СООБЩЕНИЯ)
        if any(trigger in command for trigger in ["сообщение", "телеграм", "напиши"]) and not any(v_trig in command for v_trig in ["голосовое", "звуковое"]):
            target_contact = get_real_name_and_contact(command)
            
            if target_contact:
                clean_voice_name = re.sub(r'[^\w\s]', '', target_contact).strip()
                print(f"📝 Режим диктовки для: {target_contact}")
                speak(f"Хорошо, слушаю сообщение для {clean_voice_name}")
            else:
                print("📝 Режим диктовки сообщения. Получатель не определен заранее...")
                speak("Слушаю текст сообщения...")
            
            message_text, msg_ok = listen_continuously() 
            if msg_ok and message_text:
                if target_contact:
                    command = f"отправь сообщение в телеграм контакту {target_contact} с текстом {message_text}"
                else:
                    command = f"{command} {message_text}"

        # УМНЫЙ ПЕРЕХВАТ ДЛЯ ГОЛОСОВЫХ СООБЩЕНИЙ
        elif any(v_trig in command for v_trig in ["голосовое", "звуковое"]):
            target_contact = get_real_name_and_contact(command)
            if target_contact:
                clean_voice_name = re.sub(r'[^\w\s]', '', target_contact).strip()
                speak(f"Записываю голосовое для {clean_voice_name}. Наговаривайте.")
                response = send_telegram_voice(target_contact)
                if response:
                    speak(response)
                continue
        
        result = ai.ask(command)
        
        if result["type"] == "function":
            if result["name"] == "send_message":
                result["name"] = "send_telegram_message"
                
            speak("Выполняю...")
            response = FunctionDispatcher.execute(result["name"], result["arguments"])
            if response:
                speak(response)
        elif result["type"] == "reply":
            sentences = re.split(r'(?<=[.!?])\s+', result["content"])
            for sentence in sentences:
                if sentence.strip():
                    speak(sentence.strip())
        elif result["type"] == "exit":
            speak(result["content"])
            running = False
            break

if __name__ == "__main__":
    main()
