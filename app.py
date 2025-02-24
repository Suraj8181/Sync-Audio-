import streamlit as st
import whisper
import tempfile
import ffmpeg
import os
import shutil

# Ensure FFmpeg is installed
FFMPEG_PATH = "/usr/bin/ffmpeg"
if not os.path.exists(FFMPEG_PATH):
    st.error("FFmpeg not found! Try deploying on Hugging Face Spaces.")

# Streamlit Web App UI
st.title("🎵 AI-Based Audio-SRT Sync Tool")
st.write("Upload your **Audio + SRT** file to get perfectly synced audio.")

# File Upload
audio_file = st.file_uploader("Upload Audio File (MP3/WAV)", type=["mp3", "wav"])
srt_file = st.file_uploader("Upload Subtitle File (SRT)", type=["srt"])

if audio_file and srt_file:
    st.success("✅ Files uploaded successfully! Processing...")

    # Save Uploaded Files Temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(audio_file.read())
        temp_audio_path = temp_audio.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_srt:
        temp_srt.write(srt_file.read())
        temp_srt_path = temp_srt.name

    # Load Whisper Model
    model = whisper.load_model("base")
    
    # Convert audio to WAV format (Whisper needs WAV input)
    wav_audio_path = temp_audio_path.replace(".mp3", ".wav")
    os.system(f"ffmpeg -i {temp_audio_path} -ar 16000 -ac 1 {wav_audio_path}")

    # Process Audio through AI
    result = model.transcribe(wav_audio_path)

    # Generate Synced SRT
    synced_srt_path = temp_srt_path.replace(".srt", "_synced.srt")
    with open(synced_srt_path, "w") as synced_srt:
        for segment in result["segments"]:
            synced_srt.write(f"{segment['start']} --> {segment['end']}\n{segment['text']}\n\n")

    # Generate Synced Audio using FFmpeg
    synced_audio_path = temp_audio_path.replace(".mp3", "_synced.mp3")
    os.system(f"ffmpeg -i {wav_audio_path} -vf \"subtitles={synced_srt_path}\" {synced_audio_path}")

    # Provide Download Link
    st.audio(synced_audio_path)
    with open(synced_audio_path, "rb") as f:
        st.download_button("📥 Download Synced Audio", f, file_name="synced_audio.mp3")

    st.success("✅ Processing Completed! Download your synced audio.")

    # Cleanup Temp Files
    os.remove(temp_audio_path)
    os.remove(temp_srt_path)
    os.remove(wav_audio_path)
    os.remove(synced_audio_path)
