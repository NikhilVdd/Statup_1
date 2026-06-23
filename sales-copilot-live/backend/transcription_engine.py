def process_audio_chunk(audio_data):
    # Future integration point: stream this chunk to Deepgram, AssemblyAI, Whisper, or OpenAI STT.
    return {
        "status": "received",
        "bytes_received": len(str(audio_data)),
        "message": "Audio chunk accepted by mock transcription pipeline.",
    }


def mock_transcribe_audio(audio_data):
    # Demo placeholder until live microphone or phone-call audio is connected.
    return "Mock transcript text from a future streaming speech-to-text provider."
