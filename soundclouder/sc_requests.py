import requests
import json
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
        self.api_url = "https://api-v2.soundcloud.com/"
        self.cdn_url = "https://a-v2.sndcdn.com/"
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
        self.client_id = self.getClientID()

    def decodeResponse(self, response: requests.Response) -> str:
        """ Decodes `requests.Response` raw content using `utf-8` encoding to escape unicode-based problems """
        return response.content.decode("utf-8")

    def getHydration(self, url: str) -> list:
        """ Gets the so-called JSON object `Hydration`, which contains all the necessary data for downloading media """
        response = requests.get(url)
        hydration = json.loads(re.findall(Regexp.HYDRATION, response.content.decode('utf-8'))[0])
        return hydration

    def getStreamURL(self, transcodings: dict, stream_type: int) -> str:
        """ Gets the Stream/Download (HLS/Progressive) URL, returned by SoundCloud """
        stream_url = transcodings[stream_type]["url"]
        stream_params = {
            "client_id":self.client_id,
            "track_authorization":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJnZW8iOiJERSIsInN1YiI6IiIsInJpZCI6IjU3ZTJjNjNkLTZkMmYtNDNjMC04MmRjLTIwYzYzZmE4MDcxYSIsImlhdCI6MTY3OTE3NjgwMH0.f7_AHN6tV_Eyj1ohe6qctkslrBPl4bc-knAWLQRFZIs"
        }
        stream_response = requests.get(stream_url, params=stream_params, headers=self.base_headers)
        stream_response_url = json.loads(self.decodeResponse(stream_response))["url"]
        return stream_response_url

    def getM3UPlaylistURLs(self, transcodings: dict, stream_type: int) -> dict:
        """ Gets the M3U Playlist in case of HTTP Live Streaming (HLS) instead of Progressive download """
        stream_url = self.getStreamURL(transcodings, stream_type)
        m3u_playlist_response = requests.get(stream_url)
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
        response = requests.get(url, params=params, headers=self.base_headers)
        tracks = json.loads(self.decodeResponse(response))
        return tracks
    
    def getChunkedResponse(self, url) -> requests.Response:
        """ GET Request for streaming data """
        response = requests.get(url, stream=True)
        return response
    
    def getClientID(self) -> str:
        """ GET Request for retrieving client_id parameter """
        url = self.cdn_url + "assets/0-5fca5524.js"
        response = requests.get(url)
        client_id = re.search(Regexp.CLIENTID, self.decodeResponse(response)).group(1)
        return client_id
        