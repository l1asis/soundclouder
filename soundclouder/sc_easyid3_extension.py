import sys
import mutagen.id3

from mutagen.easyid3 import EasyID3

if __name__ == "__main__":
    sys.exit(0)

else:
    for key, frameid in {
        'picture': 'APIC',
        }.items():
        EasyID3.RegisterTextKey(key, frameid)

    def picture_get(id3, _):
        return [comment.data for comment in id3['APIC'].data]

    def picture_set(id3, _, value):
        id3.add(mutagen.id3.APIC(mime=u"image/jpeg", data=value))

    EasyID3.RegisterKey(key='picture', getter=picture_get, setter=picture_set)