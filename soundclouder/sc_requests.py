import requests
import json
import time
import re

from soundclouder.sc_types import Regexp

class Requests(object):
    """Requests(user_agent) -> `object`

        Args:
            user_agent (user_agent): `User-Agent` header for the requests
                Default: `Mozilla/5.0 (Linux; x86)`

        Object that contains the `GET` requests methods used by SoundClouder
    """
    def __init__(self, user_agent="Mozilla/5.0 (Linux; x86)") -> None:
        self.session = requests.Session()
        self.api_url = "https://api-v2.soundcloud.com/"
        self.base_headers = {
            "Host": "api-v2.soundcloud.com",
            "User-Agent": user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://soundcloud.com/",
            "Origin": "https://soundcloud.com",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

    def closeSession(self) -> None:
        """ In the end, it is preferable to close the persistent HTTP connection """
        self.session.close()

    def decodeResponse(self, response: requests.Response) -> str:
        """ Decodes `requests.Response` raw content using `utf-8` encoding to escape unicode-based problems """
        return response.content.decode("utf-8")

    def dumpObject(self, obj) -> None:
        """ Function for quickly storing JSON dictionaries or regular strings """
        with open("./sc_dump", "wt") as file:
            if isinstance(obj, dict) or isinstance(obj, list):
                json.dump(obj, file, indent=" "*4)
            elif isinstance(obj, requests.Response):
                file.write(self.decodeResponse(obj))
            elif isinstance(obj, str):
                file.write(obj)

    def getHydration(self, url: str) -> list[dict]:
        """ Gets the so-called JSON object `Hydration`, which contains all the necessary data for downloading media """
        response = self.session.get(url)
        hydration = json.loads(re.findall(Regexp.HYDRATION, response.content.decode('utf-8'))[0])
        self.client_id = self.getClientID(response)
        return hydration

    def getStreamURL(self, transcodings: dict, stream_type: int) -> str:
        """ Gets the Stream/Download (HLS/Progressive) URL, returned by SoundCloud """
        stream_url = transcodings[stream_type]["url"]
        stream_params = {
            "client_id":self.client_id,
            "track_authorization":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJnZW8iOiJERSIsInN1YiI6IiIsInJpZCI6IjU3ZTJjNjNkLTZkMmYtNDNjMC04MmRjLTIwYzYzZmE4MDcxYSIsImlhdCI6MTY3OTE3NjgwMH0.f7_AHN6tV_Eyj1ohe6qctkslrBPl4bc-knAWLQRFZIs"
        }
        stream_response = self.session.get(stream_url, params=stream_params, headers=self.base_headers)
        stream_response_url = json.loads(self.decodeResponse(stream_response))["url"]
        return stream_response_url

    def getM3UPlaylistURLs(self, transcodings: dict, stream_type: int) -> list[str]:
        """ Gets the M3U Playlist in case of HTTP Live Streaming (HLS) instead of Progressive download """
        stream_url = self.getStreamURL(transcodings, stream_type)
        m3u_playlist_response = self.session.get(stream_url)
        m3u_urls = re.findall(Regexp.M3U, self.decodeResponse(m3u_playlist_response))
        return m3u_urls

    def getTracksByIDs(self, ids: str) -> list:
        """ Gets the track(s) data depending on the id(s) """
        url = self.api_url + "tracks"
        params = {
            "ids":ids,
            "client_id":self.client_id,
            "[object Object]":"",
            "app_version":"1679652891",
            "app_locale":"en",
        }
        response = self.session.get(url, params=params, headers=self.base_headers)
        tracks = json.loads(self.decodeResponse(response))
        return tracks
    
    def getTrackCollectionByUser(self, user, is_likes):
        """ Gets the tracks data dumping the whole user profile """
        userid = user["id"]
        #last_modified = user["last_modified"][:-1] + ".000Z" # `[:-1]` removes the last 'Z' literal
        #timestamp = f"0{int(time.time())}"
        offset = "0" # ",".join((last_modified, "tracks", timestamp))

        if is_likes:
            url = f"{self.api_url}users/{userid}/likes"
        elif not is_likes:
            url = f"{self.api_url}stream/users/{userid}"

        params = {
            "client_id": self.client_id,
            "limit": 80000,
            "offset": offset,
            "linked_partitioning": "1",
            "app_version": "1682677411",
            "app_locale": "en",
        }
        response = self.session.get(url, params=params, headers=self.base_headers)
        collection = json.loads(self.decodeResponse(response))["collection"]
        return collection

    
    def getChunkedResponse(self, url) -> requests.Response:
        """ GET Request for streaming data """
        response = self.session.get(url, stream=True)
        return response
    
    def getClientID(self, response) -> str:
        """ GET Request for retrieving client_id parameter """
        urls = re.findall(Regexp.CLIENTID_SCRIPT_URL, self.decodeResponse(response))
        for url in urls:
            script_response = self.session.get(url)
            client_id = re.search(Regexp.CLIENTID, self.decodeResponse(script_response)) # .group(1)
            if client_id:
                return client_id.group(1)
        else:
            raise Exception("[ERR] SoundCloud `client_id` was not found:(")
