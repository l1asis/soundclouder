__all__ = ["Tag", "TagKey", "Path", "Stream", "MIME", "Extension", "Hydration", "Hydratable", "Regexp", "Table"]

import re

class Tag:
    STRING = dict[str, str]
    EMPTY = dict
    PICTURE_MP3 = dict[str, bytes]
    PICTURE_OPUS = dict[str, str]

class TagKey:
    PICTURE = "picture"
    OGG_PICTURE = "metadata_block_picture"
    TITLE = "title"
    ARTIST = "artist"
    ALBUM_ARTIST = "albumartist"
    ALBUM = "album"
    GENRE = "genre"
    TRACK_NUMBER = "tracknumber"
    RELEASE_DATE = "date"
    PUBLISHER = "organization"
    COPYRIGHT = "copyright"

# Paths
class Path:
    CURRENT_FOLDER = "."

# Stream types
class Stream:
    MP3_HLS = 0
    MP3_PROGRESSIVE = 1
    OPUS_HLS = 2

class MIME:
    JPG = "image/jpeg"
    MP3 = "audio/mpeg"
    OPUS = "audio/opus"

class Extension:
    JPG = ".jpg"
    MP3 = ".mp3"
    OPUS = ".opus"

class Hydration:
    MEDIA_INDEX = 7
    HYDRATABLE = "hydratable"
    DATA = "data"

class Hydratable:
    SINGLE_TRACK = "sound"
    ALBUM_OR_PLAYLIST = "playlist"

# Regular Expression Patterns
class Regexp:
    CODEC = re.compile(r".*\"(.*)\"")
    RESERVED_CHARACTERS = re.compile(r"[\<\>\:\"\/\\\|\?\*]")
    HYDRATION = re.compile(r"<script>window.__sc_hydration = (\[.*\]);</script>")
    M3U = re.compile(r"http.*")
    ARTWORK = re.compile(r"((?:artworks|avatars)-.*-)(.*)(\.jpg)")
    CLIENTID = re.compile(r"client_id:\"([A-za-z0-9]+)\"")

# Translation Tables for str.translate() method
class Table:
    RESERVED_CHARACTERS = {
        58: 8758, # :
        60: 10877, # < (8804)
        62: 10878, # > (8805)
        34: 8221, # "
        92: 10745, # \
        47: 10744, # /
        124: 9474, # |  (124, 448, 9474, 2404)
        63: 11822, # ?
        42: 10033, # *
    }