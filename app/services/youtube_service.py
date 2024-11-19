import os
import yt_dlp
import assemblyai as aai
from rich import print

class YouTubeService:
    def __init__(self, api_key, url):
        self.api_key = api_key
        self.url = url
        self.ydl_opts = {
            'outtmpl': 'video.%(ext)s',
            'format': 'bestaudio/best',
            'noplaylist': True,
            'merge_output_format': None,
        }
        aai.settings.api_key = self.api_key

    def remove_existing_video(self, filename):
        if os.path.exists(filename):
            os.remove(filename)

    def download_video(self):
        try:
            self.remove_existing_video('video.m4a')
            with yt
