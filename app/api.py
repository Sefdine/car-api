from flask import Flask, render_template, request
import speech_recognition as sr
from gtts import gTTS

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    # Use SpeechRecognition to convert audio to text
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.listen(source)
    
    user_input = recognizer.recognize_google(audio)
    
    # TODO: Use user_input to interact with car API and get a response
    
    # Dummy response for now
    car_response = "Your car is parked in the garage."

    # Convert the car response to speech
    tts = gTTS(car_response, lang='en')
    tts.save("response.mp3")

    return render_template('index.html', response=car_response)

if __name__ == '__main__':
    app.run(debug=True)
