from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    games_played = Column(Integer, default=0)
    games_won = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    code = Column(String(6), unique=True, nullable=False)
    host_id = Column(Integer, nullable=False)
    max_players = Column(Integer, default=6)
    survivors_needed = Column(Integer, default=3)
    status = Column(String, default='waiting')
    current_round = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    character = Column(Text)
    is_alive = Column(Boolean, default=True)
    order = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.now)

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    round_number = Column(Integer, default=0)
    voter_id = Column(Integer)
    target_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)

engine = create_engine('sqlite:///bunker.db', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    return SessionLocal()