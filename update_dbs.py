import sqlite3
from config import SERVER_ID

# import shutil
# import os

from config import DB_LOCATION


def update_emoji_db():
    with sqlite3.connect(DB_LOCATION) as con:
        cur = con.cursor()
        cur.executescript(
            """
		    ALTER TABLE
		    emojis_default RENAME TO temp;

		    CREATE TABLE 
		    IF NOT EXISTS 
		    emojis_default (
    		    GuildID INT  NOT NULL,
    		    Name    TEXT NOT NULL,
    		    Uses    INT  NOT NULL,
                UNIQUE (GuildID, Name)
            );

		    INSERT INTO emojis_default(GuildID, Name, Uses)
		    SELECT GuildID, Name, Uses
		    FROM temp;

		    DROP TABLE temp;
		    """
        )
        cur.close()

        cur = con.cursor()
        cur.executescript(
            """
		    ALTER TABLE
		    emojis_custom RENAME TO temp;

            CREATE TABLE 
            IF NOT EXISTS 
            emojis_custom (
                GuildID  INT  NOT NULL,
                EmojiID  INT  NOT NULL,
                Name     TEXT NOT NULL,
                URL      TEXT NOT NULL,
                Uses     INT  NOT NULL,
                UNIQUE(GuildID, EmojiID)
            );

		    INSERT INTO emojis_custom(GuildID, EmojiID, Name, URL, Uses)
		    SELECT GuildID, EmojiID, Name, URL, Uses
		    FROM temp;

		    DROP TABLE temp;
		    """
        )
        cur.close()

        cur = con.cursor()

        cur.execute(
            """
			SELECT name FROM sqlite_master  
			WHERE type='table';
			"""
        )
        print(cur.fetchall())

        cur = con.cursor()
        cur.execute(
            """
			SELECT * FROM emojis_custom
			LIMIT 10;
			"""
        )
        for row in cur.fetchall():
            print(row)

    con.close()


def update_part_db():
    with sqlite3.connect(DB_LOCATION) as con:
        cur = con.cursor()
        cur.executescript(
            """
		    ALTER TABLE
		    part RENAME TO temp;

            CREATE TABLE 
            IF NOT EXISTS 
            part (
                UserID    INT  NOT NULL,
                GuildID   INT  NOT NULL,
                ChannelID INT  NOT NULL,
                Due       INT  NOT NULL,
                Error     TEXT
            );

		    INSERT INTO part(UserID, GuildID, ChannelID, Due, Status)
		    SELECT userID, guildID, channelID, due, NULL
		    FROM temp
            WHERE Status NOT LIKE "Past";

		    DROP TABLE temp;
		    """
        )
        cur.close()
        con.commit()


def update_memories_db():
    with sqlite3.connect(DB_LOCATION) as con:
        cur = con.cursor()
        cur.executescript(
            """
		    ALTER TABLE
		    memories RENAME TO temp;

            CREATE TABLE 
            IF NOT EXISTS 
            memories (
                UserID    INT  NOT NULL,
                PostURL   INT  NOT NULL,
                Reminder  TEXT NOT NULL,
                QueryMade INT  NOT NULL,
                QueryDue  INT  NOT NULL,
                Handled   INT  NOT NULL,
                Error     TEXT 
            );

		    INSERT INTO memories(UserID, PostURL, Reminder, QueryMade, QueryDue, Handled, Error)
            SELECT userID, postUrl, reminder, queryMade, queryDue, 0, NULL
		    FROM temp
            WHERE status LIKE "Future";

		    INSERT INTO memories(UserID, PostURL, Reminder, QueryMade, QueryDue, Handled, Error)
            SELECT userID, postUrl, reminder, queryMade, queryDue, 1, NULL
		    FROM temp
            WHERE status NOT LIKE "Future";

		    DROP TABLE temp;
		    """
        )
        cur.close()
        con.commit()

        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            suggestions (date INT, userID INT, postID INT, t TEXT, b TEXT, d TEXT)
            """
        )
        con.execute(
            """
            CREATE TABLE 
            IF NOT EXISTS 
            used_titles (date INT, t TEXT, b TEXT, d TEXT)
            """
        )


def update_tbd_db():
    with sqlite3.connect(DB_LOCATION) as con:
        cur = con.cursor()
        cur.executescript(
            """
		    ALTER TABLE
		    suggestions RENAME TO temp;

            CREATE TABLE 
            IF NOT EXISTS 
            suggestions (
                Suggestion TEXT NOT NULL
            );

		    INSERT INTO suggestions(Suggestion)
            SELECT t || ' ' || b || ' ' || d
            FROM temp;

		    DROP TABLE temp;
		    """
        )
        cur.close()

        cur = con.cursor()
        cur.executescript(
            f"""
		    ALTER TABLE
		    used_titles RENAME TO temp;

            CREATE TABLE 
            IF NOT EXISTS 
            used_titles (
                GuildID INT  NOT NULL,
                Date    INT  NOT NULL,
                Title   TEXT NOT NULL
            );

		    INSERT INTO used_titles(GuildID, Date, Title)
            SELECT {SERVER_ID}, date, t || ' ' || b || ' ' || d
            FROM temp;

		    DROP TABLE temp;
		    """
        )
        cur.close()
        con.commit()


if __name__ == "__main__":
    update_tbd_db()
