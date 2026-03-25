import asyncio
import logging
from typing import Dict, Optional
from aiogram import Bot, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, DISCUSSION_TIME, VOTE_TIME
from database import SessionLocal, User, Room, Player
from game_logic import GameManager
from keyboards import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

game_manager = GameManager()

class GameStates(StatesGroup):
    waiting_for_code = State()
    in_game = State()
    discussion = State()
    voting = State()

# Словарь для хранения задач таймеров
timers = {}

async def stop_timer(room_id: int, timer_key: str):
    """Останавливает таймер для комнаты, если он существует."""
    key = f"{room_id}_{timer_key}"
    if key in timers:
        timers[key].cancel()
        del timers[key]

async def start_discussion_timer(room_id: int, bot: Bot):
    """Запускает таймер обсуждения."""
    key = f"{room_id}_discussion"
    loop = asyncio.get_event_loop()
    task = loop.create_task(discussion_timeout(room_id, bot))
    timers[key] = task

async def discussion_timeout(room_id: int, bot: Bot):
    """Таймер обсуждения: по истечении времени переходит к голосованию."""
    await asyncio.sleep(DISCUSSION_TIME)
    await stop_timer(room_id, "discussion")
    await start_voting(room_id, bot)

async def start_voting(room_id: int, bot: Bot):
    """Начинает голосование в комнате."""
    room = game_manager.get_room_by_code(None, room_id=room_id)  # нужно доработать get_room_by_code
    if not room or room.status != 'in_progress':
        return

    # Получаем живых игроков
    players = game_manager.get_alive_players(room_id)
    if len(players) <= 1:
        # Если остался один, завершаем игру
        await finish_game(room_id, bot)
        return

    # Отправляем сообщение о начале голосования
    for p in players:
        keyboard = vote_keyboard(players, room_id, room.current_round or 1)
        await bot.send_message(
            p['user_id'],
            f"🗳️ *Раунд {room.current_round or 1} – Голосование!*\n\n"
            f"У вас есть {VOTE_TIME} секунд, чтобы проголосовать за игрока, который должен покинуть бункер.\n"
            f"Нажмите на кнопку с именем игрока.",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # Запускаем таймер голосования
    key = f"{room_id}_voting"
    loop = asyncio.get_event_loop()
    task = loop.create_task(voting_timeout(room_id, bot))
    timers[key] = task

async def voting_timeout(room_id: int, bot: Bot):
    """Таймер голосования: по истечении времени подводит итоги."""
    await asyncio.sleep(VOTE_TIME)
    await stop_timer(room_id, "voting")
    await process_voting_results(room_id, bot)

async def process_voting_results(room_id: int, bot: Bot):
    """Подводит итоги голосования, исключает игрока, проверяет конец игры."""
    room = game_manager.get_room_by_code(None, room_id=room_id)
    if not room or room.status != 'in_progress':
        return

    current_round = room.current_round or 1
    results = game_manager.get_vote_results(room_id, current_round)
    if not results:
        # Если никто не проголосовал, исключаем случайного
        players = game_manager.get_alive_players(room_id)
        if players:
            # Случайный выбор
            import random
            eliminated = random.choice(players)
            eliminated_id = eliminated['user_id']
        else:
            return
    else:
        # Находим игрока с максимальным количеством голосов
        max_votes = max(results.values())
        candidates = [uid for uid, votes in results.items() if votes == max_votes]
        # Если несколько, выбираем случайного
        import random
        eliminated_id = random.choice(candidates)

    # Исключаем игрока
    game_over = game_manager.eliminate_player(room_id, eliminated_id)

    # Уведомляем всех о результате
    players = game_manager.get_room_players(room_id)
    eliminated_name = next((p['username'] for p in players if p['user_id'] == eliminated_id), "Игрок")

    for p in players:
        await bot.send_message(
            p['user_id'],
            f"🚪 *Итоги голосования (раунд {current_round})*\n\n"
            f"Игрок {eliminated_name} покидает бункер.\n"
            f"Осталось живых: {len([x for x in players if x['is_alive']])}",
            parse_mode="Markdown"
        )

    # Очищаем голоса для следующего раунда
    game_manager.clear_votes(room_id, current_round)

    if game_over:
        # Игра окончена
        await finish_game(room_id, bot)
    else:
        # Начинаем следующий раунд обсуждения
        await start_discussion_round(room_id, bot)

async def start_discussion_round(room_id: int, bot: Bot):
    """Начинает новый раунд обсуждения."""
    room = game_manager.get_room_by_code(None, room_id=room_id)
    if not room or room.status != 'in_progress':
        return

    players = game_manager.get_alive_players(room_id)
    if len(players) <= 1:
        await finish_game(room_id, bot)
        return

    # Сообщаем о начале обсуждения
    for p in players:
        await bot.send_message(
            p['user_id'],
            f"💬 *Раунд {room.current_round or 1} – Обсуждение*\n\n"
            f"У вас есть {DISCUSSION_TIME} секунд, чтобы обсудить кандидатов на исключение.\n"
            f"После этого начнётся голосование.",
            parse_mode="Markdown"
        )

    # Запускаем таймер обсуждения
    await start_discussion_timer(room_id, bot)

async def finish_game(room_id: int, bot: Bot):
    """Завершает игру, объявляет победителей, обновляет статистику."""
    winner_ids = game_manager.finish_game(room_id)
    players = game_manager.get_room_players(room_id)

    # Формируем сообщение о победителях
    winners = [p for p in players if p['user_id'] in winner_ids]
    winner_names = ", ".join([p['username'] for p in winners])

    for p in players:
        text = (
            f"🏆 *Игра окончена!*\n\n"
            f"Победители, попавшие в бункер: {winner_names}\n\n"
            f"Спасибо за игру!\n"
            f"Сыграно игр: {p.get('games_played', 0)+1 if p['user_id'] in winner_ids else p.get('games_played', 0)}"
        )
        await bot.send_message(
            p['user_id'],
            text,
            parse_mode="Markdown",
            reply_markup=end_game_keyboard()
        )

    # Очищаем таймеры
    await stop_timer(room_id, "discussion")
    await stop_timer(room_id, "voting")

# Регистрация обработчиков (оставляем существующие и добавляем новые)

async def register_handlers(dp, bot: Bot):
    # ... (существующие обработчики команд и callback'ов) ...

    # Добавляем новый обработчик для голосования
    @dp.callback_query(F.data.startswith("vote_"))
    async def handle_vote(callback: CallbackQuery):
        parts = callback.data.split("_")
        room_id = int(parts[1])
        round_num = int(parts[2])
        target_id = int(parts[3])
        voter_id = callback.from_user.id

        # Проверяем, что голосование ещё идёт
        room = game_manager.get_room_by_code(None, room_id=room_id)
        if not room or room.status != 'in_progress':
            await callback.answer("Игра уже не активна", show_alert=True)
            return

        # Проверяем, что голосующий жив
        players = game_manager.get_alive_players(room_id)
        if not any(p['user_id'] == voter_id for p in players):
            await callback.answer("Вы уже выбыли из игры", show_alert=True)
            return

        # Проверяем, что цель жива
        if not any(p['user_id'] == target_id for p in players):
            await callback.answer("Этот игрок уже выбыл", show_alert=True)
            return

        success = game_manager.add_vote(room_id, round_num, voter_id, target_id)
        if success:
            await callback.answer("✅ Ваш голос учтён!", show_alert=False)
            await callback.message.delete()
        else:
            await callback.answer("❌ Ошибка при голосовании", show_alert=True)

    # Обработчик старта игры (дополняем таймером обсуждения)
    @dp.callback_query(F.data.startswith("start_game_"))
    async def start_game_callback(callback: CallbackQuery):
        code = callback.data.split("_")[-1]
        user_id = callback.from_user.id

        room = game_manager.get_room_by_code(code)
        if not room or room.host_id != user_id:
            await callback.answer("Только создатель может начать игру")
            return

        if game_manager.start_game(room.id):
            players = game_manager.get_room_players(room.id)

            await callback.message.edit_text(
                "🎲 *Игра началась!*\n\n"
                "Каждый получит карточку персонажа. После этого начнётся обсуждение.",
                parse_mode="Markdown"
            )

            # Рассылаем карточки
            for p in players:
                character = game_manager.get_player_character(room.id, p['user_id'])
                char_text = "🧬 *Ваш персонаж*\n\n"
                for key, label in [('profession', 'Профессия'), ('health', 'Здоровье'),
                                   ('hobby', 'Хобби'), ('trait', 'Характер'),
                                   ('baggage', 'Багаж'), ('fact', 'Факт')]:
                    char_text += f"• {label}: ❓\n"
                char_text += "\n*Нажимайте кнопки, чтобы открывать характеристики*"

                await bot.send_message(p['user_id'], char_text, parse_mode="Markdown",
                                      reply_markup=character_keyboard(room.id, p['user_id'], []))

            # Порядок выступлений
            order_text = "*📢 Порядок выступлений:*\n"
            for p in sorted(players, key=lambda x: x['order']):
                order_text += f"{p['order'] + 1}. {p['username']}\n"

            for p in players:
                await bot.send_message(p['user_id'], order_text, parse_mode="Markdown")

            # Запускаем обсуждение
            await start_discussion_round(room.id, bot)

            await callback.answer("Игра начата!")
        else:
            await callback.answer("Не удалось начать игру (нужно минимум 2 игрока)")

    # ... остальные обработчики ...