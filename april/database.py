from __future__ import annotations

from typing import Iterable, List

import discord
from pie.database import database, session
from sqlalchemy import BigInteger, Column, Boolean, String


class AprilConfig(database.base):

    __tablename__ = "april_april_config"

    role_id = Column(BigInteger, primary_key=True, autoincrement=False)
    guild_id = Column(BigInteger)
    new_role_id = Column(BigInteger)
    to_be_deleted = Column(Boolean)

    @staticmethod
    def add(
        guild: discord.Guild,
        role: discord.Role,
        new_role: discord.Role,
        to_be_deleted: bool,
    ) -> AprilConfig:
        query = AprilConfig(
            role_id=role.id,
            guild_id=guild.id,
            new_role_id=new_role.id,
            to_be_deleted=to_be_deleted,
        )
        session.merge(query)
        session.commit()
        return query

    @staticmethod
    def remove(guild: discord.Guild, role_id: int) -> int:
        query = (
            session.query(AprilConfig)
            .filter_by(role_id=role_id, guild_id=guild.id)
            .delete()
        )
        return query

    @staticmethod
    def get_all(guild: discord.Guild) -> List[AprilConfig]:
        query = session.query(AprilConfig).filter_by(guild_id=guild.id).all()
        return query


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
