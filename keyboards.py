from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Создать игру", callback_data="create_game")
    builder.button(text="🔍 Найти игру", callback_data="find_game")
    builder.button(text="❓ Как играть", callback_data="help_game")
    builder.adjust(1)
    return builder.as_markup()


def room_control_keyboard(room_code: str, is_host: bool, player_count: int, max_players: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Игроки", callback_data=f"show_players_{room_code}")
    builder.button(text="🔄 Обновить", callback_data=f"refresh_{room_code}")

    if is_host and player_count >= 2:
        builder.button(text="▶️ Начать игру", callback_data=f"start_game_{room_code}")

    builder.button(text="🚪 Выйти", callback_data=f"leave_room_{room_code}")
    builder.adjust(2, 1)
    return builder.as_markup()


def character_keyboard(room_id: int, user_id: int, revealed: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    buttons = [
        ("👔 Профессия", "profession"),
        ("❤️ Здоровье", "health"),
        ("🎨 Хобби", "hobby"),
        ("⭐ Характер", "trait"),
        ("🎒 Багаж", "baggage"),
        ("📖 Факт", "fact")
    ]

    for label, value in buttons:
        if value in revealed:
            builder.button(text=f"✅ {label}", callback_data=f"already")
        else:
            builder.button(text=f"🔓 {label}", callback_data=f"reveal_{value}_{room_id}_{user_id}")

    builder.adjust(2, 2, 2)
    return builder.as_markup()


def vote_keyboard(players: list, room_id: int, round_num: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in players:
        if p['is_alive']:
            builder.button(text=f"🗳️ {p['username']}", callback_data=f"vote_{room_id}_{round_num}_{p['user_id']}")
    builder.adjust(1)
    return builder.as_markup()


def end_game_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Новая игра", callback_data="new_game")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()

def vote_keyboard(players: list, room_id: int, round_num: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in players:
        if p['is_alive']:
            builder.button(text=f"🗳️ {p['username']}", callback_data=f"vote_{room_id}_{round_num}_{p['user_id']}")
    builder.adjust(1)
    return builder.as_markup()

def end_game_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Новая игра", callback_data="new_game")
    builder.button(text="🏠 Главное меню", callback_data="main_menu")
    builder.adjust(1)
    return builder.as_markup()