from gtts import gTTS

def text_to_speech(text, output_file):
    tts = gTTS(text=text, lang='en')
    tts.save(output_file)

if __name__ == "__main__":
    sample_text = "The best way to get started is to quit talking and begin doing."
    text_to_speech(sample_text, "output.mp3")