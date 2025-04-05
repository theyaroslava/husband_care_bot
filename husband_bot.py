# Бот на aiogram 3 — обновлён под версии 3.7.0+
import asyncio
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

# Укажи свой токен явно здесь, если не используешь переменные окружения
import os
API_TOKEN = os.environ["API_TOKEN"]

NICE_THINGS = [
    "Массаж спины/шеи/плеча",
    "Минет",
    "Домашний завтрак",
    "Сказать: «Я так тобой горжусь»",
    "Выложить рилс, который будет говорить о том, какой он молодец",
    "Сделать неожиданный комплимент про его силу, ум или лидерство"
]

user_tasks = {}
user_stats = {}

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

def generate_task_keyboard(tasks):
    buttons = [
        [InlineKeyboardButton(text=f"✅ {task}", callback_data=f"done:{task}")]
        for task in tasks
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def pick_daily_tasks():
    return random.sample(NICE_THINGS, 3)

@dp.message(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет, красотка! Готова делать приятности мужу? 💖")

@dp.message(commands=["стата"])
async def send_stats(message: types.Message):
    user_id = message.from_user.id
    stats = user_stats.get(user_id, {})
    if not stats:
        await message.answer("Пока нет статистики, начинай творить добро! 🫶")
        return

    total = sum(stats.values())
    text = f"<b>Твоя статистика за всё время:</b>\n\nВсего выполнено: <b>{total}</b>\n\n"
    for task, count in stats.items():
        text += f"{task} — <b>{count}</b> раз(а)\n"

    await message.answer(text)

@dp.callback_query(lambda c: c.data.startswith("done:"))
async def mark_done(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    task = callback.data.split(":", 1)[1]
    today = datetime.now().date().isoformat()
    data = user_tasks.get(user_id, {})
    if data.get("date") != today:
        return await callback.answer("Это задание не на сегодня!", show_alert=True)
    if task in data.get("done", []):
        return await callback.answer("Уже отмечено 😊")
    data.setdefault("done", []).append(task)

    user_stats.setdefault(user_id, {}).setdefault(task, 0)
    user_stats[user_id][task] += 1

    await callback.answer(f"Отмечено: {task} 💖")

async def scheduler():
    while True:
        now = datetime.now()
        for hour in [8, 11, 14, 17, 20, 22]:
            run_at = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if now > run_at:
                run_at += timedelta(days=1)
            await asyncio.sleep((run_at - datetime.now()).total_seconds())
            await send_daily_updates(hour)

async def send_daily_updates(hour):
    for user_id in user_tasks.keys():
        data = user_tasks[user_id]
        if hour == 8:
            tasks = pick_daily_tasks()
            user_tasks[user_id] = {
                "date": datetime.now().date().isoformat(),
                "tasks": tasks,
                "done": []
            }
            await bot.send_message(
                user_id,
                f"🌞 Доброе утро, красотка! Вот чем можно порадовать мужа сегодня:\n\n" +
                "\n".join([f"{i+1}. {task}" for i, task in enumerate(tasks)]),
                reply_markup=generate_task_keyboard(tasks)
            )
        elif hour in [11, 14, 17, 20]:
            done = data.get("done", [])
            remaining = [t for t in data.get("tasks", []) if t not in done]
            text = f"⏳ Статус дня:\n✅ Сделано:\n"
            text += ("\n".join([f"• {d}" for d in done]) if done else "• Пока ничего")
            text += "\n\n❗ Осталось:\n"
            text += ("\n".join([f"• {r}" for r in remaining]) if remaining else "• Всё сделано! 💕")
            await bot.send_message(user_id, text)
        elif hour == 22:
            done = data.get("done", [])
            remaining = [t for t in data.get("tasks", []) if t not in done]
            text = f"🌙 День подошёл к концу...\n\n"
            text += "✅ Ты сделала:\n" + ("\n".join([f"• {d}" for d in done]) if done else "• Пока ничего") + "\n\n"
            text += "❌ Не успела:\n" + ("\n".join([f"• {r}" for r in remaining]) if remaining else "• Всё успела!") + "\n\n"
            text += "Ты просто чудо. Завтра новый день — и ты снова разорвёшь! 💖"
            await bot.send_message(user_id, text)

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
