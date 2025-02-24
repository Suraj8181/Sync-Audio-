import streamlit as st
import whisper
import tempfile
import ffmpeg
import os

# Function to convert seconds to SRT time format
def format_time(seconds):
    millisec = int((seconds % 1) * 1000)
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02},{millisec:03}"

st.title("🎵 AI-Based Audio-SRT Sync Tool")
st.write("Upload your **Audio + SRT** file to get perfectly synced audio.")

# Upload audio & subtitle files
audio_file = st.file_uploader("Upload Audio File (MP3/WAV)", type=["mp3", "wav"])
srt_file = st.file_uploader("Upload Subtitle File (SRT)", type=["srt"])

if audio_file and srt_file:
    st.success("✅ Files uploaded successfully! Processing...")

    # Save uploaded files as temp files
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        temp_audio.write(audio_file.read())
        temp_audio_path = temp_audio.name

    with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as temp_srt:
        temp_srt.write(srt_file.read())
        temp_srt_path = temp_srt.name

    # Load Whisper Model
    model = whisper.load_model("base")

    # Convert MP3 to WAV
    wav_audio_path = temp_audio_path.replace(".mp3", ".wav")
    try:
        st.info("🔄 Converting MP3 to WAV...")
        ffmpeg.input(temp_audio_path).output(wav_audio_path, ar=16000, ac=1).run(overwrite_output=True)
        st.success("✅ Conversion Successful!")
    except Exception as e:
        st.error(f"⚠️ FFmpeg conversion failed: {e}")
        st.stop()

    # Transcribe audio with Whisper
    st.info("🎙️ Transcribing Audio...")
    result = model.transcribe(wav_audio_path)

    # Generate Synced SRT
    synced_srt_path = temp_srt_path.replace(".srt", "_synced.srt")
    with open(synced_srt_path, "w") as synced_srt:
        for idx, segment in enumerate(result["segments"], start=1):
            start_time = format_time(segment['start'])
            end_time = format_time(segment['end'])
            synced_srt.write(f"{idx}\n{start_time} --> {end_time}\n{segment['text']}\n\n")

    # Display synced subtitle preview
    st.text("📜 Synced Subtitle Preview:")
    with open(synced_srt_path, "r") as f:
        st.code(f.read(), language="srt")

    # Generate Synced Audio using FFmpeg
    synced_audio_path = temp_audio_path.replace(".mp3", "_synced.mp3")
    try:
        st.info("🎵 Generating Synced Audio...")
        (
            ffmpeg
            .input(wav_audio_path)
            .filter("subtitles", synced_srt_path)
            .output(synced_audio_path)
            .run(overwrite_output=True)
        )
        st.success("✅ Synced Audio Ready!")
    except Exception as e:
        st.error(f"⚠️ FFmpeg Audio Sync Failed: {e}")
        st.stop()

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
