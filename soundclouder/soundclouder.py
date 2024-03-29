import mimetypes
import multiprocessing
import os
import re
from urllib.parse import urlparse

# EasyID3 Extension for APIC support
import soundclouder.sc_easyid3_extension

from soundclouder.sc_metadata import Metadata
from soundclouder.sc_requests import Requests
from soundclouder.sc_types import *


class SoundClouder:
    """SoundClouder(url, base_path=".", stream_type=0, replace_characters=True) -> `None`

        Args:
            url (url): link to the track/playlist/album/set/profile on SoundCloud
            base_path (base_path): path to the folder in which the media files will be saved
                Default value: `"." - Current folder`
            stream_type (stream_type): type of the stream, affects the file format.
                Possible values: `0 - MP3 HLS`, `1 - MP3 Progressive`, `2 - OPUS HLS`
                Default value: `0`
            replace_characters (replace_characters): whether to replace reserved characters in file names
            with their unicode alternatives (title in metadata remains untouched)
                Default value: `True`

        Scrapes the initial track/playlist/album data and downloads the media.
    """
    def __init__(self, url: str, base_path=Path.CURRENT_FOLDER, stream_type=Stream.MP3_HLS, replace_characters=False) -> None:
        self.req = Requests()
        self.hydration = self.req.getHydration(self.validateURL(url))
        if len(self.hydration) >= 8:
            self.hydratable = self.hydration[Hydration.MEDIA]["hydratable"]
            self.data = self.hydration[Hydration.MEDIA]["data"]
        else:
            self.hydratable = self.hydration[Hydration.USER]["hydratable"]
            self.data = self.hydration[Hydration.USER]["data"]
            self.is_likes = True if url.endswith("likes") else False
        self.base_path = base_path
        self.stream_type = stream_type
        self.replace_characters = replace_characters

        if self.hydratable == Hydratable.SINGLE_TRACK:
            self.downloadTrack(self.data, self.base_path)
        elif self.hydratable == Hydratable.ALBUM_OR_PLAYLIST:
            self.downloadAlbumOrPlaylist(self.data, self.base_path)
        elif self.hydratable == Hydratable.USER:
            self.downloadUserProfile(self.data, self.base_path, self.is_likes)
        self.req.closeSession()

    def validateURL(self, url: str) -> str:
        result = urlparse(url)
        if result.scheme == "https" and result.netloc == "soundcloud.com":
            result = result._replace(params="", query="")
            return result.geturl()
        raise Exception("[ERR] The specified URL is incorrect.")
        
    def createFolder(self, name: str, base_path: str) -> str:
        path = os.path.join(base_path, name)
        if not os.path.exists(path):
            os.mkdir(path)
        return path
    
    def correctMIMEType(self, string: str) -> str:
        """ Corrects MIME type, because MIME of `.opus` format returned by SoundCloud as `audio/ogg; codecs=\"opus\"`
        instead of `audio/opus`"""
        splitted = string.split(";")
        if len(splitted) > 1:
            mimetype = splitted[0].strip()
            mimetype = mimetype.split("/")
            codec = splitted[1].strip()
            codec = re.sub(Regexp.CODEC, "\g<1>", codec)
            mimetype = f"{mimetype[0]}/{codec}"
        else:
            mimetype = splitted[0].strip()
        return mimetype
    
    def getExtension(self, mimetype) -> str:
        """ Guesses an extension by MIME type"""
        extension = mimetypes.guess_extension(mimetype)
        return extension

    def downloadTrack(self, data, base_path, playlist_title=None, track_number=1, total_track_number=1, mode=(Internal.DEFAULT, None)) -> None:
        """ Downloads a single track """
        if mode[0] == Internal.LOG_ID:
            mode[1].append(data["id"])
        elif mode[0] == Internal.CHECK_ID:
            if data["id"] in mode[1]:
                return

        artwork = self.downloadArtwork(data, (300,300))
        transcodings = data["media"]["transcodings"]
        if not transcodings:
            print(f"[-] Song \'{data['title']}\' is not available in your country or an error has occurred.")
            return None
        mimetype = self.correctMIMEType(transcodings[self.stream_type]["format"]["mime_type"])
        extention = self.getExtension(mimetype)
        meta = Metadata(extention, artwork, data, playlist_title, track_number, total_track_number)
        if self.replace_characters:
            filename = f"{self.replaceReservedCharacters(meta.tags[TagKey.TITLE])}{extention}"
        else:
            filename = f"{self.removeReservedCharacters(meta.tags[TagKey.TITLE])}{extention}"
        path = os.path.join(base_path, filename)

        chunk_size = 256
        if self.stream_type == Stream.MP3_HLS or self.stream_type == Stream.OPUS_HLS:
            m3u_urls = self.req.getM3UPlaylistURLs(transcodings, self.stream_type)
            with open(path, "wb") as fd:
                for url in m3u_urls:
                    response = self.req.getChunkedResponse(url)
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        fd.write(chunk)

        elif self.stream_type == Stream.MP3_PROGRESSIVE:
            url = self.req.getStreamURL(transcodings, self.stream_type)
            with open(path, "wb") as fd:
                response = self.req.getChunkedResponse(url)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    fd.write(chunk)

        meta.writeMeta(filepath=path)

    def downloadAlbumOrPlaylist(self, data, base_path, mode=(Internal.DEFAULT, None)) -> None:
        """ Downloads all tracks from an album/playlist/set """
        playlist_title = data["title"]
        if self.replace_characters:
            playlist_path = self.createFolder(self.replaceReservedCharacters(playlist_title), base_path)
        else:
            playlist_path = self.createFolder(self.removeReservedCharacters(playlist_title), base_path)
        ids_to_track_numbers = {track["id"]: track_number for track_number, track in enumerate(data["tracks"], start=1)}
        ids = list(map(str, ids_to_track_numbers.keys()))
        tracks = []
        offset = 50 # SoundCloud API `tracks` accepts only 50 ids per time
        while ids:
            tracks.extend(self.req.getTracksByIDs(",".join(ids[:offset])))
            del ids[:offset]
        total_track_number = len(tracks)
        
        tasks = [[track, # dict, that contains data of one track
                  playlist_path, # setting the `base_path` as playlist_path
                  playlist_title, # setting playlist title for certain data in meta
                  ids_to_track_numbers[track["id"]], # number of track in album/set/playlist
                  total_track_number, # total track number in album/set/playlist
                  mode] # decide whether to log track IDs
                  for track in tracks] # iterate through the list of all tracks

        with multiprocessing.Pool() as pool:
            pool.starmap(self.downloadTrack, tasks)

    def downloadUserProfile(self, data, base_path, is_likes):
        """ Downloads all tracks/albums/playlists/sets/reposts from an user profile """
        username = data["username"]
        if self.replace_characters:
            user_path = self.createFolder(self.replaceReservedCharacters(username), base_path)
        else:
            user_path = self.createFolder(self.removeReservedCharacters(username), base_path)

        if is_likes:
            user_path = self.createFolder("likes", user_path)
        
        with multiprocessing.Manager() as manager:
            tracker = manager.list()
            single_tracks = []
            collection = self.req.getTrackCollectionByUser(data, is_likes)
            for container in collection:
                container_type = container["type"] if not is_likes else container["kind"]
                if container_type == Hydratable.ALBUM_OR_PLAYLIST:
                    playlist = container["playlist"]
                    self.downloadAlbumOrPlaylist(playlist, user_path, (Internal.LOG_ID, tracker))
                elif container_type in Hydratable.USER_TRACKS:
                    track = container["track"]
                    single_tracks.append(track)
            with multiprocessing.Pool() as pool:
                tasks = [[track, user_path, None, 1, 1, (Internal.CHECK_ID, tracker)] for track in single_tracks]
                pool.starmap(self.downloadTrack, tasks)
    
    def downloadArtwork(self, data: dict, size: tuple) -> bytes:
        """ Downloads an artwork/album cover of a track """
        url = data["artwork_url"]
        if not url:
            url = data["user"]["avatar_url"]
        url = re.sub(Regexp.ARTWORK, "\g<1>t{0}x{1}\g<3>".format(*size), url)
        response = self.req.getChunkedResponse(url)
        artwork = response.raw.read()
        return artwork

    def replaceReservedCharacters(self, string: str) -> str:
        """ Translates reserved characters in a string to their unicode alternatives """
        string = string.translate(Table.RESERVED_CHARACTERS)
        return string

    def removeReservedCharacters(self, string: str) -> str:
        """ Removes reserved characters in a string """
        string = re.sub(Regexp.RESERVED_CHARACTERS, "", string)
        return string