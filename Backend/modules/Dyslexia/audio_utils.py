from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def preprocess_audio(input_path, output_path, silence_thresh=-40, min_silence_len=500):
    audio = AudioSegment.from_file(input_path)

    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh
    )

    if not nonsilent_ranges:
        # No speech detected, export original
        audio.export(output_path, format="wav")
        return

    start_trim = nonsilent_ranges[0][0]
    end_trim = nonsilent_ranges[-1][1]

    trimmed_audio = audio[start_trim:end_trim]
    trimmed_audio.export(output_path, format="wav")
