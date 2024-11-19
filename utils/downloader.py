import yt_dlp
import os

class YouTubeDownloader:
    def __init__(self, url):
        self.url = url
        self.ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'bestaudio/best',
            'noplaylist': True,
            'merge_output_format': None,
        }

    def remove_existing_video(self, filename):
        if os.path.exists(filename):
            os.remove(filename)

    def download_video(self):
        try:
            self.remove_existing_video('video.m4a')
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([self.url])
            print("Download completed successfully!")
        except Exception as e:
            print(f"An error occurred: {e}")
