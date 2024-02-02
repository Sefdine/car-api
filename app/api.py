from flask import Flask, render_template, jsonify
import speech_recognition as sr
from gtts import gTTS
from pygame import mixer
from pymongo import MongoClient
from geopy.geocoders import Nominatim

app = Flask(__name__)

# Connect to MongoDB
mongo_client = MongoClient('localhost', 27017)
mongo_db = mongo_client['cars_db']
mongo_collection = mongo_db['cars_collection']

# Initialize the mixer for audio playback
mixer.init()

# Initialize geopy Nominatim for reverse geocoding
geolocator = Nominatim(user_agent="reverse_geocoding_example")

# Cache for storing geocoding results
geocode_cache = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    # Retrieve all documents from MongoDB collection
    car_data = list(mongo_collection.find())

    # Convert ObjectId to string for JSON serialization
    for car in car_data:
        car['_id'] = str(car['_id'])

    # Return the data as JSON response
    return jsonify(car_data)

@app.route('/process_audio', methods=['GET', 'POST'])
def process_audio():
    # Use SpeechRecognition to convert audio to text
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something:")
        try:
            audio = recognizer.listen(source, timeout=5)  # Adjust timeout as needed
            user_input = recognizer.recognize_google(audio)
            print(f"Recognized: {user_input}")

            # Retrieve the latest document from MongoDB
            latest_doc = mongo_collection.find_one(sort=[('_id', -1)])

            if latest_doc:
                # Extract latitude and longitude from the latest document
                latitude = round(float(latest_doc.get('Latitude', 'N/A')), 4)
                longitude = round(float(latest_doc.get('Longitude', 'N/A')), 2)

                # Check if result is already in cache
                cache_key = (latitude, longitude)
                if cache_key in geocode_cache:
                    country = geocode_cache[cache_key]
                else:
                    # Perform reverse geocoding to get the country
                    location = geolocator.reverse((latitude, longitude), language='en')
                    if location and 'address' in location.raw:
                        country = location.raw['address'].get('country', 'N/A')
                        # Cache the result for future use
                        geocode_cache[cache_key] = country
                    else:
                        country = None

                if not country:
                     # Create the response string
                    car_response = f"Your car is lost at latitude{round(latitude, 2)} and longitude {round(longitude, 2)}."
                else:
                    # Create the response string
                    car_response = f"Your car is currently in {country}."

                # Convert the car response to speech
                tts = gTTS(car_response, lang='en')
                tts.save("response.mp3")

                # Play the audio response
                mixer.music.load("response.mp3")
                mixer.music.play()

            else:
                car_response = "No location data available."

            # Pass user_input and car_response to the template
            return render_template('index.html', user_input=user_input, car_response=car_response)
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
            return render_template('index.html', user_input="Unknown", car_response="Could not understand audio")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            return render_template('index.html', user_input="Error", car_response="Error communicating with speech recognition service")

if __name__ == '__main__':
    app.run(debug=True)
