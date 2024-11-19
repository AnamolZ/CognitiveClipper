import os
import assemblyai as aai
from utils.downloader import YouTubeDownloader

class YouTubeTranscriber:
    def __init__(self, api_key, url):
        self.api_key = api_key
        self.url = url
        aai.settings.api_key = self.api_key
        self.downloader = YouTubeDownloader(self.url)

    def remove_existing_video(self, filename):
        if os.path.exists(filename):
            os.remove(filename)

    def download_video(self):
        self.downloader.download_video()

    def transcribe_video(self, filename):
        if not os.path.exists(filename):
            print(f"File {filename} not found.")
            return ""
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(filename)
        return transcript.text
