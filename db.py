import aiosqlite
import os
from datetime import datetime
from pathlib import Path

import sqlite3

from config import DB_LOCATION, BACKUPS_LOCATION


async def get_database(location: str) -> aiosqlite.Connection:
    if os.path.isfile(location):
        con = await aiosqlite.connect(location)
        con.row_factory = aiosqlite.Row
        return con
    raise FileNotFoundError


def check_backups(backup_folder: str):
    print("Checking backup folder.")
    backup_folder = Path(backup_folder)
    if not os.path.exists(backup_folder):
        print("Can't find backup folder.")
        return

    def check(f: str) -> bool:
        if not os.path.isfile(os.path.join(backup_folder, f)):
            return False
        date = f[:19]
        db = f[19:]
        if db != "_db.db":
            return False
        try:
            datetime.fromisoformat(date)
        except ValueError:
            return False
        return True

    for file in os.listdir(backup_folder):
        if not check(file):
            print(f"Unexpected file or folder in backups folder: {file}")
            continue
    print("Done")


def backup(db_location: str, backup_folder: str):
    print("Backup start.")
    if not os.path.isfile(db_location):
        raise FileNotFoundError
    backup_folder = Path(backup_folder)
    if not os.path.exists(backup_folder):
        print("No backup folder found, creating...")
        os.makedirs(backup_folder)
    now = datetime.now().isoformat(timespec="seconds")

    new_backup = os.path.join(backup_folder, now + "_db.db")
    if os.path.isfile(new_backup):
        print("Last backup was less than one second ago? Aborting.")
        return
    print(f"Creating new backup file: {new_backup}")

    new_con = sqlite3.connect(new_backup)
    con = sqlite3.connect(db_location)

    con.backup(new_con)

    new_con.close()
    con.close()
    print("Backup done.")


def initialise_database(location: str):
    """Columns CamelCase, Tables snake_case"""
    location = Path(DB_LOCATION)
    os.makedirs(location.parent, exist_ok=True)
    if not os.path.isfile(location):
        print("Database doesn't exist yet! This is weird and should be investigated.")

    with sqlite3.connect(location) as con:
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            memories (userID INTEGER, postID INTEGER, postUrl TEXT, reminder TEXT, queryMade INT, queryDue INT, status TEXT);
            """
        )
        con.execute(
            """
            CREATE TABLE
            IF NOT EXISTS
            remove_role (
                UserID  INT NOT NULL,
                GuildID INT NOT NULL,
                RoleID  INT NOT NULL,
                Due     INT NOT NULL,
                Error TEXT
            );"""
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            emojis_default (
                GuildID INT  NOT NULL,
                Name    TEXT NOT NULL,
                Uses    INT  NOT NULL,
                UNIQUE (GuildID, Name)
            );
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            emojis_custom (
                GuildID  INT  NOT NULL,
                EmojiID  INT  NOT NULL,
                Name     TEXT NOT NULL,
                URL      TEXT NOT NULL,
                Uses     INT  NOT NULL,
                UNIQUE (GuildID, EmojiID)
            );
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            suggestions (
                Suggestion TEXT NOT NULL
            );
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            used_titles (
                GuildID INT  NOT NULL,
                Date    INT  NOT NULL,
                Title   TEXT NOT NULL
            );
            """
        )
        con.execute(
            """
            CREATE TABLE
            IF NOT EXISTS
            yuds (date INT, userID INT, postID INT, width INT, height INT, quality INT)
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            yudminders (userID INT, due INT);
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            part (
                UserID    INT  NOT NULL,
                GuildID   INT  NOT NULL,
                ChannelID INT  NOT NULL,
                Due       INT  NOT NULL,
                Error     TEXT
            );
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            hotwords (
                UserID    INT  NOT NULL,
                Hotword   TEXT NOT NULL
            );
            """
        )


async def add_hotword(con: aiosqlite.Connection, user_id: int, hotword: str):
    await con.execute(
        "INSERT INTO hotwords (UserID, Hotword) VALUES (?, ?)", (user_id, hotword)
    )
    await con.commit()


async def remove_hotword(con: aiosqlite.Connection, user_id: int, hotword: str):
    await con.execute(
        "DELETE FROM hotwords WHERE UserID = ? AND Hotword = ?", (user_id, hotword)
    )
    await con.commit()


async def get_hotwords(con: aiosqlite.Connection, user_id: int):
    cursor = await con.execute(
        "SELECT Hotword FROM hotwords WHERE UserID = ?", (user_id,)
    )
    rows = await cursor.fetchall()
    return [row["Hotword"] for row in rows]


if __name__ == "__main__":
    initialise_database(DB_LOCATION)
    backup(DB_LOCATION, BACKUPS_LOCATION)
    check_backups(BACKUPS_LOCATION)
