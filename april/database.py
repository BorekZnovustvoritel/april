from __future__ import annotations

from typing import Iterable, List

import discord
from pie.database import database, session
from sqlalchemy import BigInteger, Column, Boolean, String


class AprilConfig(database.base):

    __tablename__ = "april_april_config"

    role_id = Column(BigInteger, primary_ley=True, autoincrement=False)
    guild_id = Column(BigInteger)

    @staticmethod
    def add(guild: discord.Guild, role: discord.Role) -> AprilConfig:
        query = AprilConfig(role_id=role.id, guild_id=guild.id)
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def remove(guild: discord.Guild, role: discord.Role) -> int:
        query = session.query(AprilConfig).filter_by(role_id=role.id, guild_id=guild.id).delete()
        return query

    @staticmethod
    def get_all(guild: discord.Guild) -> List[AprilConfig]:
        query = session.query(AprilConfig).filter_by(guild_id=guild.id).all()
        return query


class NewRoles(database.base):
    __tablename__ = "april_april_new_roles"
    role_id = Column(BigInteger, primary_key=True, autoincrement=False)
    guild_id = Column(BigInteger)

    @staticmethod
    def add(guild: discord.Guild, role: discord.Role):
        query = NewRoles(role_id=role.id, guild_id=guild.id)
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def nuke(guild: discord.Guild):
        query = session.query(NewRoles).filter_by(guild_id=guild.id).delete()
        return query

    @staticmethod
    def get_all(guild: discord.Guild) -> List[NewRoles]:
        return session.query(NewRoles).filter_by(guild_id=guild.id).all()


class Nicknames(database.base):
    __tablename__ = "april_april_nicknames"
    user_id = Column(BigInteger, primary_key=True, autoincrement=False)
    guild_id = Column(BigInteger)
    old_nickname = Column(String)

    @staticmethod
    def add(user: discord.Member, guild: discord.Guild) -> Nicknames:
        query = Nicknames(user_id=user.id, guild_id=guild.id, old_nickname=user.nick)
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def get_all(guild: discord.Guild) -> Iterable[Nicknames]:
        query = session.query(Nicknames).filter_by(guild_id=guild.id).all()
        return query

    @staticmethod
    def delete_all(guild: discord.Guild) -> int:
        return session.query(Nicknames).filter_by(guild_id=guild.id).delete()
