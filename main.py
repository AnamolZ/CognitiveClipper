import requests
import time
import os

class AudioTranscriber:
    def __init__(self, api_key):
        self.api_key = api_key

    def transcribe_audio(self, audio_file_path):
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"The audio file {audio_file_path} does not exist.")
        
        upload_url = self.upload_audio(audio_file_path)
        transcription_id = self.request_transcription(upload_url)
        return self.poll_for_transcription(transcription_id)

    def upload_audio(self, audio_file_path):
        upload_endpoint = 'https://api.assemblyai.com/v2/upload'
        with open(audio_file_path, 'rb') as f:
            response = requests.post(upload_endpoint, headers={'authorization': self.api_key}, files={'file': f})
        response.raise_for_status()
        return response.json()['upload_url']

    def request_transcription(self, upload_url):
        transcription_endpoint = 'https://api.assemblyai.com/v2/transcript'
        transcription_payload = {'audio_url': upload_url}
        response = requests.post(transcription_endpoint, json=transcription_payload, headers={'authorization': self.api_key})
        response.raise_for_status()
        return response.json()['id']

    def poll_for_transcription(self, transcription_id):
        transcription_endpoint = f'https://api.assemblyai.com/v2/transcript/{transcription_id}'
        max_wait_time = 600
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            response = requests.get(transcription_endpoint, headers={'authorization': self.api_key})
            response_data = response.json()
            
            if response_data['status'] == 'completed':
                return response_data['text']
            elif response_data['status'] == 'error':
                raise Exception(f"Transcription failed: {response_data.get('error', 'Unknown error')}")
            
            time.sleep(5)  # wait before polling again
        
        raise TimeoutError('Transcription timed out')

if __name__ == '__main__':
    api_key = 'API_KEY'
    audio_file_path = 'AUDIO_FILE_PATH'

    transcriber = AudioTranscriber(api_key)
    try:
        transcription_text = transcriber.transcribe_audio(audio_file_path)
        print("Transcription:", transcription_text)
    except Exception as e:
        print(f"Error occurred: {e}")
