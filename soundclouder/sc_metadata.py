import base64
import mutagen.id3
from mutagen.easyid3 import EasyID3
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture
from mutagen.mp3 import EasyMP3

from soundclouder.sc_types import Tag, TagKey, Extension, MIME

class Metadata(object):
    """Metadata(artwork, data, playlist_title, track_number, total_track_number) -> `object`

        Args:
            artwork (artwork): bytes object containing picture of a track
            data (data): data returned by SoundCloud
            playlist_title (playlist_title): playlist/album title (if came from it)
            track_number (track_number): the song number in the album/playlist
            total_track_number (total_track_number): the total track number in the album/playlist

        Object that contains the metadata of the track depending on it's availability on SoundCloud
        and a method to write it into the track file.
    """
    def __init__(self, extension: str, artwork: bytes, data: dict, 
                    playlist_title: str | None, track_number: int, total_track_number: int) -> None:
        self.publisher_metadata = self.getPublisherMetadata(data)

        self.tags = {}
        self.tags.update(self.setArtwork(artwork, extension))
        self.tags.update(self.setTitle(data))
        self.tags.update(self.setTitleSortOrderKey(data))
        self.tags.update(self.setAlbum(data, playlist_title))
        self.tags.update(self.setGenre(data))
        self.tags.update(self.setTrackNumber(track_number, total_track_number))
        self.tags.update(self.setArtist(data))
        self.tags.update(self.setAlbumArtist())
        self.tags.update(self.setReleaseDate(data))
        self.tags.update(self.setPublisher())
        self.tags.update(self.setCopyright())

    def getPublisherMetadata(self, data) -> dict | None:
        """ Gets the special data about the track, which is not always available
            but gives more accurate data about the track, artist and album. """
        return data["publisher_metadata"]

    def setArtwork(self, artwork: bytes, extension) -> Tag.PICTURE_MP3 | Tag.PICTURE_OPUS: # APIC
        """ Sets the artwork/album cover tag """
        if extension == Extension.MP3:
            picture = artwork
            return {TagKey.PICTURE: picture}
        elif extension == Extension.OPUS:
            picture = Picture()
            picture.data = artwork
            picture.mime = MIME.JPG
            picture.type = 3
            picture = base64.b64encode(picture.write()).decode('ascii')
            return {TagKey.OGG_PICTURE: picture}


    def setTitle(self, data) -> Tag.STRING: # TIT2
        """ Sets the track title tag """
        if self.publisher_metadata:
            if "release_title" in self.publisher_metadata:
                title = self.publisher_metadata["release_title"]
            else:
                title = data["title"]
        else:
            title = data["title"]
        return {TagKey.TITLE: title}

    def setTitleSortOrderKey(self, data) -> Tag.STRING: # TSOT
        """ Sets the TSOT tag """
        title = data["title"]
        return {} # *NOT IMPLEMENTED*

    def setAlbum(self, data, playlist_title) -> Tag.STRING: # TALB
        """ Sets the album title tag """
        if self.publisher_metadata:
            if "album_title" in self.publisher_metadata:
                album = self.publisher_metadata["album_title"]
            else:
                if playlist_title:
                    album = playlist_title
                else:
                    album = data["title"]
        else:
            album = data["title"]
        return {TagKey.ALBUM: album}

    def setGenre(self, data) -> Tag.STRING: # TCON
        """ Sets the genre tag """
        if "genre" in data:
            genre = data["genre"]
            return {TagKey.GENRE: genre}
        else:
            return {}

    def setTrackNumber(self, track_number, total_track_number) -> Tag.STRING: # TRCK
        """ Sets the track number (#/total) tag """
        track_number = f"{track_number}/{total_track_number}"
        return {TagKey.TRACK_NUMBER: track_number}

    def setArtist(self, data) -> Tag.STRING: # TPE1 (main artist) SEPARATED BY '/', ';' or '//'
        """ Sets the track artist tag """
        if self.publisher_metadata:
            if "artist" in self.publisher_metadata:
                artist = self.publisher_metadata["artist"]
            else:
                splitted_title = data["title"].split("-")
                if len(splitted_title) > 1:
                    artist = splitted_title[0].strip()
                else:
                    artist = data["user"]["username"]
        else:
            artist = data["user"]["username"]
        return {TagKey.ARTIST: artist}
    
    def setAlbumArtist(self) -> Tag.STRING: # TPE2 (featured and other artists)
        """ Sets the album artist tag """
        return {TagKey.ALBUM_ARTIST: self.tags[TagKey.ARTIST]}

    def setReleaseDate(self, data) -> Tag.STRING: # TDRC
        """ Sets the release date tag """
        for release_date in ("release_date", "created_at", "display_date"):
            if release_date in data:
                date = data[release_date]
                return {TagKey.RELEASE_DATE: date}
        else:
            return {}

    def setPublisher(self) -> Tag.STRING | Tag.EMPTY: # TPUB
        """ Sets the publisher tag """
        if self.publisher_metadata:
            if "p_line_for_display" in self.publisher_metadata:
                publisher = self.publisher_metadata["p_line_for_display"]
                return {TagKey.PUBLISHER: publisher}
            else:
                return {}
        else:
            return {}

    def setCopyright(self) -> Tag.STRING | Tag.EMPTY: # TCOP
        """ Sets the copyright tag """
        if self.publisher_metadata:
            if "c_line_for_display" in self.publisher_metadata:
                copyright = self.publisher_metadata["c_line_for_display"]
                return {TagKey.COPYRIGHT: copyright}
            else:
                return {}
        else:
            return {}

    def writeMeta(self, filepath: str) -> None:
        """ Writes metadata to the track """
        file = mutagen.File(filepath, easy=True)
        filetype = type(file)
        if filetype == EasyMP3 or filetype == EasyID3:
            file.add_tags()

        for key, value in self.tags.items():
            if value:
                file[key] = value
        file.save()