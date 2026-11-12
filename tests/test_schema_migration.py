import sqlite3
import unittest

from database.schema import SchemaMigrationError, ensure_schema, schema_needs_migration

OFFICIAL_1252_UPDATEITEMS = (
    "CREATE TABLE UpdateItems ("
    "EmbyId INTEGER, "
    "EmbyRequestContent TEXT COLLATE NOCASE, "
    "EmbyLibraryId TEXT COLLATE NOCASE, "
    "KodiDB TEXT COLLATE NOCASE, "
    "EmbyParentId INTEGER, "
    "EmbyParentType TEXT COLLATE NOCASE, "
    "KodiParentId INTEGER, "
    "PRIMARY KEY(EmbyId, KodiDB, EmbyParentId))"
)

CORE_UPDATEITEMS_COLUMNS = ["EmbyId", "EmbyRequestContent", "EmbyLibraryId", "KodiDB"]


class SchemaMigrationTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")

    def tearDown(self):
        self.connection.close()

    def columns(self, table):
        return [row[1] for row in self.connection.execute(f"PRAGMA table_info('{table}')")]

    def test_official_1252_updateitems_is_migrated_to_core(self):
        self.connection.execute(OFFICIAL_1252_UPDATEITEMS)
        self.connection.execute(
            "INSERT INTO UpdateItems (EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB, EmbyParentId, EmbyParentType, KodiParentId) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("42", "Movie", "lib-1", "video", "7", "Season", "3"),
        )

        self.assertTrue(ensure_schema(self.connection))

        self.assertEqual(self.columns("UpdateItems"), CORE_UPDATEITEMS_COLUMNS)
        rows = self.connection.execute("SELECT * FROM UpdateItems").fetchall()
        self.assertEqual(rows, [(42, "Movie", "lib-1", "video")])

        primary_key = [row[5] for row in self.connection.execute("PRAGMA table_info('UpdateItems')")]
        self.assertEqual(primary_key, [1, 0, 0, 2])
        indexes = [row[1] for row in self.connection.execute("PRAGMA index_list('UpdateItems')")]
        self.assertIn("idx_UpdateItems_EmbyId_NullKodiDB", indexes)

    def test_official_updateitems_duplicate_parent_rows_are_collapsed(self):
        self.connection.execute(OFFICIAL_1252_UPDATEITEMS)
        self.connection.executemany(
            "INSERT INTO UpdateItems (EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB, EmbyParentId) VALUES (?, ?, ?, ?, ?)",
            (
                ("8", "Episode", "lib-1", "video", "1"),
                ("8", "Episode", "lib-1", "video", "2"),
            ),
        )

        self.assertTrue(ensure_schema(self.connection))

        self.assertEqual(
            self.connection.execute("SELECT EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB FROM UpdateItems").fetchall(),
            [(8, "Episode", "lib-1", "video")],
        )

    def test_core_updates_can_write_into_official_updateitems(self):
        self.connection.execute(OFFICIAL_1252_UPDATEITEMS)
        self.assertTrue(ensure_schema(self.connection))

        self.connection.execute(
            "INSERT OR REPLACE INTO UpdateItems (EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB) VALUES (?, ?, ?, ?)",
            ("42", "Movie", "lib-1", "video"),
        )
        rows = self.connection.execute(
            "SELECT EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB FROM UpdateItems WHERE EmbyId = ?", ("42",)
        ).fetchall()
        self.assertEqual(rows, [(42, "Movie", "lib-1", "video")])

    def test_current_core_schema_is_idempotent(self):
        self.assertTrue(ensure_schema(self.connection))
        before = {table: self.columns(table) for table in ("UpdateItems", "Playlist", "MediaSources", "Movie")}
        self.connection.execute(
            "INSERT INTO Movie (EmbyId, KodiId, KodiFileId) VALUES (?, ?, ?)", ("1", "10", "20")
        )

        self.assertTrue(ensure_schema(self.connection))

        after = {table: self.columns(table) for table in before}
        self.assertEqual(after, before)
        self.assertEqual(
            self.connection.execute("SELECT EmbyId, KodiId, KodiFileId FROM Movie").fetchall(),
            [(1, 10, 20)],
        )
        self.assertEqual(
            self.columns("UpdateItems"),
            CORE_UPDATEITEMS_COLUMNS,
        )

    def test_missing_playlist_columns_are_added_without_data_loss(self):
        self.connection.execute(
            "CREATE TABLE Playlist (EmbyId INTEGER PRIMARY KEY, KodiId TEXT COLLATE NOCASE, "
            "EmbyFavourite BOOL, EmbyArtwork TEXT COLLATE NOCASE) WITHOUT ROWID"
        )
        self.connection.execute(
            "INSERT INTO Playlist (EmbyId, KodiId, EmbyFavourite, EmbyArtwork) VALUES (?, ?, ?, ?)",
            ("7", "100;200", 1, "image://playlist"),
        )

        self.assertTrue(ensure_schema(self.connection))

        self.assertEqual(
            self.columns("Playlist"),
            ["EmbyId", "KodiId", "EmbyFavourite", "EmbyArtwork", "EmbyLinkedId", "Name"],
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT EmbyId, KodiId, EmbyFavourite, EmbyArtwork, EmbyLinkedId, Name FROM Playlist"
            ).fetchall(),
            [(7, "100;200", 1, "image://playlist", None, None)],
        )

    def test_missing_mediasources_intro_columns_are_added_without_data_loss(self):
        self.connection.execute(
            "CREATE TABLE MediaSources (EmbyId INTEGER, MediaSourceId TEXT COLLATE NOCASE, "
            "Path TEXT COLLATE NOCASE, Name TEXT COLLATE NOCASE, Size INTEGER, "
            "PRIMARY KEY(EmbyId, MediaSourceId))"
        )
        self.connection.execute(
            "INSERT INTO MediaSources (EmbyId, MediaSourceId, Path, Name, Size) VALUES (?, ?, ?, ?, ?)",
            ("9", "src-1", "/media/movie.mkv", "Movie", 1234),
        )

        self.assertTrue(ensure_schema(self.connection))

        self.assertEqual(
            self.columns("MediaSources"),
            ["EmbyId", "MediaSourceId", "Path", "Name", "Size", "IntroStart", "IntroEnd", "CreditsStart"],
        )
        self.assertEqual(
            self.connection.execute(
                "SELECT EmbyId, MediaSourceId, Path, Name, Size, IntroStart, IntroEnd, CreditsStart FROM MediaSources"
            ).fetchall(),
            [(9, "src-1", "/media/movie.mkv", "Movie", 1234, None, None, None)],
        )

    def test_official_video_audio_extra_columns_are_tolerated(self):
        self.connection.execute(
            "CREATE TABLE Video (EmbyId INTEGER PRIMARY KEY, KodiId INTEGER, EmbyFavourite BOOL, "
            "KodiFileId INTEGER, EmbyPresentationKey TEXT COLLATE NOCASE, EmbyFolder TEXT COLLATE NOCASE, "
            "KodiPathId INTEGER, EmbyParentId INTEGER, EmbyExtraType TEXT COLLATE NOCASE, "
            "KodiParentId INTEGER, EmbyParentType TEXT COLLATE NOCASE, EmbyMetaData TEXT COLLATE NOCASE) WITHOUT ROWID"
        )
        self.connection.execute(
            "CREATE TABLE Audio (EmbyId INTEGER PRIMARY KEY, KodiId TEXT COLLATE NOCASE, EmbyFavourite BOOL, "
            "EmbyFolder TEXT COLLATE NOCASE, KodiPathId INTEGER, LibraryIds TEXT COLLATE NOCASE, "
            "EmbyExtraType TEXT COLLATE NOCASE, KodiParentId INTEGER, EmbyParentType TEXT COLLATE NOCASE, "
            "EmbyMetaData TEXT COLLATE NOCASE, EmbyParentId INTEGER) WITHOUT ROWID"
        )
        self.connection.execute(
            "INSERT INTO Video (EmbyId, KodiId, KodiFileId, EmbyParentId, EmbyExtraType) VALUES (?, ?, ?, ?, ?)",
            ("11", "110", "120", 7, "Trailer"),
        )
        self.connection.execute(
            "INSERT INTO Audio (EmbyId, KodiId, LibraryIds, EmbyParentId) VALUES (?, ?, ?, ?)",
            ("12", "130", "lib-1", 8),
        )

        self.assertTrue(ensure_schema(self.connection))

        video = self.connection.execute("SELECT EmbyId, KodiId, KodiFileId, EmbyParentId, EmbyExtraType FROM Video").fetchone()
        self.assertEqual(video, (11, 110, 120, 7, "Trailer"))
        audio = self.connection.execute("SELECT EmbyId, KodiId, LibraryIds, EmbyParentId FROM Audio").fetchone()
        self.assertEqual(audio, (12, "130", "lib-1", 8))
        self.assertIn("EmbyMetaData", self.columns("Audio"))

    def test_unknown_extra_columns_are_tolerated_and_preserved(self):
        self.connection.execute(
            "CREATE TABLE Movie (EmbyId INTEGER PRIMARY KEY, KodiId INTEGER, EmbyFavourite BOOL, "
            "KodiFileId INTEGER, EmbyPresentationKey TEXT COLLATE NOCASE, EmbyFolder TEXT COLLATE NOCASE, "
            "KodiPathId INTEGER, LegacyNote TEXT) WITHOUT ROWID"
        )
        self.connection.execute(
            "INSERT INTO Movie (EmbyId, KodiId, KodiFileId, LegacyNote) VALUES (?, ?, ?, ?)",
            ("5", "50", "60", "keep-me"),
        )

        self.assertTrue(ensure_schema(self.connection))

        self.assertIn("LegacyNote", self.columns("Movie"))
        self.assertEqual(
            self.connection.execute("SELECT EmbyId, KodiId, KodiFileId, LegacyNote FROM Movie").fetchall(),
            [(5, 50, 60, "keep-me")],
        )

    def test_missing_tables_are_created(self):
        self.assertTrue(ensure_schema(self.connection))

        for table in (
            "Genre", "Studio", "Tag", "Person", "Folder", "Movie", "Video", "BoxSet", "Series",
            "Season", "Episode", "MusicArtist", "MusicGenre", "MusicVideo", "MusicAlbum", "Audio",
            "Playlist", "MediaSources", "VideoStreams", "AudioStreams", "SubtitleStreams",
            "RemoveItems", "UpdateItems", "UserdataItems", "LibrarySynced", "LibrarySyncedMirrow",
            "LastIncrementalSync", "LastIncrementalSyncStart", "LibraryAdd", "LibraryRemove",
            "EmbyLibraryMapping",
        ):
            with self.subTest(table=table):
                cols = self.columns(table)
                self.assertTrue(cols, f"{table} was not created")
        self.assertEqual(self.columns("UpdateItems"), CORE_UPDATEITEMS_COLUMNS)

    def test_schema_needs_migration_detects_real_differences(self):
        self.assertTrue(schema_needs_migration(self.connection))
        self.assertTrue(ensure_schema(self.connection))
        self.assertFalse(schema_needs_migration(self.connection))

        self.connection.execute("DROP TABLE UpdateItems")
        self.connection.execute(OFFICIAL_1252_UPDATEITEMS)
        self.assertTrue(schema_needs_migration(self.connection))

        self.connection.execute("DROP TABLE Playlist")
        self.connection.execute(
            "CREATE TABLE Playlist (EmbyId INTEGER PRIMARY KEY, KodiId TEXT COLLATE NOCASE, "
            "EmbyFavourite BOOL, EmbyArtwork TEXT COLLATE NOCASE) WITHOUT ROWID"
        )
        self.assertTrue(schema_needs_migration(self.connection))

    def test_missing_primary_key_column_is_rejected(self):
        self.connection.execute("CREATE TABLE Movie (KodiId INTEGER)")

        with self.assertRaises(SchemaMigrationError):
            ensure_schema(self.connection)

    def test_failed_migration_can_be_rolled_back_by_caller(self):
        self.connection.execute(OFFICIAL_1252_UPDATEITEMS)
        self.connection.execute(
            "INSERT INTO UpdateItems (EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB) VALUES (?, ?, ?, ?)",
            ("9", "Movie", "lib-1", "video"),
        )
        self.connection.commit()

        self.connection.execute("BEGIN IMMEDIATE TRANSACTION")
        ensure_schema(self.connection)
        self.connection.rollback()

        self.assertEqual(
            self.columns("UpdateItems"),
            CORE_UPDATEITEMS_COLUMNS + ["EmbyParentId", "EmbyParentType", "KodiParentId"],
        )
        self.assertEqual(self.columns("Playlist"), [])
        self.assertEqual(
            self.connection.execute("SELECT EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB FROM UpdateItems").fetchall(),
            [(9, "Movie", "lib-1", "video")],
        )

    def test_extra_columns_alone_do_not_request_migration(self):
        self.assertTrue(ensure_schema(self.connection))
        self.connection.execute("ALTER TABLE Movie ADD COLUMN LegacyNote TEXT")

        self.assertFalse(schema_needs_migration(self.connection))

    def test_repeated_migration_keeps_official_rows(self):
        self.connection.execute(OFFICIAL_1252_UPDATEITEMS)
        self.connection.execute(
            "INSERT INTO UpdateItems (EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB) VALUES (?, ?, ?, ?)",
            ("43", "Episode", "lib-2", "video"),
        )

        self.assertTrue(ensure_schema(self.connection))
        self.assertTrue(ensure_schema(self.connection))

        self.assertEqual(self.columns("UpdateItems"), CORE_UPDATEITEMS_COLUMNS)
        self.assertEqual(
            self.connection.execute("SELECT EmbyId, EmbyRequestContent, EmbyLibraryId, KodiDB FROM UpdateItems").fetchall(),
            [(43, "Episode", "lib-2", "video")],
        )


if __name__ == "__main__":
    unittest.main()
