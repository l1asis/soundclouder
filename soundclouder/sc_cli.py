import argparse

def cli():
    """ Simple `argparse` command-line interface """
    from soundclouder import SoundClouder
    parser = argparse.ArgumentParser(prog="soundclouder",
                            description="This tool/library is capable of downloading non-Go SoundCloud songs/playlists")
    parser.add_argument("-u", "--url", dest="url", type=str, required=True, 
                        help="song/album/playlist URL")
    parser.add_argument("-s", "--stream-type", dest="stream_type", choices=range(0,3), type=int, default=0, 
                        help="Stream Type: 0 - MP3 HLS, 1 - MP3 Progressive, 2 - OPUS HLS")
    parser.add_argument("-o", "--output", dest="output", type=str, default=".", 
                        help="Output path (default: current folder)")
    parser.add_argument("-r", "--replace-characters", dest="replace_characters", default=False, action="store_true",
                         help="Whether to replace reserved characters in file names to their unicode alternatives")
    # *NOT IMPLEMENTED*
    #parser.add_argument("-l", "--logging", dest="logging", action="store_true", default=False, help="Enable logging (default: disabled)")
    args = parser.parse_args()
    SoundClouder(url=args.url, base_path=args.output, stream_type=args.stream_type, replace_characters=args.replace_characters)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    cli()