class SchemaMigrationError(Exception):
    pass


def _table(name, columns, primary_key=(), without_rowid=False):
    return {
        "name": name,
        "columns": tuple(columns),
        "primary_key": tuple(primary_key),
        "without_rowid": without_rowid,
    }


TABLES = (
    _table("Genre", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("EmbyArtwork", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Studio", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("EmbyArtwork", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Tag", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("Memo", "TEXT COLLATE NOCASE"),
        ("EmbyArtwork", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Person", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
    ), without_rowid=True),
    _table("Folder", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("EmbyFolder", "TEXT COLLATE NOCASE"),
        ("EmbyMetaData", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Movie", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("KodiFileId", "INTEGER"),
        ("EmbyPresentationKey", "TEXT COLLATE NOCASE"),
        ("EmbyFolder", "TEXT COLLATE NOCASE"),
        ("KodiPathId", "INTEGER"),
    ), without_rowid=True),
    _table("Video", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("KodiFileId", "INTEGER"),
        ("EmbyPresentationKey", "TEXT COLLATE NOCASE"),
        ("EmbyFolder", "TEXT COLLATE NOCASE"),
        ("KodiPathId", "INTEGER"),
        ("EmbyParentId", "INTEGER"),
    ), without_rowid=True),
    _table("BoxSet", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("KodiParentId", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Series", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("EmbyPresentationKey", "TEXT COLLATE NOCASE"),
        ("KodiPathId", "INTEGER"),
    ), without_rowid=True),
    _table("Season", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("KodiParentId", "INTEGER"),
        ("EmbyPresentationKey", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Episode", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "INTEGER"),
        ("EmbyFavourite", "BOOL"),
        ("KodiFileId", "INTEGER"),
        ("KodiParentId", "INTEGER"),
        ("EmbyPresentationKey", "TEXT COLLATE NOCASE"),
        ("EmbyFolder", "TEXT COLLATE NOCASE"),
        ("KodiPathId", "INTEGER"),
    ), without_rowid=True),
    _table("MusicArtist", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "TEXT COLLATE NOCASE"),
        ("EmbyFavourite", "BOOL"),
        ("LibraryIds", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("MusicGenre", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "TEXT COLLATE NOCASE"),
        ("EmbyFavourite", "BOOL"),
        ("LibraryIds", "TEXT COLLATE NOCASE"),
        ("EmbyArtwork", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("MusicVideo", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "TEXT COLLATE NOCASE"),
        ("EmbyFavourite", "BOOL"),
        ("KodiFileId", "TEXT COLLATE NOCASE"),
        ("EmbyPresentationKey", "TEXT COLLATE NOCASE"),
        ("EmbyFolder", "TEXT COLLATE NOCASE"),
        ("KodiPathId", "TEXT COLLATE NOCASE"),
        ("LibraryIds", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("MusicAlbum", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "TEXT COLLATE NOCASE"),
        ("EmbyFavourite", "BOOL"),
        ("LibraryIds", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("Audio", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "TEXT COLLATE NOCASE"),
        ("EmbyFavourite", "BOOL"),
        ("EmbyFolder", "TEXT COLLATE NOCASE"),
        ("KodiPathId", "INTEGER"),
        ("LibraryIds", "TEXT COLLATE NOCASE"),
        ("EmbyParentId", "INTEGER"),
    ), without_rowid=True),
    _table("Playlist", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("KodiId", "TEXT COLLATE NOCASE"),
        ("EmbyFavourite", "BOOL"),
        ("EmbyArtwork", "TEXT COLLATE NOCASE"),
        ("EmbyLinkedId", "TEXT COLLATE NOCASE"),
        ("Name", "TEXT COLLATE NOCASE"),
    ), without_rowid=True),
    _table("MediaSources", (
        ("EmbyId", "INTEGER"),
        ("MediaSourceId", "TEXT COLLATE NOCASE"),
        ("Path", "TEXT COLLATE NOCASE"),
        ("Name", "TEXT COLLATE NOCASE"),
        ("Size", "INTEGER"),
        ("IntroStart", "INTEGER"),
        ("IntroEnd", "INTEGER"),
        ("CreditsStart", "INTEGER"),
    ), primary_key=("EmbyId", "MediaSourceId")),
    _table("VideoStreams", (
        ("EmbyId", "INTEGER"),
        ("MediaSourceId", "TEXT COLLATE NOCASE"),
        ("EmbyIndex", "INTEGER"),
        ("Codec", "TEXT COLLATE NOCASE"),
        ("BitRate", "INTEGER"),
        ("Width", "INTEGER"),
        ("KodiIndex", "INTEGER"),
    ), primary_key=("EmbyId", "MediaSourceId", "EmbyIndex")),
    _table("AudioStreams", (
        ("EmbyId", "INTEGER"),
        ("MediaSourceId", "TEXT COLLATE NOCASE"),
        ("EmbyIndex", "INTEGER"),
        ("DisplayTitle", "TEXT COLLATE NOCASE"),
        ("Codec", "TEXT COLLATE NOCASE"),
        ("BitRate", "INTEGER"),
        ("KodiIndex", "INTEGER"),
    ), primary_key=("EmbyId", "MediaSourceId", "EmbyIndex")),
    _table("SubtitleStreams", (
        ("EmbyId", "INTEGER"),
        ("MediaSourceId", "TEXT COLLATE NOCASE"),
        ("EmbyIndex", "INTEGER"),
        ("Codec", "TEXT COLLATE NOCASE"),
        ("Language", "TEXT COLLATE NOCASE"),
        ("DisplayTitle", "TEXT COLLATE NOCASE"),
        ("External", "BOOL"),
        ("KodiIndex", "INTEGER"),
    ), primary_key=("EmbyId", "MediaSourceId", "EmbyIndex")),
    _table("RemoveItems", (
        ("EmbyId", "INTEGER"),
        ("EmbyLibraryId", "TEXT COLLATE NOCASE"),
    ), primary_key=("EmbyId", "EmbyLibraryId")),
    _table("UpdateItems", (
        ("EmbyId", "INTEGER"),
        ("EmbyRequestContent", "TEXT COLLATE NOCASE"),
        ("EmbyLibraryId", "TEXT COLLATE NOCASE"),
        ("KodiDB", "TEXT COLLATE NOCASE"),
    ), primary_key=("EmbyId", "KodiDB")),
    _table("UserdataItems", (
        ("EmbyId", "INTEGER PRIMARY KEY"),
        ("EmbyType", "TEXT COLLATE NOCASE"),
        ("EmbyPlaybackPositionTicks", "INT"),
        ("EmbyPlayCount", "INT"),
        ("EmbyIsFavorite", "BOOL"),
        ("EmbyPlayed", "BOOL"),
        ("EmbyLastPlayedDate", "TEXT COLLATE NOCASE"),
        ("PlayedPercentage", "INT"),
        ("UnplayedItemCount", "INT"),
    ), without_rowid=True),
    _table("LibrarySynced", (
        ("EmbyLibraryId", "TEXT COLLATE NOCASE"),
        ("EmbyLibraryName", "TEXT COLLATE NOCASE"),
        ("EmbyType", "TEXT COLLATE NOCASE"),
        ("KodiDBs", "TEXT COLLATE NOCASE"),
    ), primary_key=("EmbyLibraryId", "EmbyLibraryName", "EmbyType")),
    _table("LibrarySyncedMirrow", (
        ("EmbyLibraryId", "TEXT COLLATE NOCASE"),
        ("EmbyLibraryName", "TEXT COLLATE NOCASE"),
        ("EmbyType", "TEXT COLLATE NOCASE"),
        ("KodiDBs", "TEXT COLLATE NOCASE"),
    ), primary_key=("EmbyLibraryId", "EmbyLibraryName", "EmbyType")),
    _table("LastIncrementalSync", (
        ("Date", "TEXT"),
    )),
    _table("LastIncrementalSyncStart", (
        ("Date", "TEXT"),
    )),
    _table("LibraryAdd", (
        ("EmbyLibraryId", "TEXT COLLATE NOCASE"),
        ("EmbyLibraryName", "TEXT COLLATE NOCASE"),
        ("EmbyType", "TEXT COLLATE NOCASE"),
        ("KodiDBs", "TEXT COLLATE NOCASE"),
    ), primary_key=("EmbyLibraryId", "EmbyLibraryName", "EmbyType", "KodiDBs")),
    _table("LibraryRemove", (
        ("EmbyLibraryId", "TEXT COLLATE NOCASE PRIMARY KEY"),
        ("EmbyLibraryName", "TEXT COLLATE NOCASE"),
    )),
    _table("EmbyLibraryMapping", (
        ("EmbyLibraryId", "TEXT COLLATE NOCASE"),
        ("EmbyId", "INTEGER"),
        ("EmbyMusicAlbumId", "INTEGER NOT NULL DEFAULT 0"),
        ("EmbyMusicArtistId", "INTEGER NOT NULL DEFAULT 0"),
        ("EmbyMusicGenreId", "INTEGER NOT NULL DEFAULT 0"),
    ), primary_key=("EmbyLibraryId", "EmbyId", "EmbyMusicAlbumId", "EmbyMusicArtistId", "EmbyMusicGenreId")),
)


TABLES_BY_NAME = {table["name"]: table for table in TABLES}


def create_table_sql(table):
    columns = [f"{name} {declaration}" for name, declaration in table["columns"]]

    if table["primary_key"]:
        columns.append(f"PRIMARY KEY({', '.join(table['primary_key'])})")

    sql = f"CREATE TABLE IF NOT EXISTS {table['name']} ({', '.join(columns)})"

    if table["without_rowid"]:
        sql += " WITHOUT ROWID"

    return sql


def schema_needs_migration(connection):
    cursor = connection.cursor()

    for table in TABLES:
        existing = [row[1] for row in cursor.execute(f"PRAGMA table_info('{table['name']}')")]
        required = [name for name, _ in table["columns"]]

        if not existing:
            return True

        if any(name not in existing for name in required):
            return True

        # Official builds add parent columns to UpdateItems with a different primary key.
        if table["name"] == "UpdateItems" and existing != required:
            return True

    return False


def _rebuild_update_items(cursor):
    required = [name for name, _ in TABLES_BY_NAME["UpdateItems"]["columns"]]
    existing = [row[1] for row in cursor.execute("PRAGMA table_info('UpdateItems')")]

    if existing == required:
        return

    rows = cursor.execute(
        "SELECT EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB FROM UpdateItems ORDER BY rowid"
    ).fetchall()
    # Core expects one queue row per item and Kodi database, even when KodiDB is NULL.
    deduplicated = {}
    for row in rows:
        deduplicated[(row[0], row[3])] = row
    rows = list(deduplicated.values())

    cursor.execute("DROP INDEX IF EXISTS idx_UpdateItems_EmbyId_NullKodiDB")
    cursor.execute("DROP TABLE IF EXISTS UpdateItems_migration")
    cursor.execute("ALTER TABLE UpdateItems RENAME TO UpdateItems_migration")
    cursor.execute(create_table_sql(TABLES_BY_NAME["UpdateItems"]))
    cursor.executemany(
        "INSERT OR REPLACE INTO UpdateItems (EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB) VALUES (?, ?, ?, ?)",
        rows,
    )
    cursor.execute("DROP TABLE UpdateItems_migration")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_UpdateItems_EmbyId_NullKodiDB ON UpdateItems (EmbyId) WHERE KodiDB IS NULL")


def ensure_schema(connection):
    cursor = connection.cursor()

    for table in TABLES:
        cursor.execute(create_table_sql(table))

    # Existing tables can come from older core builds or official builds. Add what is
    # missing instead of rejecting the database; unknown extra columns are harmless.
    for table in TABLES:
        existing = {row[1] for row in cursor.execute(f"PRAGMA table_info('{table['name']}')")}
        primary_key = set(table["primary_key"])

        for name, declaration in table["columns"]:
            if name in existing:
                continue

            if name in primary_key or "PRIMARY KEY" in declaration.upper():
                raise SchemaMigrationError(f"Cannot add missing primary key column {table['name']}.{name}")

            cursor.execute(f"ALTER TABLE {table['name']} ADD COLUMN {name} {declaration}")

    _rebuild_update_items(cursor)
    return True
