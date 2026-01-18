import whisper

model = whisper.load_model("small")

def transcribe_with_timestamps(audio_path):
    # ### UPDATED: Added language="en" to force English
    result = model.transcribe(
        audio_path,
        word_timestamps=True,
        verbose=False,
        language="en" 
    )

    words = []
    for segment in result["segments"]:
        for w in segment["words"]:
            words.append({
                "word": w["word"],
                "start": round(w["start"], 2),
                "end": round(w["end"], 2)
            })

    return {
        "transcribed_text": result["text"].strip(),
        "word_timestamps": words
    }