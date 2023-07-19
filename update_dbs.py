import sqlite3

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


if __name__ == "__main__":
    update_part_db()
