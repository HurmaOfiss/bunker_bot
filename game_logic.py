import random
import csv
import json
from typing import Dict, List, Optional
from database import SessionLocal, Room, Player, Vote


class CharacterGenerator:
    def __init__(self, data_path: str):
        self.cards = {
            'profession': [], 'health': [], 'hobby': [],
            'trait': [], 'baggage': [], 'fact': []
        }
        self._load_cards(data_path)

    def _load_cards(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for category in self.cards.keys():
                        if row.get(category) and row[category].strip():
                            self.cards[category].append(row[category].strip())
        except FileNotFoundError:
            self._set_default_cards()

    def _set_default_cards(self):
        self.cards = {
            'profession': ['Врач', 'Инженер', 'Повар', 'Военный', 'Учитель', 'Строитель', 'Художник', 'Музыкант',
                           'Фермер', 'Полицейский', 'Пожарный', 'Программист', 'Водитель', 'Моряк', 'Учёный'],
            'health': ['Здоров', 'Астма', 'Аллергия', 'Диабет', 'Бессонница', 'Идеальное здоровье', 'Слабое сердце',
                       'Сильный иммунитет', 'Проблемы со спиной', 'Мигрень'],
            'hobby': ['Шахматы', 'Рыбалка', 'Чтение', 'Спорт', 'Рисование', 'Музыка', 'Садоводство', 'Охота',
                      'Кулинария', 'Туризм', 'Фотография', 'Рукоделие'],
            'trait': ['Харизматичный', 'Педантичный', 'Добрый', 'Умный', 'Смелый', 'Спокойный', 'Энергичный',
                      'Терпеливый', 'Ответственный', 'Креативный', 'Аналитический', 'Справедливый'],
            'baggage': ['Аптечка', 'Инструменты', 'Книги', 'Еда', 'Вода', 'Оружие', 'Топливо', 'Семена', 'Палатка',
                        'Рация', 'Ноутбук', 'Топор', 'Компас', 'Аппарат для очистки воды'],
            'fact': ['Был в армии', 'Знает 5 языков', 'Выиграл конкурс', 'Путешествовал по миру', 'Имеет тайник',
                     'Спас человека', 'Олимпийский чемпион', 'Доктор наук', 'Имеет выживальческий опыт']
        }

    def generate_character(self) -> Dict:
        return {
            'profession': random.choice(self.cards['profession']),
            'health': random.choice(self.cards['health']),
            'hobby': random.choice(self.cards['hobby']),
            'trait': random.choice(self.cards['trait']),
            'baggage': random.choice(self.cards['baggage']),
            'fact': random.choice(self.cards['fact']),
            'revealed': []
        }


class GameManager:
    def __init__(self):
        self.character_gen = CharacterGenerator('data/cards.csv')

    def create_room(self, user_id: int) -> Optional[str]:
        db = SessionLocal()
        try:
            code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
            room = Room(code=code, host_id=user_id, max_players=6, survivors_needed=3, status='waiting')
            db.add(room)
            db.commit()

            player = Player(room_id=room.id, user_id=user_id,
                            character=json.dumps(self.character_gen.generate_character()), order=0)
            db.add(player)
            db.commit()
            return code
        except:
            db.rollback()
            return None
        finally:
            db.close()

    def join_room(self, user_id: int, username: str, first_name: str, code: str) -> bool:
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.code == code.upper(), Room.status == 'waiting').first()
            if not room:
                return False

            existing = db.query(Player).filter(Player.room_id == room.id, Player.user_id == user_id).first()
            if existing:
                return True

            player_count = db.query(Player).filter(Player.room_id == room.id).count()
            if player_count >= room.max_players:
                return False

            # Сохраняем пользователя
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                user = User(user_id=user_id, username=username, first_name=first_name)
                db.add(user)
                db.commit()

            player = Player(room_id=room.id, user_id=user_id,
                            character=json.dumps(self.character_gen.generate_character()), order=player_count)
            db.add(player)
            db.commit()
            return True
        except:
            db.rollback()
            return False
        finally:
            db.close()

    def get_room_by_code(self, code: str):
        db = SessionLocal()
        try:
            return db.query(Room).filter(Room.code == code.upper()).first()
        finally:
            db.close()

    def get_room_players(self, room_id: int) -> List[Dict]:
        db = SessionLocal()
        try:
            players = db.query(Player).filter(Player.room_id == room_id).all()
            result = []
            for p in players:
                user = db.query(User).filter(User.user_id == p.user_id).first()
                result.append({
                    'user_id': p.user_id,
                    'username': user.username if user and user.username else str(p.user_id),
                    'first_name': user.first_name if user else '',
                    'is_alive': p.is_alive,
                    'order': p.order,
                    'character': json.loads(p.character) if p.character else None
                })
            return result
        finally:
            db.close()

    def start_game(self, room_id: int) -> bool:
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room or room.status != 'waiting':
                return False

            players = db.query(Player).filter(Player.room_id == room_id).all()
            if len(players) < 2:
                return False

            shuffled = random.sample(players, len(players))
            for i, p in enumerate(shuffled):
                p.order = i

            room.status = 'in_progress'
            room.current_round = 1
            db.commit()
            return True
        except:
            db.rollback()
            return False
        finally:
            db.close()

    def get_player_character(self, room_id: int, user_id: int) -> Optional[Dict]:
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.room_id == room_id, Player.user_id == user_id).first()
            if player and player.character:
                return json.loads(player.character)
            return None
        finally:
            db.close()

    def reveal_card(self, room_id: int, user_id: int, card_type: str) -> Optional[str]:
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.room_id == room_id, Player.user_id == user_id).first()
            if not player or not player.character:
                return None

            character = json.loads(player.character)
            if card_type not in character.get('revealed', []):
                if 'revealed' not in character:
                    character['revealed'] = []
                character['revealed'].append(card_type)
                player.character = json.dumps(character)
                db.commit()
                return character.get(card_type, 'Неизвестно')
            return character.get(card_type, 'Неизвестно')
        except:
            db.rollback()
            return None
        finally:
            db.close()

    def add_vote(self, room_id: int, round_number: int, voter_id: int, target_id: int) -> bool:
        db = SessionLocal()
        try:
            existing = db.query(Vote).filter(Vote.room_id == room_id,
                                             Vote.round_number == round_number,
                                             Vote.voter_id == voter_id).first()
            if existing:
                existing.target_id = target_id
            else:
                vote = Vote(room_id=room_id, round_number=round_number,
                            voter_id=voter_id, target_id=target_id)
                db.add(vote)
            db.commit()
            return True
        except:
            db.rollback()
            return False
        finally:
            db.close()

    def get_vote_results(self, room_id: int, round_number: int) -> Dict:
        db = SessionLocal()
        try:
            votes = db.query(Vote).filter(Vote.room_id == room_id,
                                          Vote.round_number == round_number).all()
            results = {}
            for v in votes:
                results[v.target_id] = results.get(v.target_id, 0) + 1
            return results
        finally:
            db.close()

    def clear_votes(self, room_id: int, round_number: int):
        db = SessionLocal()
        try:
            db.query(Vote).filter(Vote.room_id == room_id,
                                  Vote.round_number == round_number).delete()
            db.commit()
        finally:
            db.close()

    def eliminate_player(self, room_id: int, user_id: int) -> bool:
        db = SessionLocal()
        try:
            player = db.query(Player).filter(Player.room_id == room_id, Player.user_id == user_id).first()
            if player:
                player.is_alive = False

            room = db.query(Room).filter(Room.id == room_id).first()
            alive = db.query(Player).filter(Player.room_id == room_id, Player.is_alive == True).count()

            if alive <= room.survivors_needed:
                room.status = 'finished'
                db.commit()
                return True
            else:
                room.current_round += 1
                db.commit()
                return False
        except:
            db.rollback()
            return False
        finally:
            db.close()

class GameManager:
    # ... (существующие методы) ...

    def get_alive_players(self, room_id: int) -> List[Dict]:
        """Возвращает список живых игроков."""
        players = self.get_room_players(room_id)
        return [p for p in players if p['is_alive']]

    def check_winner(self, room_id: int) -> bool:
        """Проверяет, окончена ли игра (количество живых <= survivors_needed)."""
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room:
                return False
            alive_count = db.query(Player).filter(
                Player.room_id == room_id,
                Player.is_alive == True
            ).count()
            return alive_count <= room.survivors_needed
        finally:
            db.close()

    def finish_game(self, room_id: int) -> List[int]:
        """Завершает игру, обновляет статистику победителей, возвращает список user_id победителей."""
        db = SessionLocal()
        try:
            room = db.query(Room).filter(Room.id == room_id).first()
            if not room or room.status != 'in_progress':
                return []

            # Получаем живых игроков
            winners = db.query(Player).filter(
                Player.room_id == room_id,
                Player.is_alive == True
            ).all()
            winner_ids = [p.user_id for p in winners]

            # Обновляем статистику победителей
            for p in winners:
                user = db.query(User).filter(User.user_id == p.user_id).first()
                if user:
                    user.games_won = (user.games_won or 0) + 1

            # Обновляем статистику всех участников (игр сыграно)
            all_players = db.query(Player).filter(Player.room_id == room_id).all()
            for p in all_players:
                user = db.query(User).filter(User.user_id == p.user_id).first()
                if user:
                    user.games_played = (user.games_played or 0) + 1

            room.status = 'finished'
            db.commit()
            return winner_ids
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def eliminate_player(self, room_id: int, user_id: int) -> bool:
        """Исключает игрока, возвращает True, если игра окончена."""
        db = SessionLocal()
        try:
            player = db.query(Player).filter(
                Player.room_id == room_id,
                Player.user_id == user_id,
                Player.is_alive == True
            ).first()
            if player:
                player.is_alive = False
                db.commit()

                # Проверяем окончание игры
                room = db.query(Room).filter(Room.id == room_id).first()
                alive_count = db.query(Player).filter(
                    Player.room_id == room_id,
                    Player.is_alive == True
                ).count()
                if alive_count <= room.survivors_needed:
                    return True  # игра окончена
                else:
                    # Увеличиваем раунд для следующего голосования
                    room.current_round = (room.current_round or 0) + 1
                    db.commit()
                    return False
            return False
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()
def get_room_by_code(self, code: str = None, room_id: int = None):
    db = SessionLocal()
    try:
        if code:
            return db.query(Room).filter(Room.code == code.upper()).first()
        elif room_id:
            return db.query(Room).filter(Room.id == room_id).first()
        return None
    finally:
        db.close()