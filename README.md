# SoundClouder

![SoundClouder Banner](https://github.com/l1asis/soundclouder/blob/main/images/banner.png)

[***SoundClouder***](https://github.com/1omka/soundclouder) is a library for downloading publicly available SoundCloud songs, playlists, albums or compilations and full user profiles. It also applies bundled **metadata** with tags, including album cover. Available formats are **MP3** and **OPUS**(sometimes not) with constant quality of **128kbps**. There is also support for both **HLS** & **Progressive** streams. 

## **Disclaimer**
Availability of metadata from SoundCloud API responses is directly depends on whether the author/uploader provides it, so it can be inaccurate. 

**For example**: there may be no album title, even if the song is in the album, so in such a situation SoundClouder will set the album title as the song title.

## **Installation**

SoundClouder was tested on [Python](https://python.org/downloads) 3.10 and depends on [mutagen](https://github.com/quodlibet/mutagen) (for metadata embedding) and [requests](https://github.com/psf/requests) libraries.

> With pip, where "." is a root soundclouder folder:
```
pip install .
```

## **Usage**
> Command-line interface:
```
soundclouder --help
```
```
soundclouder -u "https://soundcloud.com/rick-astley-official/never-gonna-give-you-up-4"
```
> In Python:
```python
>>> from soundclouder import SoundClouder
>>> from soundclouder import Stream
>>> SoundClouder(url="...", stream_type=Stream.MP3_HLS)
>>> # With path: (Default - Current Folder)
>>> SoundClouder(url="...", base_path="E:\Music")
>>> ....
```