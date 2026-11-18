import sys
import types
import unittest
from urllib.parse import quote


def _install_kodi_stubs():
    if "xbmc" not in sys.modules:
        xbmc = types.ModuleType("xbmc")
        xbmc.LOGDEBUG = xbmc.LOGINFO = xbmc.LOGWARNING = xbmc.LOGERROR = 0
        xbmc.log = lambda *args, **kwargs: None
        sys.modules["xbmc"] = xbmc

    if "helper" not in sys.modules:
        helper = types.ModuleType("helper")
        utils = types.ModuleType("helper.utils")
        utils.EmbyTypeMapping = {"Movie": "movie", "Episode": "episode"}
        helper.utils = utils
        helper.copy = types.ModuleType("helper.copy")
        helper.versions = types.ModuleType("helper.versions")
        sys.modules["helper"] = helper
        sys.modules["helper.utils"] = helper.utils
        sys.modules["helper.copy"] = helper.copy
        sys.modules["helper.versions"] = helper.versions


_install_kodi_stubs()

from core import common  # noqa: E402


class BlurayPathTests(unittest.TestCase):
    def test_scheme_prefix_is_decoded(self):
        path = "bluray://" + quote("/mnt/disc/BDMV/index.bdmv", safe="")
        self.assertEqual(common.bluray_source(path), "/mnt/disc")

    def test_udf_prefix_is_decoded(self):
        path = "udf://" + quote("smb://NAS/Share/Movie/BDMV/index.bdmv", safe="")
        self.assertEqual(common.bluray_source(path), "smb://NAS/Share/Movie")

    def test_unc_path_becomes_smb(self):
        self.assertEqual(
            common.bluray_source("\\\\NAS\\Share\\Movie\\BDMV\\index.bdmv"),
            "smb://NAS/Share/Movie",
        )

    def test_bdmv_suffix_is_removed(self):
        self.assertEqual(common.bluray_source("/mnt/disc/BDMV"), "/mnt/disc")
        self.assertEqual(common.bluray_source("/mnt/disc/BDMV/index.bdmv"), "/mnt/disc")

    def test_iso_path_is_kept(self):
        self.assertEqual(common.bluray_source("/mnt/disc/movie.iso"), "/mnt/disc/movie.iso")

    def test_loopback_url_resolves_single_media_source(self):
        emby = types.ModuleType("emby")
        metadata = types.ModuleType("emby.metadata")
        metadata.load_MetaData = lambda *args: {"MediaSources": [[{"Path": "/mnt/disc/BDMV/index.bdmv"}]]}
        emby.metadata = metadata
        sys.modules["emby"] = emby
        sys.modules["emby.metadata"] = metadata

        self.assertEqual(
            common.bluray_source("http://127.0.0.1:57342/emby/items/1/stream?static=true"),
            "/mnt/disc",
        )


class BluraySourceDetectionTests(unittest.TestCase):
    def test_iso_and_bdmv_are_bluray(self):
        self.assertTrue(common.is_bluray_source("/mnt/disc/movie.iso", ""))
        self.assertTrue(common.is_bluray_source("/mnt/disc/BDMV/index.bdmv", ""))
        self.assertTrue(common.is_bluray_source("/mnt/disc/movie.mkv", "bluray"))
        self.assertTrue(common.is_bluray_source("/mnt/disc/movie.mkv", "ISO"))

    def test_http_iso_alias_is_bluray(self):
        self.assertTrue(common.is_bluray_source("https://host/a/video.iso?token=1", ""))

    def test_regular_video_is_not_bluray(self):
        self.assertFalse(common.is_bluray_source("/mnt/disc/movie.mkv", ""))
        self.assertFalse(common.is_bluray_source("https://host/a/movie.mkv", ""))


class FakeVideo:
    def __init__(self, files):
        self.files = files
        self.path_calls = []
        self.file_path_calls = []

    def get_bluray_files(self, KodiItemId, KodiType):
        return self.files

    def get_add_path(self, path, media):
        self.path_calls.append((path, media))
        return 999

    def update_file_path(self, KodiFileId, KodiPathId):
        self.file_path_calls.append((KodiFileId, KodiPathId))


class FakeEmby:
    def __init__(self, versions=None, items=None, sources=None):
        self.versions = versions or []
        self.items = items or {}
        self.sources = sources or {}
        self.ref_calls = []

    def get_movieversions(self, EmbyId):
        return self.versions

    def get_item_by_id(self, EmbyId, EmbyType):
        return self.items[str(EmbyId)]

    def get_mediasource(self, EmbyId):
        return self.sources

    def update_file_reference(self, EmbyId, EmbyType, KodiFileId, KodiPathId):
        self.ref_calls.append((EmbyId, EmbyType, KodiFileId, KodiPathId))


class BlurayPathUpdateTests(unittest.TestCase):
    def test_unchanged_disc_keeps_file_state(self):
        Item = {
            "Id": "10",
            "KodiFileId": 5,
            "KodiPathId": 6,
            "KodiPath": "/kodi/disc",
            "KodiBlurayFiles": {5: (6, "/kodi/disc", "00000.mpls", "/server/disc")},
        }
        video = FakeVideo([])
        emby = FakeEmby()
        self.assertTrue(common.update_bluray_path(Item, {"video": video, "emby": emby}, "Movie"))
        self.assertEqual(video.file_path_calls, [])
        self.assertEqual(emby.ref_calls, [])

    def test_changed_disc_moves_existing_file(self):
        Item = {
            "Id": "10",
            "KodiFileId": 5,
            "KodiPathId": 6,
            "KodiPath": "/kodi/disc-new",
            "KodiBlurayFiles": {5: (6, "/kodi/disc", "00000.mpls", "/server/disc")},
        }
        video = FakeVideo([])
        emby = FakeEmby()
        self.assertFalse(common.update_bluray_path(Item, {"video": video, "emby": emby}, "Movie"))
        self.assertEqual(Item["KodiPathId"], 999)
        self.assertEqual(video.file_path_calls, [(5, 999)])
        self.assertEqual(emby.ref_calls, [("10", "Movie", 5, 999)])

    def test_unknown_file_does_nothing(self):
        Item = {"Id": "10", "KodiFileId": 5, "KodiPath": "/kodi/disc"}
        self.assertFalse(common.update_bluray_path(Item, {"video": FakeVideo([]), "emby": FakeEmby()}, "Movie"))


class BlurayReferenceSyncTests(unittest.TestCase):
    def _movie_item(self):
        return {
            "Id": "100",
            "UpdateItem": True,
            "KodiItemId": 700,
            "KodiFileId": 800,
            "KodiPathId": 900,
            "MediaSources": [{"Path": "/server/disc/BDMV/index.bdmv", "Container": "bluray"}],
        }

    def test_adopted_mpls_file_is_linked_back_to_movie(self):
        disc = "/server/disc/BDMV/index.bdmv"
        Item = self._movie_item()
        video = FakeVideo([(801, 901, "bluray://" + quote(disc, safe=""), "00000.mpls")])
        emby = FakeEmby(
            versions=[("100", 800, 700, 900)],
            items={"100": (100, 700, 0, 800, "", disc, 900)},
            sources={"src": {"Path": disc}},
        )

        common.sync_bluray_references(Item, {"video": video, "emby": emby}, "Movie")

        self.assertEqual(Item["KodiFileId"], 801)
        self.assertEqual(Item["KodiPathId"], 901)
        self.assertEqual(emby.ref_calls, [("100", "Movie", 801, 901)])
        self.assertEqual(Item["KodiBlurayFiles"][801][3], "/server/disc")

    def test_matching_existing_file_needs_no_reference_update(self):
        disc = "/server/disc/BDMV/index.bdmv"
        Item = self._movie_item()
        video = FakeVideo([(800, 900, "bluray://" + quote(disc, safe=""), "00000.mpls")])
        emby = FakeEmby(
            versions=[("100", 800, 700, 900)],
            items={"100": (100, 700, 0, 800, "", disc, 900)},
            sources={"src": {"Path": disc}},
        )

        common.sync_bluray_references(Item, {"video": video, "emby": emby}, "Movie")

        self.assertEqual(emby.ref_calls, [])
        self.assertIn(800, Item["KodiBlurayFiles"])

    def test_new_items_and_regular_videos_skip_the_lookup(self):
        new_item = self._movie_item()
        new_item["UpdateItem"] = False
        regular = self._movie_item()
        regular["MediaSources"] = [{"Path": "/server/movie.mkv", "Container": "mkv"}]

        for Item in (new_item, regular):
            video = FakeVideo([(1, 2, "bluray://x", "00000.mpls")])
            common.sync_bluray_references(Item, {"video": video, "emby": FakeEmby()}, "Movie")
            self.assertNotIn("KodiBlurayFiles", Item)


if __name__ == "__main__":
    unittest.main()
