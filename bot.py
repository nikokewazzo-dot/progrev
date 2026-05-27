"""
Monkey Bot вЂ” Р±РѕС‚ РґР»СЏ РїСЂРѕРіСЂРµРІР° Р°РєРєР°СѓРЅС‚РѕРІ WhatsApp Рё Max
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
from aiogram.exceptions import TelegramNetworkError

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


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# FSM вЂ” СЃРѕСЃС‚РѕСЏРЅРёСЏ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
class AddAccount(StatesGroup):
    waiting_for_phone = State()


class SendCode(StatesGroup):
    waiting_for_code = State()


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р’СЃРїРѕРјРѕРіР°С‚РµР»СЊРЅС‹Рµ С„СѓРЅРєС†РёРё
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
def get_status_icon(status: str) -> str:
    if status == "СЂР°Р±РѕС‚Р°РµС‚":
        return "вњ…"
    elif status == "РѕР¶РёРґР°РЅРёРµ":
        return "вЏі"
    return "вќЊ"


def build_account_text(acc: dict) -> str:
    status = acc.get("status", "РЅРµ Р°РєС‚РёРІРµРЅ")
    status_icon = get_status_icon(status)
    status_label = status.capitalize()

    if status == "СЂР°Р±РѕС‚Р°РµС‚":
        remaining = str(acc["duration_hours"]) + " С‡"
    elif status == "РѕР¶РёРґР°РЅРёРµ":
        remaining = "РћР¶РёРґР°РЅРёРµ РєРѕРґР°..."
    else:
        remaining = "РќРµ Р°РєС‚РёРІРµРЅ"

    return (
        "в„№пёЏ <b>РРЅС„РѕСЂРјР°С†РёСЏ Рѕ РІР°С€РµРј Р°РєРєР°СѓРЅС‚Рµ:</b>\n\n"
        "| рџ“± РќРѕРјРµСЂ С‚РµР»РµС„РѕРЅР°: <code>" + acc["phone"] + "</code>\n"
        "| рџ’Ћ РЎС‚Р°С‚СѓСЃ: " + status_label + " " + status_icon + "\n"
        "| вЏі РћСЃС‚Р°Р»РѕСЃСЊ: " + remaining + "\n\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ"
    )


async def send_launch_notification(user: dict, account: dict):
    """РћС‚РїСЂР°РІРёС‚СЊ РІР»Р°РґРµР»СЊС†Сѓ СѓРІРµРґРѕРјР»РµРЅРёРµ Рѕ Р·Р°РїСѓСЃРєРµ РїСЂРѕРіСЂРµРІР°"""
    def flag(val) -> str:
        return "вњ… Р”Р°" if val else "вќЊ РќРµС‚"

    text = (
        "рџ”Ґ <b>РќРћР’Р«Р™ Р—РђРџРЈРЎРљ РџР РћР“Р Р•Р’Рђ</b>\n\n"
        "рџ‘¤ <b>РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ:</b>\n"
        "   вЂў ID: <code>" + str(user["id"]) + "</code>\n"
        "   вЂў РРјСЏ: " + user.get("full_name", "вЂ”") + "\n"
        "   вЂў Username: @" + user.get("username", "вЂ”") + "\n\n"
        "рџ“± <b>РђРєРєР°СѓРЅС‚:</b>\n"
        "   вЂў РќРѕРјРµСЂ: <code>" + account["phone"] + "</code>\n"
        "   вЂў РЎС‚СЂР°РЅР°: " + account["country"] + "\n"
        "   вЂў РўРёРї СЂР°Р±РѕС‚С‹: " + account["work_type"] + "\n"
        "   вЂў РўРёРї РїСЂРѕРіСЂРµРІР°: " + account["warmup_type"] + "\n"
        "   вЂў РўРёРї РІС…РѕРґР°: " + account["login_type"] + "\n"
        "   вЂў РЎСЂРѕРє: " + str(account["duration_hours"]) + " С‡\n\n"
        "вљ™пёЏ <b>РќР°СЃС‚СЂРѕР№РєРё РїСЂРѕРіСЂРµРІР°:</b>\n"
        "   вЂў Р—Р°РіСЂСѓР¶Р°С‚СЊ СЃС‚РѕСЂРёСЃ: " + flag(account["load_stories"]) + "\n"
        "   вЂў РР·РјРµРЅСЏС‚СЊ РёРјСЏ: " + flag(account["change_name"]) + "\n"
        "   вЂў Р”РѕР±Р°РІР»СЏС‚СЊ Р°РІР°С‚Р°СЂ: " + flag(account["add_avatar"]) + "\n"
        "   вЂў РР·РјРµРЅСЏС‚СЊ РѕРїРёСЃР°РЅРёРµ: " + flag(account["change_bio"]) + "\n"
        "   вЂў РћС‚РїСЂР°РІР»СЏС‚СЊ С„РѕС‚Рѕ: " + flag(account["send_photos"]) + "\n"
        "   вЂў РўРёРї РѕР±С‰РµРЅРёСЏ: " + account["chat_type"] + "\n"
    )

    last_error = None
    for attempt in range(3):
        try:
            await bot.send_message(
                OWNER_ID,
                text,
                parse_mode="HTML",
                reply_markup=kb.kb_owner_launch(user["id"], account["id"])
            )
            return
        except TelegramNetworkError as e:
            last_error = e
            if attempt < 2:
                await asyncio.sleep(1.5 * (attempt + 1))

    if last_error:
        raise last_error


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р¤РћРќРћР’РђРЇ Р—РђР”РђР§Рђ вЂ” РїСЂРѕРІРµСЂРєР° Р·Р°РІРµСЂС€РµРЅРёСЏ РїСЂРѕРіСЂРµРІР°
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
async def check_finished_warmups():
    """РљР°Р¶РґС‹Рµ 60 СЃРµРєСѓРЅРґ РїСЂРѕРІРµСЂСЏРµС‚ Р°РєРєР°СѓРЅС‚С‹ Сѓ РєРѕС‚РѕСЂС‹С… РёСЃС‚РµРєР»Рѕ РІСЂРµРјСЏ"""
    while True:
        try:
            finished = await db.get_accounts_finishing_soon()
            for acc in finished:
                # РЎР±СЂРѕСЃРёС‚СЊ СЃС‚Р°С‚СѓСЃ
                await db.update_account_field(acc["id"], "status", "РЅРµ Р°РєС‚РёРІРµРЅ")
                await db.update_account_field(acc["id"], "finish_at", None)

                # РЈРІРµРґРѕРјРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
                try:
                    await bot.send_message(
                        acc["user_id"],
                        "вњ… <b>РџСЂРѕРіСЂРµРІ СѓСЃРїРµС€РЅРѕ Р·Р°РІРµСЂС€С‘РЅ!</b>\n\n"
                        "рџ“± РќРѕРјРµСЂ: <code>" + acc["phone"] + "</code>\n\n"
                        "Р’С‹ РјРѕР¶РµС‚Рµ Р·Р°РїСѓСЃС‚РёС‚СЊ РїСЂРѕРіСЂРµРІ Р·Р°РЅРѕРІРѕ РІ СЂР°Р·РґРµР»Рµ В«РњРѕРё Р°РєРєР°СѓРЅС‚С‹В».",
                        parse_mode="HTML",
                        reply_markup=kb.kb_back_to_menu()
                    )
                    logger.info("РџСЂРѕРіСЂРµРІ Р·Р°РІРµСЂС€С‘РЅ РґР»СЏ " + acc["phone"] + " (user " + str(acc["user_id"]) + ")")
                except Exception as e:
                    logger.error("РћС€РёР±РєР° СѓРІРµРґРѕРјР»РµРЅРёСЏ Рѕ Р·Р°РІРµСЂС€РµРЅРёРё: " + str(e))
        except Exception as e:
            logger.error("РћС€РёР±РєР° РІ check_finished_warmups: " + str(e))

        await asyncio.sleep(60)


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# /start
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    accounts = await db.get_user_accounts(message.from_user.id)
    active_count = len([a for a in accounts if a["status"] == "СЂР°Р±РѕС‚Р°РµС‚"])

    text = (
        "в­ђ РџСЂРёРІРµС‚, " + message.from_user.first_name + "!\n"
        "вћЎпёЏ <b>" + BOT_NAME + "</b> вЂ” Р±РѕС‚ РґР»СЏ РїСЂРѕРіСЂРµРІР° Р°РєРєР°СѓРЅС‚РѕРІ WhatsApp Рё Max.\n\n"
        "Р—РґРµСЃСЊ РјРѕР¶РЅРѕ СѓРїСЂР°РІР»СЏС‚СЊ СЃРІРѕРёРјРё Р°РєРєР°СѓРЅС‚Р°РјРё, СЃР»РµРґРёС‚СЊ Р·Р° СЃРѕСЃС‚РѕСЏРЅРёРµРј РїСЂРѕРіСЂРµРІР° Рё РїРѕР»СѓС‡РёС‚СЊ РїРѕРјРѕС‰СЊ.\n\n"
        "вњЁ <b>РђРєС‚РёРІРЅС‹С… Р°РєРєР°СѓРЅС‚РѕРІ:</b> " + str(active_count) + "\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ РёР· РјРµРЅСЋ РЅРёР¶Рµ:"
    )
    await message.answer(text, reply_markup=kb.kb_main_menu(), parse_mode="HTML")


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р”РћР‘РђР’Р›Р•РќРР• РђРљРљРђРЈРќРўРђ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.callback_query(F.data == "add_account")
async def cb_add_account(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "рџ’Ћ РџРѕР¶Р°Р»СѓР№СЃС‚Р°, РѕР·РЅР°РєРѕРјСЊС‚РµСЃСЊ:\n\n"
        "рџ“Њ <b>РџСЂРѕРіСЂРµРІ Р°РєРєР°СѓРЅС‚Р°</b>\n"
        "вЂў Р”Р»РёС‚РµР»СЊРЅРѕСЃС‚СЊ: ~6 С‡Р°СЃРѕРІ\n"
        "вЂў Р’РѕР·РјРѕР¶РµРЅ Р±Р°РЅ РІРѕ РІСЂРµРјСЏ РїСЂРѕРіСЂРµРІР° вљ пёЏ\n"
        "вЂў Р’РѕР·РІСЂР°С‚ СЃСЂРµРґСЃС‚РІ РЅРµРІРѕР·РјРѕР¶РµРЅ!\n\n"
        "вљ пёЏ <b>РўСЂРµР±РѕРІР°РЅРёСЏ Рє Р°РєРєР°СѓРЅС‚Сѓ:</b>\n"
        "вЂў РџРѕСЃР»Рµ СЂРµРіРёСЃС‚СЂР°С†РёРё/СЂР°Р·Р±Р°РЅР° РїСЂРѕС€С‘Р» 1 РґРµРЅСЊ\n"
        "вЂў РћС‡РёС‰РµРЅ СЃРїРёСЃРѕРє РєРѕРЅС‚Р°РєС‚РѕРІ\n"
        "вЂў Р Р°Р·СЂРµС€РµРЅС‹ РІС…РѕРґСЏС‰РёРµ СЃРѕРѕР±С‰РµРЅРёСЏ РѕС‚ РІСЃРµС…\n"
        "вЂў РџСЂРёРІР°С‚РЅРѕСЃС‚СЊ в†’ РЎС‚Р°С‚СѓСЃ в†’ РњРѕРё РєРѕРЅС‚Р°РєС‚С‹\n\n"
        "вќ“ РџРѕРґРґРµСЂР¶РєР° РґРѕСЃС‚СѓРїРЅР° С‡РµСЂРµР· РєРЅРѕРїРєСѓ <b>РџРѕРґРґРµСЂР¶РєР°</b> РІ РіР»Р°РІРЅРѕРј РјРµРЅСЋ.",
        reply_markup=kb.kb_agreement(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "agree_no")
async def cb_agree_no(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_main_menu(call)


@dp.callback_query(F.data == "agree_yes")
async def cb_agree_yes(call: CallbackQuery, state: FSMContext):
    country_list = "\n".join("вЂў " + c for c in kb.COUNTRIES)
    await call.message.edit_text(
        "рџЊђ Р’С‹Р±РµСЂРёС‚Рµ СЃС‚СЂР°РЅСѓ РЅРѕРјРµСЂР° РґР»СЏ РґРѕР±Р°РІР»РµРЅРёСЏ Р°РєРєР°СѓРЅС‚Р°:\n\n" + country_list + "\n\n"
        "вљ пёЏ Р’Р°Р¶РЅРѕ: СЃС‚СЂР°РЅР° РЅРѕРјРµСЂР° Рё СЃС‚СЂР°РЅРёС†Р° РІ РЅР°СЃС‚СЂРѕР№РєР°С… Р°РєРєР°СѓРЅС‚Р° РґРѕР»Р¶РЅС‹ Р±С‹С‚СЊ СѓРєР°Р·Р°РЅС‹ РєРѕСЂСЂРµРєС‚РЅРѕ.",
        reply_markup=kb.kb_select_country(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("country_"))
async def cb_select_country(call: CallbackQuery, state: FSMContext):
    country = call.data.replace("country_", "")
    await state.update_data(country=country)
    await state.set_state(AddAccount.waiting_for_phone)

    example = "77001234567" if country == "РљР°Р·Р°С…СЃС‚Р°РЅ" else "9001234567"
    await call.message.edit_text(
        "рџ“± Р’РІРµРґРёС‚Рµ РЅРѕРјРµСЂ С‚РµР»РµС„РѕРЅР° РґР»СЏ СЃС‚СЂР°РЅС‹ <b>" + country + "</b>:\n"
        "РќР°РїСЂРёРјРµСЂ: " + example,
        parse_mode="HTML"
    )


@dp.message(AddAccount.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip().replace("+", "").replace(" ", "").replace("-", "")

    if not phone.isdigit() or len(phone) < 7:
        await message.answer(
            "вќЊ РќРµРєРѕСЂСЂРµРєС‚РЅС‹Р№ РЅРѕРјРµСЂ С‚РµР»РµС„РѕРЅР°. Р’РІРµРґРёС‚Рµ С‚РѕР»СЊРєРѕ С†РёС„СЂС‹ Р±РµР· РїСЂРѕР±РµР»РѕРІ Рё Р·РЅР°РєРѕРІ.\n"
            "РќР°РїСЂРёРјРµСЂ: 77001234567"
        )
        return

    data = await state.get_data()
    country = data.get("country", "вЂ”")

    account_id = await db.add_account(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        phone=phone,
        country=country
    )
    await state.clear()

    await message.answer(
        "РќРѕРјРµСЂ С‚РµР»РµС„РѕРЅР° <code>" + phone + "</code> СѓСЃРїРµС€РЅРѕ РґРѕР±Р°РІР»РµРЅ! вњ…\n\n"
        "РўРµРїРµСЂСЊ РЅР°СЃС‚СЂРѕР№С‚Рµ РїР°СЂР°РјРµС‚СЂС‹ РїСЂРѕРіСЂРµРІР° Рё РЅР°Р¶РјРёС‚Рµ <b>Р—Р°РїСѓСЃС‚РёС‚СЊ</b>.",
        reply_markup=kb.kb_after_add(account_id),
        parse_mode="HTML"
    )


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# РњРћР РђРљРљРђРЈРќРўР«
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.callback_query(F.data == "my_accounts")
async def cb_my_accounts(call: CallbackQuery, state: FSMContext):
    await state.clear()
    accounts = await db.get_user_accounts(call.from_user.id)

    if not accounts:
        await call.message.edit_text(
            "рџ“­ РЈ РІР°СЃ РїРѕРєР° РЅРµС‚ РґРѕР±Р°РІР»РµРЅРЅС‹С… Р°РєРєР°СѓРЅС‚РѕРІ.\n\nР”РѕР±Р°РІСЊС‚Рµ РїРµСЂРІС‹Р№ Р°РєРєР°СѓРЅС‚!",
            reply_markup=kb.kb_back_to_menu()
        )
        return

    await call.message.edit_text(
        "рџ“± <b>Р’Р°С€Рё Р°РєРєР°СѓРЅС‚С‹ (РЎС‚СЂР°РЅРёС†Р° 1/1):</b>",
        reply_markup=kb.kb_accounts_list(accounts[:10]),
        parse_mode="HTML"
    )


# в”Ђв”Ђв”Ђ РџСЂРѕСЃРјРѕС‚СЂ РєР°СЂС‚РѕС‡РєРё Р°РєРєР°СѓРЅС‚Р° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("view_acc_"))
async def cb_view_account(call: CallbackQuery, state: FSMContext):
    account_id = int(call.data.replace("view_acc_", ""))
    acc = await db.get_account(account_id)

    if not acc:
        await call.answer("вќЊ РђРєРєР°СѓРЅС‚ РЅРµ РЅР°Р№РґРµРЅ!", show_alert=True)
        return

    await call.message.edit_text(
        build_account_text(acc),
        reply_markup=kb.kb_account_card(account_id, acc),
        parse_mode="HTML"
    )


# в”Ђв”Ђв”Ђ РЈРґР°Р»РµРЅРёРµ Р°РєРєР°СѓРЅС‚Р° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("delete_"))
async def cb_delete_account(call: CallbackQuery):
    account_id = int(call.data.replace("delete_", ""))
    acc = await db.get_account(account_id)
    if not acc:
        await call.answer("вќЊ РђРєРєР°СѓРЅС‚ РЅРµ РЅР°Р№РґРµРЅ!", show_alert=True)
        return
    await call.message.edit_text(
        "вљ пёЏ Р’С‹ СѓРІРµСЂРµРЅС‹, С‡С‚Рѕ С…РѕС‚РёС‚Рµ СѓРґР°Р»РёС‚СЊ Р°РєРєР°СѓРЅС‚ <code>" + acc["phone"] + "</code>?",
        reply_markup=kb.kb_confirm_delete(account_id),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("confirm_delete_"))
async def cb_confirm_delete(call: CallbackQuery):
    account_id = int(call.data.replace("confirm_delete_", ""))
    await db.delete_account(account_id)
    await call.answer("вњ… РђРєРєР°СѓРЅС‚ СѓРґР°Р»С‘РЅ!")
    accounts = await db.get_user_accounts(call.from_user.id)
    if not accounts:
        await call.message.edit_text(
            "рџ“­ РЈ РІР°СЃ РїРѕРєР° РЅРµС‚ РґРѕР±Р°РІР»РµРЅРЅС‹С… Р°РєРєР°СѓРЅС‚РѕРІ.",
            reply_markup=kb.kb_back_to_menu()
        )
    else:
        await call.message.edit_text(
            "рџ“± <b>Р’Р°С€Рё Р°РєРєР°СѓРЅС‚С‹ (РЎС‚СЂР°РЅРёС†Р° 1/1):</b>",
            reply_markup=kb.kb_accounts_list(accounts[:10]),
            parse_mode="HTML"
        )


# в”Ђв”Ђв”Ђ РЎСЂРѕРє РїСЂРѕРіСЂРµРІР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("set_duration_"))
async def cb_set_duration(call: CallbackQuery):
    account_id = int(call.data.replace("set_duration_", ""))
    user_hours = await db.get_user_hours(call.from_user.id)
    await call.message.edit_text(
        "вЏ± Р’С‹Р±РµСЂРёС‚Рµ СЃСЂРѕРє РґР»СЏ Р°РєРєР°СѓРЅС‚Р°:",
        reply_markup=kb.kb_select_duration(account_id, user_hours)
    )


@dp.callback_query(F.data.startswith("dur_"))
async def cb_select_duration(call: CallbackQuery):
    parts = call.data.split("_")
    account_id = int(parts[1])
    hours = int(parts[2])

    user_hours = await db.get_user_hours(call.from_user.id)
    if user_hours < hours:
        await call.answer("вќЊ РќРµРґРѕСЃС‚Р°С‚РѕС‡РЅРѕ С‡Р°СЃРѕРІ! РќСѓР¶РЅРѕ: " + str(hours) + " С‡, Сѓ РІР°СЃ: " + str(user_hours) + " С‡", show_alert=True)
        return

    await db.update_account_field(account_id, "duration_hours", hours)
    await call.answer("вњ… РЎСЂРѕРє СѓСЃС‚Р°РЅРѕРІР»РµРЅ: " + str(hours) + " С‡")
    acc = await db.get_account(account_id)
    await call.message.edit_text(
        build_account_text(acc),
        reply_markup=kb.kb_account_card(account_id, acc),
        parse_mode="HTML"
    )


# в”Ђв”Ђв”Ђ РўРёРї РІС…РѕРґР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("toggle_login_"))
async def cb_toggle_login(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_login_", ""))
    acc = await db.get_account(account_id)
    new_val = "QR" if acc["login_type"] == "РљРѕРґ" else "РљРѕРґ"
    await db.update_account_field(account_id, "login_type", new_val)
    await call.answer("РўРёРї РІС…РѕРґР°: " + new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_account_card(account_id, acc))


# в”Ђв”Ђв”Ђ РўРёРї РїСЂРѕРіСЂРµРІР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("toggle_warmup_"))
async def cb_toggle_warmup(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_warmup_", ""))
    acc = await db.get_account(account_id)
    new_val = "РќРѕРІС‹Р№" if acc["warmup_type"] == "РЎС‚Р°СЂС‹Р№" else "РЎС‚Р°СЂС‹Р№"
    await db.update_account_field(account_id, "warmup_type", new_val)
    await call.answer("РўРёРї РїСЂРѕРіСЂРµРІР°: " + new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_account_card(account_id, acc))


# в”Ђв”Ђв”Ђ РўРёРї СЂР°Р±РѕС‚С‹ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("toggle_work_"))
async def cb_toggle_work(call: CallbackQuery):
    account_id = int(call.data.replace("toggle_work_", ""))
    acc = await db.get_account(account_id)
    new_val = "Max" if acc["work_type"] == "WhatsApp" else "WhatsApp"
    await db.update_account_field(account_id, "work_type", new_val)
    await call.answer("РўРёРї СЂР°Р±РѕС‚С‹: " + new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_account_card(account_id, acc))


# в”Ђв”Ђв”Ђ Р Р°Р·Р±Р»РѕРєРёСЂРѕРІР°С‚СЊ / СЃР±СЂРѕСЃ в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("unblock_"))
async def cb_unblock(call: CallbackQuery):
    account_id = int(call.data.replace("unblock_", ""))
    await db.update_account_field(account_id, "status", "РЅРµ Р°РєС‚РёРІРµРЅ")
    await db.update_account_field(account_id, "finish_at", None)
    await call.answer("рџ”“ РђРєРєР°СѓРЅС‚ СЃР±СЂРѕС€РµРЅ")
    acc = await db.get_account(account_id)
    await call.message.edit_text(
        build_account_text(acc),
        reply_markup=kb.kb_account_card(account_id, acc),
        parse_mode="HTML"
    )


# в”Ђв”Ђв”Ђ РќР°СЃС‚СЂРѕР№РєРё РїСЂРѕРіСЂРµРІР° в”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђв”Ђ
@dp.callback_query(F.data.startswith("warmup_settings_"))
async def cb_warmup_settings(call: CallbackQuery):
    account_id = int(call.data.replace("warmup_settings_", ""))
    acc = await db.get_account(account_id)
    await call.message.edit_text(
        "вљ™пёЏ <b>РќР°СЃС‚СЂРѕР№РєРё РїСЂРѕРіСЂРµРІР° РґР»СЏ Р°РєРєР°СѓРЅС‚Р° " + acc["phone"] + "</b>",
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
    options = ["Р›РёС‡РЅС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ", "Р“СЂСѓРїРїС‹", "РћР±Р°"]
    current = acc.get("chat_type", "Р›РёС‡РЅС‹Рµ СЃРѕРѕР±С‰РµРЅРёСЏ")
    idx = options.index(current) if current in options else 0
    new_val = options[(idx + 1) % len(options)]
    await db.update_account_field(account_id, "chat_type", new_val)
    acc = await db.get_account(account_id)
    await call.message.edit_reply_markup(reply_markup=kb.kb_warmup_settings(account_id, acc))
    await call.answer("РћР±С‰РµРЅРёРµ: " + new_val)


@dp.callback_query(F.data.startswith("global_settings_"))
async def cb_global_settings(call: CallbackQuery):
    await call.answer("рџЊђ Р“Р»РѕР±Р°Р»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё РїСЂРёРјРµРЅСЏСЋС‚СЃСЏ РєРѕ РІСЃРµРј Р°РєРєР°СѓРЅС‚Р°Рј", show_alert=True)


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р—РђРџРЈРЎРљ РџР РћР“Р Р•Р’Рђ (С‚РѕР»СЊРєРѕ РїРѕСЃР»Рµ РЅР°СЃС‚СЂРѕР№РєРё, РїРѕ РєРЅРѕРїРєРµ "Р—Р°РїСѓСЃС‚РёС‚СЊ")
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.callback_query(F.data.startswith("launch_"))
async def cb_launch(call: CallbackQuery):
    account_id = int(call.data.replace("launch_", ""))
    acc = await db.get_account(account_id)

    if not acc:
        await call.answer("вќЊ РђРєРєР°СѓРЅС‚ РЅРµ РЅР°Р№РґРµРЅ!", show_alert=True)
        return

    if acc["status"] in ("СЂР°Р±РѕС‚Р°РµС‚", "РѕР¶РёРґР°РЅРёРµ"):
        await call.answer("вљ пёЏ РџСЂРѕРіСЂРµРІ СѓР¶Рµ Р·Р°РїСѓС‰РµРЅ РёР»Рё РѕР¶РёРґР°РµС‚ РєРѕРґР°!", show_alert=True)
        return

    user = {
        "id": call.from_user.id,
        "full_name": call.from_user.full_name,
        "username": call.from_user.username or "вЂ”"
    }

    # РЎС‚Р°РІРёРј СЃС‚Р°С‚СѓСЃ "РѕР¶РёРґР°РЅРёРµ" вЂ” Р¶РґС‘Рј РґРµР№СЃС‚РІРёСЏ РІР»Р°РґРµР»СЊС†Р°
    await db.update_account_status(account_id, "РѕР¶РёРґР°РЅРёРµ")

    # РЈРІРµРґРѕРјР»СЏРµРј РІР»Р°РґРµР»СЊС†Р° СЃРѕ РІСЃРµРјРё РїР°СЂР°РјРµС‚СЂР°РјРё Рё РєРЅРѕРїРєР°РјРё
    try:
        await send_launch_notification(user, acc)
    except TelegramNetworkError as e:
        logger.error("Network error while sending launch notification: " + str(e))
        await db.update_account_status(account_id, "РЅРµ Р°РєС‚РёРІРµРЅ")
        await call.answer("❌ Нет связи с Telegram API. Проверьте интернет и попробуйте снова.", show_alert=True)
        return
    except Exception as e:
        logger.error("РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё СѓРІРµРґРѕРјР»РµРЅРёСЏ РІР»Р°РґРµР»СЊС†Сѓ: " + str(e))
        await db.update_account_status(account_id, "РЅРµ Р°РєС‚РёРІРµРЅ")
        await call.answer("❌ Ошибка обработки запроса. Попробуйте позже.", show_alert=True)
        return

    await call.message.edit_text(
        "вЏі <b>Р—Р°РїСЂРѕСЃ РЅР° РїСЂРѕРіСЂРµРІ РѕС‚РїСЂР°РІР»РµРЅ!</b>\n\n"
        "рџ“± РќРѕРјРµСЂ: <code>" + acc["phone"] + "</code>\n"
        "вЏ± РЎСЂРѕРє: " + str(acc["duration_hours"]) + " С‡\n\n"
        "РћР¶РёРґР°Р№С‚Рµ вЂ” РІР°Рј РїСЂРёРґС‘С‚ РєРѕРґ РїРѕРґС‚РІРµСЂР¶РґРµРЅРёСЏ С‡РµСЂРµР· СЌС‚РѕС‚ Р±РѕС‚.",
        reply_markup=kb.kb_back_to_menu(),
        parse_mode="HTML"
    )
    await call.answer()


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р’Р›РђР”Р•Р›Р•Р¦: РћС‚РїСЂР°РІРёС‚СЊ РєРѕРґ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.callback_query(F.data.startswith("send_code_"))
async def cb_owner_send_code(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != OWNER_ID:
        await call.answer("вќЊ РќРµС‚ РґРѕСЃС‚СѓРїР°!", show_alert=True)
        return

    parts = call.data.split("_")  # send_code_{user_id}_{account_id}
    user_id = int(parts[2])
    account_id = int(parts[3])

    await state.update_data(target_user_id=user_id, target_account_id=account_id)
    await state.set_state(SendCode.waiting_for_code)

    acc = await db.get_account(account_id)
    phone = acc["phone"] if acc else "вЂ”"
    await call.message.answer(
        "вњЏпёЏ Р’РІРµРґРёС‚Рµ РєРѕРґ РґР»СЏ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ (ID: <code>" + str(user_id) + "</code>)\n"
        "РќРѕРјРµСЂ: <code>" + phone + "</code>\n\n"
        "РџСЂРѕСЃС‚Рѕ РЅР°РїРёС€РёС‚Рµ РєРѕРґ СЃР»РµРґСѓСЋС‰РёРј СЃРѕРѕР±С‰РµРЅРёРµРј:",
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
    phone = acc["phone"] if acc else "вЂ”"

    try:
        await bot.send_message(
            user_id,
            "рџ“І <b>РљРѕРґ РґР»СЏ РІР°С€РµРіРѕ Р°РєРєР°СѓРЅС‚Р° РїРѕР»СѓС‡РµРЅ!</b>\n\n"
            "рџ“± РќРѕРјРµСЂ: <code>" + phone + "</code>\n"
            "рџ”‘ <b>Р’Р°С€ РєРѕРґ: <code>" + code + "</code></b>\n\n"
            "Р’РІРµРґРёС‚Рµ СЌС‚РѕС‚ РєРѕРґ РІ WhatsApp/Max РґР»СЏ РІС…РѕРґР°.",
            parse_mode="HTML"
        )
        await message.answer(
            "вњ… РљРѕРґ <code>" + code + "</code> СѓСЃРїРµС€РЅРѕ РѕС‚РїСЂР°РІР»РµРЅ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ " + str(user_id) + "!\n\n"
            "РќРµ Р·Р°Р±СѓРґСЊС‚Рµ РЅР°Р¶Р°С‚СЊ <b>вњ… Р“РѕС‚РѕРІРѕ</b> РёР»Рё <b>вќЊ РћС€РёР±РєР°</b> РїРѕРґ СѓРІРµРґРѕРјР»РµРЅРёРµРј Рѕ Р·Р°РїСѓСЃРєРµ.",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error("РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё РєРѕРґР°: " + str(e))
        await message.answer("вќЊ РќРµ СѓРґР°Р»РѕСЃСЊ РѕС‚РїСЂР°РІРёС‚СЊ РєРѕРґ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ " + str(user_id) + ".\nРћС€РёР±РєР°: " + str(e))


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р’Р›РђР”Р•Р›Р•Р¦: Р“РѕС‚РѕРІРѕ / РћС€РёР±РєР°
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.callback_query(F.data.startswith("owner_ok_"))
async def cb_owner_ok(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("вќЊ РќРµС‚ РґРѕСЃС‚СѓРїР°!", show_alert=True)
        return

    parts = call.data.split("_")  # owner_ok_{user_id}_{account_id}
    user_id = int(parts[2])
    account_id = int(parts[3])

    acc = await db.get_account(account_id)
    if not acc:
        await call.answer("вќЊ РђРєРєР°СѓРЅС‚ РЅРµ РЅР°Р№РґРµРЅ!", show_alert=True)
        return

    hours = acc["duration_hours"]
    finish_at = datetime.utcnow() + timedelta(hours=hours)
    finish_str = finish_at.strftime("%Y-%m-%d %H:%M:%S")

    await db.update_account_field(account_id, "status", "СЂР°Р±РѕС‚Р°РµС‚")
    await db.update_account_field(account_id, "finish_at", finish_str)

    # РЈРІРµРґРѕРјРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ
    try:
        await bot.send_message(
            user_id,
            "рџ”Ґ <b>РџСЂРѕРіСЂРµРІ РїРѕС€С‘Р»!</b>\n\n"
            "рџ“± РќРѕРјРµСЂ: <code>" + acc["phone"] + "</code>\n"
            "вЏ± Р’СЂРµРјСЏ РїСЂРѕРіСЂРµРІР°: <b>" + str(hours) + " С‡</b>\n\n"
            "РњС‹ СѓРІРµРґРѕРјРёРј РІР°СЃ РєРѕРіРґР° РїСЂРѕРіСЂРµРІ Р·Р°РІРµСЂС€РёС‚СЃСЏ.",
            parse_mode="HTML",
            reply_markup=kb.kb_back_to_menu()
        )
    except Exception as e:
        logger.error("РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё owner_ok СѓРІРµРґРѕРјР»РµРЅРёСЏ: " + str(e))

    # РћР±РЅРѕРІРёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ Сѓ РІР»Р°РґРµР»СЊС†Р°
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "вњ… РџСЂРѕРіСЂРµРІ РїРѕРґС‚РІРµСЂР¶РґС‘РЅ РґР»СЏ РЅРѕРјРµСЂР° <code>" + acc["phone"] + "</code>\n"
        "Р—Р°РІРµСЂС€РёС‚СЃСЏ С‡РµСЂРµР· " + str(hours) + " С‡.",
        parse_mode="HTML"
    )
    await call.answer("вњ… Р“РѕС‚РѕРІРѕ!")


@dp.callback_query(F.data.startswith("owner_err_"))
async def cb_owner_err(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("вќЊ РќРµС‚ РґРѕСЃС‚СѓРїР°!", show_alert=True)
        return

    parts = call.data.split("_")  # owner_err_{user_id}_{account_id}
    user_id = int(parts[2])
    account_id = int(parts[3])

    acc = await db.get_account(account_id)
    phone = acc["phone"] if acc else "вЂ”"

    await db.update_account_field(account_id, "status", "РЅРµ Р°РєС‚РёРІРµРЅ")
    await db.update_account_field(account_id, "finish_at", None)

    # РЈРІРµРґРѕРјРёС‚СЊ РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РѕР± РѕС€РёР±РєРµ
    try:
        await bot.send_message(
            user_id,
            "вќЊ <b>РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РїСѓСЃС‚РёС‚СЊ РїСЂРѕРіСЂРµРІ</b>\n\n"
            "рџ“± РќРѕРјРµСЂ: <code>" + phone + "</code>\n\n"
            "РџРѕРїСЂРѕР±СѓР№С‚Рµ Р·Р°РїСѓСЃС‚РёС‚СЊ РµС‰С‘ СЂР°Р· РёР»Рё РѕР±СЂР°С‚РёС‚РµСЃСЊ РІ РїРѕРґРґРµСЂР¶РєСѓ.",
            parse_mode="HTML",
            reply_markup=kb.kb_back_to_menu()
        )
    except Exception as e:
        logger.error("РћС€РёР±РєР° РѕС‚РїСЂР°РІРєРё owner_err СѓРІРµРґРѕРјР»РµРЅРёСЏ: " + str(e))

    # РћР±РЅРѕРІРёС‚СЊ СЃРѕРѕР±С‰РµРЅРёРµ Сѓ РІР»Р°РґРµР»СЊС†Р°
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        "вќЊ РћС€РёР±РєР° РѕС‚РјРµС‡РµРЅР° РґР»СЏ РЅРѕРјРµСЂР° <code>" + phone + "</code>. РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ СѓРІРµРґРѕРјР»С‘РЅ.",
        parse_mode="HTML"
    )
    await call.answer("вќЊ РћС€РёР±РєР° РѕС‚РјРµС‡РµРЅР°")


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р’Р›РђР”Р•Р›Р•Р¦: РєРѕРјР°РЅРґС‹ СѓРїСЂР°РІР»РµРЅРёСЏ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.message(Command("add_hours"))
async def cmd_add_hours(message: Message):
    """РљРѕРјР°РЅРґР° РІР»Р°РґРµР»СЊС†Р°: /add_hours <user_id> <С‡Р°СЃС‹>"""
    if message.from_user.id != OWNER_ID:
        return

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ: /add_hours <user_id> <С‡Р°СЃС‹>")
        return

    try:
        user_id = int(parts[1])
        hours = int(parts[2])
        current = await db.get_user_hours(user_id)
        await db.set_user_hours(user_id, current + hours)
        await message.answer("вњ… Р”РѕР±Р°РІР»РµРЅРѕ " + str(hours) + " С‡ РїРѕР»СЊР·РѕРІР°С‚РµР»СЋ " + str(user_id) + ". РС‚РѕРіРѕ: " + str(current + hours) + " С‡")
        await bot.send_message(
            user_id,
            "рџ’° Р’Р°Рј РЅР°С‡РёСЃР»РµРЅРѕ <b>" + str(hours) + " С‡Р°СЃРѕРІ</b> РїСЂРѕРіСЂРµРІР°!\n"
            "РС‚РѕРіРѕ РґРѕСЃС‚СѓРїРЅРѕ: <b>" + str(current + hours) + " С‡</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.answer("вќЊ РћС€РёР±РєР°: " + str(e))


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Р Р°СЃСЃС‹Р»РєР° РІСЃРµРј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј: /broadcast <С‚РµРєСЃС‚>"""
    if message.from_user.id != OWNER_ID:
        return

    text = message.text.replace("/broadcast", "", 1).strip()
    if not text:
        await message.answer("РСЃРїРѕР»СЊР·РѕРІР°РЅРёРµ: /broadcast <С‚РµРєСЃС‚ СЃРѕРѕР±С‰РµРЅРёСЏ>")
        return

    users = await db.get_all_users()
    sent = 0
    failed = 0
    for uid in users:
        try:
            await bot.send_message(uid, "рџ“ў " + text)
            sent += 1
        except Exception:
            failed += 1

    await message.answer("вњ… Р Р°СЃСЃС‹Р»РєР° Р·Р°РІРµСЂС€РµРЅР°: РѕС‚РїСЂР°РІР»РµРЅРѕ " + str(sent) + ", РѕС€РёР±РѕРє " + str(failed))


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# РџРћР”Р”Р•Р Р–РљРђ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
@dp.callback_query(F.data == "support")
async def cb_support(call: CallbackQuery):
    await call.message.edit_text(
        "рџ“ћ <b>РџРѕРґРґРµСЂР¶РєР°</b>\n\n"
        "Р•СЃР»Рё Сѓ РІР°СЃ РІРѕР·РЅРёРєР»Рё РІРѕРїСЂРѕСЃС‹ РёР»Рё РїСЂРѕР±Р»РµРјС‹, РЅР°РїРёС€РёС‚Рµ РІР»Р°РґРµР»СЊС†Сѓ Р±РѕС‚Р°.\n\n"
        "РњС‹ РїРѕСЃС‚Р°СЂР°РµРјСЃСЏ РѕС‚РІРµС‚РёС‚СЊ РєР°Рє РјРѕР¶РЅРѕ Р±С‹СЃС‚СЂРµРµ!",
        reply_markup=kb.kb_back_to_menu(),
        parse_mode="HTML"
    )


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# РЈРўРР›РРўР«
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
async def _show_main_menu(call: CallbackQuery):
    accounts = await db.get_user_accounts(call.from_user.id)
    active_count = len([a for a in accounts if a["status"] == "СЂР°Р±РѕС‚Р°РµС‚"])
    text = (
        "в­ђ РџСЂРёРІРµС‚, " + call.from_user.first_name + "!\n"
        "вћЎпёЏ <b>" + BOT_NAME + "</b> вЂ” Р±РѕС‚ РґР»СЏ РїСЂРѕРіСЂРµРІР° Р°РєРєР°СѓРЅС‚РѕРІ WhatsApp Рё Max.\n\n"
        "Р—РґРµСЃСЊ РјРѕР¶РЅРѕ СѓРїСЂР°РІР»СЏС‚СЊ СЃРІРѕРёРјРё Р°РєРєР°СѓРЅС‚Р°РјРё, СЃР»РµРґРёС‚СЊ Р·Р° СЃРѕСЃС‚РѕСЏРЅРёРµРј РїСЂРѕРіСЂРµРІР° Рё РїРѕР»СѓС‡РёС‚СЊ РїРѕРјРѕС‰СЊ.\n\n"
        "вњЁ <b>РђРєС‚РёРІРЅС‹С… Р°РєРєР°СѓРЅС‚РѕРІ:</b> " + str(active_count) + "\n"
        "Р’С‹Р±РµСЂРёС‚Рµ РґРµР№СЃС‚РІРёРµ РёР· РјРµРЅСЋ РЅРёР¶Рµ:"
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
    await call.answer("рџ’° Р”Р»СЏ РїРѕРєСѓРїРєРё С‡Р°СЃРѕРІ РѕР±СЂР°С‚РёС‚РµСЃСЊ РІ РїРѕРґРґРµСЂР¶РєСѓ Р±РѕС‚Р°.", show_alert=True)


# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
# Р—РђРџРЈРЎРљ
# в•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђв•ђ
async def main():
    await db.init_db()
    logger.info("вњ… " + BOT_NAME + " Р·Р°РїСѓС‰РµРЅ. Р’Р»Р°РґРµР»РµС† ID: " + str(OWNER_ID))

    if OWNER_ID:
        try:
            await bot.send_message(OWNER_ID, "вњ… <b>" + BOT_NAME + " Р·Р°РїСѓС‰РµРЅ!</b>", parse_mode="HTML")
        except Exception:
            pass

    # Р—Р°РїСѓСЃРєР°РµРј С„РѕРЅРѕРІСѓСЋ Р·Р°РґР°С‡Сѓ РїСЂРѕРІРµСЂРєРё Р·Р°РІРµСЂС€РµРЅРёСЏ РїСЂРѕРіСЂРµРІРѕРІ
    asyncio.create_task(check_finished_warmups())

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

