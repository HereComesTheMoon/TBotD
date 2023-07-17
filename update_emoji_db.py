import sqlite3
import shutil
import os

from config import SERVER_ID, DB_LOCATION, BACKUPS_LOCATION


def main():
    os.mkdir(BACKUPS_LOCATION)
    backup_path = BACKUPS_LOCATION + "db_backup.db"
    assert not os.path.exists(backup_path)
    shutil.copyfile(DB_LOCATION, backup_path)

    with sqlite3.connect(DB_LOCATION) as con:
        cur = con.cursor()
        cur.executescript(
            f"""
		    ALTER TABLE
		    emojis_default RENAME TO temp;

		    CREATE TABLE 
		    IF NOT EXISTS 
		    emojis_default (
		    GuildID INT  NOT NULL,
		    Name    TEXT NOT NULL,
		    Uses    INT  NOT NULL);

		    INSERT INTO emojis_default(GuildID, Name, Uses)
		    SELECT {SERVER_ID}, name, uses
		    FROM temp;

		    DROP TABLE temp;
		    """
        )
        cur.close()

        cur = con.cursor()
        cur.executescript(
            f"""
		    ALTER TABLE
		    emojis_custom RENAME TO temp;

            CREATE TABLE 
            IF NOT EXISTS 
            emojis_custom (
            GuildID  INT  NOT NULL,
            EmojiID  INT  NOT NULL,
            Name     TEXT NOT NULL,
            URL      TEXT NOT NULL,
            Uses     INT  NOT NULL);

		    INSERT INTO emojis_custom(GuildID, EmojiID, Name, URL, Uses)
		    SELECT {SERVER_ID}, emoji_id, name, url, uses
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


if __name__ == "__main__":
    main()
