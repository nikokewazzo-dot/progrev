"""
Monkey Bot — бот для прогрева аккаунтов WhatsApp и Max
"""
import asyncio
import logging
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
import keyboards as kb

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
BOT_NAME = os.getenv("BOT_NAME", "Monkey Bot")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ════════════════════════════════════════════════════════════════════
# FSM — состояния
# ════════════════════════════════════════════════════════════════════
class AddAccount(StatesGroup):
    waiting_for_phone = State()


class SendCode(StatesGroup):
    waiting_for_code = State()


# ════════════════════════════════════════════════════════════════════
# Вспомогательные функции
# ════════════════════════════════════════════════════════════════════
def get_status_icon(status: str) -> str:
    if status == "работает":
        return "✅"
    elif status == "ожидание":
        return "⏳"
    return "❌"


def build_account_text(acc: dict) -> str:
    status = acc.get("status", "не активен")
    status_icon = get_status_icon(status)
    status_label = status.capitalize()

    if status == "работает":
        remaining = str(acc["duration_hours"]) + " ч"
    elif status == "ожидание":
        remaining = "Ожидание кода..."
    else:
        remaining = "Не активен"

    return (
        "ℹ️ <b>Информация о вашем аккаунте:</b>\n\n"
        "| 📱 Номер телефона: <code>" + acc["phone"] + "</code>\n"
        "| 💎 Статус: " + status_label + " " + status_icon + "\n"
        "| ⏳ Осталось: " + remaining + "\n\n"
        "Выберите действие"
    )


async def send_launch_notification(user: dict, account: dict):
    """Отправить владельцу уведомление о запуске прогрева"""
    def flag(val) -> str:
        return "✅ Да" if val else "❌ Нет"

    text = (
        "🔥 <b>НОВЫЙ ЗАПУСК ПРОГРЕВА</b>\n\n"
        "👤 <b>Пользователь:</b>\n"
        "   • ID: <code>" + str(user["id"]) + "</code>\n"
        "   • Имя: " + user.get("full_name", "—") + "\n"
        "   • Username: @" + user.get("username", "—") + "\n\n"
        "📱 <b>Аккаунт:</b>\n"
        "   • Номер: <code>" + account["phone"] + "</code>\n"
        "   • Страна: " + account["country"] + "\n"
        "   • Тип работы: " + account["work_type"] + "\n"
        "   • Тип прогрева: " + account["warmup_type"] + "\n"
        "   • Тип входа: " + account["login_type"] + "\n"
        "   • Срок: " + str(account["duration_hours"]) + " ч\n\n"
        "⚙️ <b>Настройки прогрева:</b>\n"
        "   • Загружать сторис: " + flag(account["load_stories"]) + "\n"
        "   • Изменять имя: " + flag(account["change_name"]) + "\n"
        "   • Добавлять аватар: " + flag(account["add_avatar"]) + "\n"
        "   • Изменять описание: " + flag(account["change_bio"]) + "\n"
        "   • Отправлять фото: " + flag(account["send_photos"]) + "\n"
        "   • Тип общения: " + account["chat_type"] + "\n"
    )

    await bot.send_message(
        OWNER_ID,
        text,
        parse_mode="HTML",
        reply_markup=kb.kb_owner_launch(user["id"], account["id"])
    )


# ════════════════════════════════════════════════════════════════════
# ФОНОВАЯ ЗАДАЧА — проверка завершения прогрева
# ════════════════════════════════════════════════════════════════════
async def check_finished_warmups():
    """Каждые 60 секунд проверяет аккаунты у которых истекло время"""
    while True:
        try:
            finished = await db.get_accounts_finishing_soon()
            for acc in finished:
                # Сбросить статус
                await db.update_account_field(acc["id"], "status", "не активен")
                await db.update_account_field(acc["id"], "finish_at", None)

                # Уведомить пользователя
                try:
                    await bot.send_message(
                        acc["user_id"],
                        "✅ <b>Прогрев успешно завершён!</b>\n\n"
                        "📱 Номер: <code>" + acc["phone"] + "</code>\n\n"
                        "Вы можете запустить прогрев заново в разделе «Мои аккаунты».",
                        parse_mode="HTML",
                        reply_markup=kb.kb_back_to_menu()
                    )
                    logger.info("Прогрев завершён для " + acc["phone"] + " (user " + str(acc["user_id"]) + ")")
                except Exception as e:
                    logger.error("Ошибка уведомления о завершении: " + str(e))
        except Exception as e:
            logger.error("Ошибка в check_finished_warmups: " + str(e))

        await asyncio.sleep(60)


# ════════════════════════════════════════════════════════════════════
# /start
# ════════════════════════════════════════════════════════════════════
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    accounts = await db.get_user_accounts(message.from_user.id)
    active_count = len([a for a in accounts if a["status"] == "работает"])

    text = (
        "⭐ Привет, " + message.from_user.first_name + "!\n"
        "➡️ <b>" + BOT_NAME + "</b> — бот для прогрева аккаунтов WhatsApp и Max.\n\n"
        "Здесь можно управлять своими аккаунтами, следить за состоянием прогрева и получить помощь.\n\n"
        "✨ <b>Активных аккаунтов:</b> " + str(active_count) + "\n"
        "Выберите действие из меню ниже:"
    )
    await message.answer(text, reply_markup=kb.kb_main_menu(), parse_mode="HTML")


# ════════════════════════════════════════════════════════════════════
# ДОБАВЛЕНИЕ АККАУНТА
# ════════════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "add_account")
async def cb_add_account(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "💎 Пожалуйста, ознакомьтесь:\n\n"
        "📌 <b>Прогрев аккаунта</b>\n"
        "• Длительность: ~6 часов\n"
        "• Возможен бан во время прогрева ⚠️\n"
        "• Возврат средств невозможен!\n\n"
        "⚠️ <b>Требования к аккаунту:</b>\n"
        "• После регистрации/разбана прошёл 1 день\n"
        "• Очищен список контактов\n"
        "• Разрешены входящие сообщения от всех\n"
        "• Приватность → Статус → Мои контакты\n\n"
        "❓ Поддержка доступна через кнопку <b>Поддержка</b> в главном меню.",
        reply_markup=kb.kb_agreement(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "agree_no")
async def cb_agree_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_main_menu(call)


@dp.callback_query(F.data == "agree_yes")
async def cb_agree_yes(call: CallbackQuery, state: FSMContext):
    country_list = "\n".join("• " + c for c in kb.COUNTRIES)
    await call.message.edit_text(
        "🌐 Выберите страну номера для добавления аккаунта:\n\n" + country_list + "\n\n"
        "⚠️ Важно: страна номера и страница в настройках аккаунта должны быть указаны корректно.",
        reply_markup=kb.kb_select_country(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("country_"))
async def cb_select_country(call: CallbackQuery, state: FSMContext):
    country = call.data.replace("country_", "")
    await state.update_data(country=country)
    await state.set_state(AddAccount.waiting_for_phone)

    example = "77001234567" if country == "Казахстан" else "9001234567"
    await call.message.edit_text(
        "📱 Введите номер телефона для страны <b>" + country + "</b>:\n"
        "Например: " + example,
        parse_mode="HTML"
    )


@dp.message(AddAccount.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip().replace("+", "").replace(" ", "").replace("-", "")

    if not phone.isdigit() or len(phone) < 7:
        await message.answer(
            "❌ Некорректный номер телефона. Введите только цифры без пробелов и знаков.\n"
            "Например: 77001234567"
        )
        return

    data = await state.get_data()
    country = data.get("country", "—")

    account_id = await db.add_account(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        phone=phone,
        country=country
    )
    await state.clear()

    await message.answer(
        "Номер телефона <code>" + phone + "</code> успешно добавлен! ✅\n\n"
        "Теперь настройте параметры прогрева и нажмите <b>Запустить</b>.",
        reply_markup=kb.kb_after_add(account_id),
        parse_mode="HTML"
    )


# ════════════════════════════════════════════════════════════════════
# МОИ АККАУНТЫ
# ════════════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "my_accounts")
async def cb_my_accounts(call: CallbackQuery, state: FSMContext):
    await state.clear()
    accounts = await db.get_user_accounts(call.from_user.id)

    if not accounts:
        await call.message.edit_text(
            "📭 У вас пока нет добавленных аккаунтов.\n\nДобавьте первый аккаунт!",
            reply_markup=kb.kb_back_to_menu()
        )
        return

    await call.message.edit_text(
        "📱 <b>Ваши аккаунты (Страница 1/1):</b>",
        reply_markup=kb.kb_accounts_list(accounts[:10]),
        parse_mode="HTML"
    )


# ─── Просмотр карточки аккаунта ──────────────────────────────────────
@dp.callback_query(F.data.startswith("view_acc_"))
async def cb_view_account(call: CallbackQuery, state: FSMContext):
    account_id = int(call.data.replace("view_acc_", ""))
    acc = await db.get_account(account_id)

    if not acc:
        await call.answer("❌ Аккаунт не найден!", show_alert=True)
        return

    await call.message.edit_text(
        build_account_text(acc),
        reply_markup=kb.kb_account_card(account_id, acc),
        parse_mode="HTML"
    )


# ─── Удаление аккаунта ───────────────────────────────────────────────
@dp.callback_query(F.data.startswith("delete_"))
async def cb_delete_account(call: CallbackQuery):
    account_id = int(call.data.replace("delete_", ""))
    acc = await db.get_account(account_id)
    if not acc:
        await call.answer("❌ Аккаунт не найден!", show_alert=True)
        return
    await call.message.edit_text(
        "⚠️ Вы уверены, что хотите удалить аккаунт <code>" + acc["phone"] + "</code>?",
        reply_markup=kb.kb_confirm_delete(account_id),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("confirm_delete_"))
async def cb_confirm_delete(call: CallbackQuery):
    account_id = int(call.data.replace("confirm_delete_", ""))
    await db.delete_account(account_id)
    await call.answer("✅ Аккаунт удалён!")
    accounts = await db.get_user_accounts(call.from_user.id)
    if not accounts:
        await call.message.edit_text(
            "📭 У вас пока нет добавленных аккаунтов.",
            reply_markup=kb.kb_back_to_menu()
        )
    else:
        await call.message.edit_text(
            "📱 <b>Ваши аккаунты (Страница 1/1):</b>",
            reply_markup=kb.kb_accounts_list(accounts[:10]),
            parse_mode="HTML"
        )


# ─── Срок прогрева ───────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("set_duration_"))
async def cb_set_duration(call: CallbackQuery):
    account_id = int(call.data.replace("set_duration_", ""))
    user_hours = await db.get_user_hours(call.from_user.id)
    await call.message.edit_text(
        "⏱ Выберите срок для аккаунта:",
        reply_markup=kb.kb_select_duration(account_id, user_hours)
    )


@dp.callback_query(F.data.startswith("dur_"))
async def cb_select_duration(call: CallbackQuery):
    parts = call.data.split("_")
    account_id = int(parts[1])
    hours = int(parts[2])

    user_hours = await db.get_user_hours(call.from_user.id)
    if user_hours < hours:
        await call.answer("❌ Недостаточно часов! Нужно: " + str(hours) + " ч, у вас: " + str(user_hours) + " ч", show_alert=True)
        return

    await db.update_account_field(account_id, "duration_hours", hours)
    await call.answer("✅ Срок установлен: " + str(hours) + " ч")
    acc = await db.get_account(account_id)
    await call.message.edit_text(
        build_account_text(acc),
        reply_markup=kb.kb_account_card(account_id, acc),
        parse_mode="HTML"
    )


# ─── Тип входа ───────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("toggle_login_"))
async def cb_toggle_login(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_login_", ""))
    acc = await db.get_account(account_id)
    new_val = "QR" if acc["login_type"] == "Код" else "Код"
    await db.update_account_field(account_id, "login_type", new_val)
    await call.answer("Тип входа: " + new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_account_card(account_id, acc))


# ─── Тип прогрева ────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("toggle_warmup_"))
async def cb_toggle_warmup(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_warmup_", ""))
    acc = await db.get_account(account_id)
    new_val = "Новый" if acc["warmup_type"] == "Старый" else "Старый"
    await db.update_account_field(account_id, "warmup_type", new_val)
    await call.answer("Тип прогрева: " + new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_account_card(account_id, acc))


# ─── Тип работы ──────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith("toggle_work_"))
async def cb_toggle_work(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_work_", ""))
    acc = await db.get_account(account_id)
    new_val = "Max" if acc["work_type"] == "WhatsApp" else "WhatsApp"
    await db.update_account_field(account_id, "work_type", new_val)
    await call.answer("Тип работы: " + new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_account_card(account_id, acc))


# ─── Разблокировать / сброс ──────────────────────────────────────────
@dp.callback_query(F.data.startswith("unblock_"))
async def cb_unblock(call: CallbackQuery):
    account_id = int(call.data.replace("unblock_", ""))
    await db.update_account_field(account_id, "status", "не активен")
    await db.update_account_field(account_id, "finish_at", None)
    await call.answer("🔓 Аккаунт сброшен")
    acc = await db.get_account(account_id)
    await call.message.edit_text(
        build_account_text(acc),
        reply_markup=kb.kb_account_card(account_id, acc),
        parse_mode="HTML"
    )


# ─── Настройки прогрева ──────────────────────────────────────────────
@dp.callback_query(F.data.startswith("warmup_settings_"))
async def cb_warmup_settings(call: CallbackQuery):
    account_id = int(call.data.replace("warmup_settings_", ""))
    acc = await db.get_account(account_id)
    await call.message.edit_text(
        "⚙️ <b>Настройки прогрева для аккаунта " + acc["phone"] + "</b>",
        reply_markup=kb.kb_warmup_settings(account_id, acc),
        parse_mode="HTML"
    )


TOGGLE_MAP = {
    "toggle_stories_": "load_stories",
    "toggle_chname_": "change_name",
    "toggle_avatar_": "add_avatar",
    "toggle_bio_": "change_bio",
    "toggle_photos_": "send_photos",
}


@dp.callback_query(F.data.startswith(tuple(TOGGLE_MAP.keys())))
async def cb_toggle_warmup_setting(call: CallbackQuery):
    for prefix, field in TOGGLE_MAP.items():
        if call.data.startswith(prefix):
            account_id = int(call.data.replace(prefix, ""))
            acc = await db.get_account(account_id)
            new_val = 0 if acc[field] else 1
            await db.update_account_field(account_id, field, new_val)
            acc = await db.get_account(account_id)
            await call.message.edit_reply_markup(reply_markup=kb.kb_warmup_settings(account_id, acc))
            await call.answer()
            return


@dp.callback_query(F.data.startswith("toggle_chat_"))
async def cb_toggle_chat(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_chat_", ""))
    acc = await db.get_account(account_id)
    options = ["Личные сообщения", "Группы", "Оба"]
    current = acc.get("chat_type", "Личные сообщения")
    idx = options.index(current) if current in options else 0
    new_val = options[(idx + 1) % len(options)]
    await db.update_account_field(account_id, "chat_type", new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_warmup_settings(account_id, acc))
    await call.answer("Общение: " + new_val)


@dp.callback_query(F.data.startswith("global_settings_"))
async def cb_global_settings(call: CallbackQuery):
    await call.answer("🌐 Глобальные настройки применяются ко всем аккаунтам", show_alert=True)


# ════════════════════════════════════════════════════════════════════
# ЗАПУСК ПРОГРЕВА (только после настройки, по кнопке "Запустить")
# ════════════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("launch_"))
async def cb_launch(call: CallbackQuery):
    account_id = int(call.data.replace("launch_", ""))
    acc = await db.get_account(account_id)

    if not acc:
        await call.answer("❌ Аккаунт не найден!", show_alert=True)
        return

    if acc["status"] in ("работает", "ожидание"):
        await call.answer("⚠️ Прогрев уже запущен или ожидает кода!", show_alert=True)
        return

    user = {
        "id": call.from_user.id,
        "full_name": call.from_user.full_name,
        "username": call.from_user.username or "—"
    }

    # Ставим статус "ожидание" — ждём действия владельца
    await db.update_account_status(account_id, "ожидание")

    # Уведомляем владельца со всеми параметрами и кнопками
    try:
        await send_launch_notification(user, acc)
    except Exception as e:
        logger.error("Ошибка отправки уведомления владельцу: " + str(e))
        await db.update_account_status(account_id, "не активен")
        await call.answer("❌ Ошибка связи с сервером. Попробуйте позже.", show_alert=True)
        return

    await call.message.edit_text(
        "⏳ <b>Запрос на прогрев отправлен!</b>\n\n"
        "📱 Номер: <code>" + acc["phone"] + "</code>\n"
        "⏱ Срок: " + str(acc["duration_hours"]) + " ч\n\n"
        "Ожидайте — вам придёт код подтверждения через этот бот.",
        reply_markup=kb.kb_back_to_menu(),
        parse_mode="HTML"
    )
    await call.answer()


# ════════════════════════════════════════════════════════════════════
# ВЛАДЕЛЕЦ: Отправить код
# ════════════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("send_code_"))
async def cb_owner_send_code(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("❌ Нет доступа!", show_alert=True)
        return

    parts = call.data.split("_")  # send_code_{user_id}_{account_id}
    user_id = int(parts[2])
    account_id = int(parts[3])

    await state.update_data(target_user_id=user_id, target_account_id=account_id)
    await state.set_state(SendCode.waiting_for_code)

    acc = await db.get_account(account_id)
    phone = acc["phone"] if acc else "—"
    await call.message.answer(
        "✏️ Введите код для пользователя (ID: <code>" + str(user_id) + "</code>)\n"
        "Номер: <code>" + phone + "</code>\n\n"
        "Просто напишите код следующим сообщением:",
        parse_mode="HTML"
    )
    await call.answer()


@dp.message(SendCode.waiting_for_code)
async def process_owner_code(message: Message, state: FSMContext):
    if message.from_user.id != OWNER_ID:
        return

    code = message.text.strip()
    data = await state.get_data()
    user_id = data.get("target_user_id")
    account_id = data.get("target_account_id")
    await state.clear()

    acc = await db.get_account(account_id)
    phone = acc["phone"] if acc else "—"

    try:
        await bot.send_message(
            user_id,
            "📲 <b>Код для вашего аккаунта получен!</b>\n\n"
            "📱 Номер: <code>" + phone + "</code>\n"
            "🔑 <b>Ваш код: <code>" + code + "</code></b>\n\n"
            "Введите этот код в WhatsApp/Max для входа.",
            parse_mode="HTML"
        )
        await message.answer(
            "✅ Код <code>" + code + "</code> успешно отправлен пользователю " + str(user_id) + "!\n\n"
            "Не забудьте нажать <b>✅ Готово</b> или <b>❌ Ошибка</b> под уведомлением о запуске.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error("Ошибка отправки кода: " + str(e))
        await message.answer("❌ Не удалось отправить код пользователю " + str(user_id) + ".\nОшибка: " + str(e))


# ════════════════════════════════════════════════════════════════════
# ВЛАДЕЛЕЦ: Готово / Ошибка
# ════════════════════════════════════════════════════════════════════
@dp.callback_query(F.data.startswith("owner_ok_"))
async def cb_owner_ok(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("❌ Нет доступа!", show_alert=True)
        return

    parts = call.data.split("_")  # owner_ok_{user_id}_{account_id}
    user_id = int(parts[2])
    account_id = int(parts[3])

    acc = await db.get_account(account_id)
    if not acc:
        await call.answer("❌ Аккаунт не найден!", show_alert=True)
        return

    hours = acc["duration_hours"]
    finish_at = datetime.utcnow() + timedelta(hours=hours)
    finish_str = finish_at.strftime("%Y-%m-%d %H:%M:%S")

    await db.update_account_field(account_id, "status", "работает")
    await db.update_account_field(account_id, "finish_at", finish_str)

    # Уведомить пользователя
    try:
        await bot.send_message(
            user_id,
            "🔥 <b>Прогрев пошёл!</b>\n\n"
            "📱 Номер: <code>" + acc["phone"] + "</code>\n"
            "⏱ Время прогрева: <b>" + str(hours) + " ч</b>\n\n"
            "Мы уведомим вас когда прогрев завершится.",
            parse_mode="HTML",
            reply_markup=kb.kb_back_to_menu()
        )
    except Exception as e:
        logger.error("Ошибка отправки owner_ok уведомления: " + str(e))

    # Обновить сообщение у владельца
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "✅ Прогрев подтверждён для номера <code>" + acc["phone"] + "</code>\n"
        "Завершится через " + str(hours) + " ч.",
        parse_mode="HTML"
    )
    await call.answer("✅ Готово!")


@dp.callback_query(F.data.startswith("owner_err_"))
async def cb_owner_err(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("❌ Нет доступа!", show_alert=True)
        return

    parts = call.data.split("_")  # owner_err_{user_id}_{account_id}
    user_id = int(parts[2])
    account_id = int(parts[3])

    acc = await db.get_account(account_id)
    phone = acc["phone"] if acc else "—"

    await db.update_account_field(account_id, "status", "не активен")
    await db.update_account_field(account_id, "finish_at", None)

    # Уведомить пользователя об ошибке
    try:
        await bot.send_message(
            user_id,
            "❌ <b>Не удалось запустить прогрев</b>\n\n"
            "📱 Номер: <code>" + phone + "</code>\n\n"
            "Попробуйте запустить ещё раз или обратитесь в поддержку.",
            parse_mode="HTML",
            reply_markup=kb.kb_back_to_menu()
        )
    except Exception as e:
        logger.error("Ошибка отправки owner_err уведомления: " + str(e))

    # Обновить сообщение у владельца
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "❌ Ошибка отмечена для номера <code>" + phone + "</code>. Пользователь уведомлён.",
        parse_mode="HTML"
    )
    await call.answer("❌ Ошибка отмечена")


# ════════════════════════════════════════════════════════════════════
# ВЛАДЕЛЕЦ: команды управления
# ════════════════════════════════════════════════════════════════════
@dp.message(Command("add_hours"))
async def cmd_add_hours(message: Message):
    """Команда владельца: /add_hours <user_id> <часы>"""
    if message.from_user.id != OWNER_ID:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /add_hours <user_id> <часы>")
        return

    try:
        user_id = int(parts[1])
        hours = int(parts[2])
        current = await db.get_user_hours(user_id)
        await db.set_user_hours(user_id, current + hours)
        await message.answer("✅ Добавлено " + str(hours) + " ч пользователю " + str(user_id) + ". Итого: " + str(current + hours) + " ч")
        await bot.send_message(
            user_id,
            "💰 Вам начислено <b>" + str(hours) + " часов</b> прогрева!\n"
            "Итого доступно: <b>" + str(current + hours) + " ч</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("❌ Ошибка: " + str(e))


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Рассылка всем пользователям: /broadcast <текст>"""
    if message.from_user.id != OWNER_ID:
        return

    text = message.text.replace("/broadcast", "", 1).strip()
    if not text:
        await message.answer("Использование: /broadcast <текст сообщения>")
        return

    users = await db.get_all_users()
    sent = 0
    failed = 0
    for uid in users:
        try:
            await bot.send_message(uid, "📢 " + text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer("✅ Рассылка завершена: отправлено " + str(sent) + ", ошибок " + str(failed))


# ════════════════════════════════════════════════════════════════════
# ПОДДЕРЖКА
# ════════════════════════════════════════════════════════════════════
@dp.callback_query(F.data == "support")
async def cb_support(call: CallbackQuery):
    await call.message.edit_text(
        "📞 <b>Поддержка</b>\n\n"
        "Если у вас возникли вопросы или проблемы, напишите владельцу бота.\n\n"
        "Мы постараемся ответить как можно быстрее!",
        reply_markup=kb.kb_back_to_menu(),
        parse_mode="HTML"
    )


# ════════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ════════════════════════════════════════════════════════════════════
async def _show_main_menu(call: CallbackQuery):
    accounts = await db.get_user_accounts(call.from_user.id)
    active_count = len([a for a in accounts if a["status"] == "работает"])
    text = (
        "⭐ Привет, " + call.from_user.first_name + "!\n"
        "➡️ <b>" + BOT_NAME + "</b> — бот для прогрева аккаунтов WhatsApp и Max.\n\n"
        "Здесь можно управлять своими аккаунтами, следить за состоянием прогрева и получить помощь.\n\n"
        "✨ <b>Активных аккаунтов:</b> " + str(active_count) + "\n"
        "Выберите действие из меню ниже:"
    )
    await call.message.edit_text(text, reply_markup=kb.kb_main_menu(), parse_mode="HTML")


@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(call: CallbackQuery, state: FSMContext = None):
    if state:
        await state.clear()
    await _show_main_menu(call)


@dp.callback_query(F.data == "cancel_to_menu")
async def cb_cancel_to_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_main_menu(call)


@dp.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()


@dp.callback_query(F.data == "buy_hours")
async def cb_buy_hours(call: CallbackQuery):
    await call.answer("💰 Для покупки часов обратитесь в поддержку бота.", show_alert=True)


# ════════════════════════════════════════════════════════════════════
# ЗАПУСК
# ════════════════════════════════════════════════════════════════════
async def main():
    await db.init_db()
    logger.info("✅ " + BOT_NAME + " запущен. Владелец ID: " + str(OWNER_ID))

    if OWNER_ID:
        try:
            await bot.send_message(OWNER_ID, "✅ <b>" + BOT_NAME + " запущен!</b>", parse_mode="HTML")
        except Exception:
            pass

    # Запускаем фоновую задачу проверки завершения прогревов
    asyncio.create_task(check_finished_warmups())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
