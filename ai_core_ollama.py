import json
import ollama
import re
from config import MAX_HISTORY

# Загружаем описание инструментов
with open('tools.json', 'r', encoding='utf-8') as f:
    TOOLS = json.load(f)

class AICore:
    def __init__(self):
        self.history = []
        self.model = "qwen2.5:7b-instruct"
        
        # Формируем список функций для промпта
        func_list = []
        for tool in TOOLS:
            func = tool['function']
            func_list.append(f"{func['name']}: {func['description']}")
        
        self.functions_text = "\n".join(func_list)
        
        self.system_prompt = f"""Ты — Пятница, голосовой помощник для ПК.

Ты общаешься с пользователем как живой человек.

ОСНОВНЫЕ ПРАВИЛА:
1. На обычные вопросы (как дела, что нового, кто ты и т.д.) — ОТВЕЧАЙ КАК ЧЕЛОВЕК, кратко и дружелюбно
2. Если пользователь просит ЧТО-ТО СДЕЛАТЬ (открыть, найти, включить, перемотать) — используй функции
3. НЕ РАССУЖДАЙ ВСЛУХ о функциях — просто вызывай их или отвечай
4. Если пользователь говорит «Старому» или «Старый», это псевдоним конкретного контакта, а НЕ папа! Передавай в аргумент contact значение "Старый".

Доступные функции:
{self.functions_text}

ФОРМАТ ОТВЕТА:
- Для выполнения действия: {{"action": "имя_функции", "arguments": {{"параметр": "значение"}}}}
- Для обычного ответа: {{"reply": "текст ответа"}}

Примеры:
{{"reply": "Привет! У меня всё отлично, а как твои дела?"}}
{{"action": "open_application", "arguments": {{"app_name": "ютуб"}}}}
{{"action": "get_time", "arguments": {{}}}}

ВАЖНО: Никогда не объясняй, какую функцию ты выбрал. Просто выполняй действие или отвечай.
ОТВЕЧАЙ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ.
"""
    
    def ask(self, user_input: str) -> dict:
        """Отправляет запрос в Ollama и возвращает результат"""
        
        # Проверяем, не хочет ли пользователь выйти
        if any(word in user_input.lower() for word in ["пока", "до свидания", "заверши работу", "выйти", "прощай"]):
            return {"type": "exit", "content": "До свидания! Буду ждать."}
        
        # Добавляем в историю
        self.history.append({"role": "user", "content": user_input})
        if len(self.history) > 20:
            self.history = self.history[-20:]
        
        # Формируем сообщения
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.history
        
        try:
            # Отправляем запрос в Ollama
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "num_ctx": 2048,
                    "temperature": 0.4  # Немного творчества для живых ответов
                },
                stream=False
            )
            
            content = response.get('message', {}).get('content', '').strip()
            print(f"[AI] Ответ: {content[:150]}...")
            
            # Сохраняем в историю
            self.history.append({"role": "assistant", "content": content})
            
            # Парсим JSON-ответ
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    
                    if "action" in data:
                        return {
                            "type": "function",
                            "name": data["action"],
                            "arguments": data.get("arguments", {})
                        }
                    elif "reply" in data:
                        return {"type": "reply", "content": data["reply"]}
                    else:
                        # Если JSON есть, но без reply/action — используем весь текст
                        return {"type": "reply", "content": content}
                except:
                    return {"type": "reply", "content": content}
            else:
                # Если JSON не найден — это обычный ответ
                return {"type": "reply", "content": content}
            
        except Exception as e:
            print(f"[AI] Ошибка: {e}")
            return {"type": "reply", "content": f"Ошибка: {str(e)[:100]}"}
    
    def clear_history(self):
        """Очищает историю диалога"""
        self.history = []