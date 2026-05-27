"""
Модуль клавиатур для бота
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ─── Главное меню ───────────────────────────────────────────────────
def kb_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Добавить", callback_data="add_account"),
        InlineKeyboardButton(text="📱 Мои аккаунты", callback_data="my_accounts"),
    )
    builder.row(
        InlineKeyboardButton(text="📞 Поддержка", callback_data="support"),
    )
    return builder.as_markup()


# ─── Согласие ───────────────────────────────────────────────────────
def kb_agreement() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Я согласен", callback_data="agree_yes"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="agree_no"),
    )
    return builder.as_markup()


# ─── Выбор страны ───────────────────────────────────────────────────
COUNTRIES = [
    "Россия", "Казахстан", "Чехия", "Италия", "USA",
    "Словакия", "Словения", "Кыргызстан", "Узбекистан", "Беларусь"
]

def kb_select_country() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for country in COUNTRIES:
        builder.row(InlineKeyboardButton(text=country, callback_data="country_" + country))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_to_menu"))
    return builder.as_markup()


# ─── После добавления номера (идём настраивать, не запускать сразу) ──
def kb_after_add(account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⚙️ Настроить и запустить", callback_data="view_acc_" + str(account_id)))
    builder.row(InlineKeyboardButton(text="◀️ Меню", callback_data="back_to_menu"))
    return builder.as_markup()


# ─── Список аккаунтов ────────────────────────────────────────────────
def kb_accounts_list(accounts: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for acc in accounts:
        if acc["status"] == "работает":
            icon = "✅"
        elif acc["status"] == "ожидание":
            icon = "⏳"
        else:
            icon = "❌"
        builder.row(InlineKeyboardButton(
            text=icon + " " + acc["phone"],
            callback_data="view_acc_" + str(acc["id"])
        ))
    builder.row(InlineKeyboardButton(text="➕ Добавить аккаунт 📱", callback_data="add_account"))
    builder.row(InlineKeyboardButton(text="◀️ Меню", callback_data="back_to_menu"))
    return builder.as_markup()


# ─── Карточка аккаунта ───────────────────────────────────────────────
def kb_account_card(account_id: int, acc: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    status = acc.get("status", "не активен")
    # Кнопка запуска — только если не в процессе и не ожидает
    if status == "ожидание":
        builder.row(InlineKeyboardButton(text="⏳ Ожидание кода...", callback_data="noop"))
    elif status == "работает":
        builder.row(InlineKeyboardButton(text="✅ Прогрев идёт", callback_data="noop"))
    else:
        builder.row(
            InlineKeyboardButton(text="▶️ Запустить", callback_data="launch_" + str(account_id)),
            InlineKeyboardButton(text="❌ Удалить", callback_data="delete_" + str(account_id)),
        )

    if status not in ("ожидание", "работает"):
        builder.row(
            InlineKeyboardButton(text="Срок: " + str(acc.get("duration_hours", 6)) + " ч", callback_data="set_duration_" + str(account_id)),
            InlineKeyboardButton(text="Тип входа: " + acc.get("login_type", "Код"), callback_data="toggle_login_" + str(account_id)),
        )
        builder.row(InlineKeyboardButton(text="⚙️ Настройки прогрева", callback_data="warmup_settings_" + str(account_id)))
        builder.row(InlineKeyboardButton(text="Тип прогрева: " + acc.get("warmup_type", "Старый"), callback_data="toggle_warmup_" + str(account_id)))
        builder.row(InlineKeyboardButton(text="Тип работы: " + acc.get("work_type", "WhatsApp"), callback_data="toggle_work_" + str(account_id)))
    else:
        builder.row(InlineKeyboardButton(text="❌ Удалить", callback_data="delete_" + str(account_id)))

    builder.row(InlineKeyboardButton(text="Страна: " + acc.get("country", "—"), callback_data="noop"))
    builder.row(InlineKeyboardButton(text="🔓 Разблокировать / Сброс", callback_data="unblock_" + str(account_id)))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="my_accounts"))
    return builder.as_markup()


# ─── Выбор срока ─────────────────────────────────────────────────────
def kb_select_duration(account_id: int, user_hours: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    durations = [6, 12, 18, 24]
    for h in durations:
        builder.row(InlineKeyboardButton(
            text=str(h) + " часов  |  у вас: " + str(user_hours) + " ч",
            callback_data="dur_" + str(account_id) + "_" + str(h)
        ))
    builder.row(InlineKeyboardButton(text="💰 Купить часы", callback_data="buy_hours"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="view_acc_" + str(account_id)))
    return builder.as_markup()


# ─── Настройки прогрева ──────────────────────────────────────────────
def kb_warmup_settings(account_id: int, acc: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    def flag(val) -> str:
        return "✅" if val else "❌"

    builder.row(InlineKeyboardButton(
        text="Загружать сторис: " + flag(acc.get("load_stories")),
        callback_data="toggle_stories_" + str(account_id)
    ))
    builder.row(InlineKeyboardButton(
        text="Изменять имя: " + flag(acc.get("change_name")),
        callback_data="toggle_chname_" + str(account_id)
    ))
    builder.row(InlineKeyboardButton(
        text="Добавлять аватар: " + flag(acc.get("add_avatar")),
        callback_data="toggle_avatar_" + str(account_id)
    ))
    builder.row(InlineKeyboardButton(
        text="Изменять описание: " + flag(acc.get("change_bio")),
        callback_data="toggle_bio_" + str(account_id)
    ))
    builder.row(InlineKeyboardButton(
        text="Отправлять фото: " + flag(acc.get("send_photos")),
        callback_data="toggle_photos_" + str(account_id)
    ))
    builder.row(InlineKeyboardButton(
        text="Общение: " + acc.get("chat_type", "Личные сообщения"),
        callback_data="toggle_chat_" + str(account_id)
    ))
    builder.row(InlineKeyboardButton(text="🌐 Глобальные настройки", callback_data="global_settings_" + str(account_id)))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="view_acc_" + str(account_id)))
    return builder.as_markup()


# ─── Подтверждение удаления ──────────────────────────────────────────
def kb_confirm_delete(account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete_" + str(account_id)),
        InlineKeyboardButton(text="❌ Отмена", callback_data="view_acc_" + str(account_id)),
    )
    return builder.as_markup()


# ─── Владелец: кнопки под уведомлением о запуске ────────────────────
def kb_owner_launch(user_id: int, account_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="📨 Отправить код",
        callback_data="send_code_" + str(user_id) + "_" + str(account_id)
    ))
    builder.row(
        InlineKeyboardButton(
            text="✅ Готово (прогрев пошёл)",
            callback_data="owner_ok_" + str(user_id) + "_" + str(account_id)
        ),
        InlineKeyboardButton(
            text="❌ Ошибка",
            callback_data="owner_err_" + str(user_id) + "_" + str(account_id)
        ),
    )
    return builder.as_markup()


# ─── Назад ──────────────────────────────────────────────────────────
def kb_back_to_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Меню", callback_data="back_to_menu"))
    return builder.as_markup()
