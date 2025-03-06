import requests
import os
import time

# Fetch the OpenWeather API key and Telegram API key from environment variables
OWM_API_KEY = os.getenv('OWM_API_KEY')
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
OWM_URL = 'https://api.openweathermap.org/data/2.5/weather'

# Check if the API keys were successfully retrieved
if OWM_API_KEY is None:
    print("Error: OpenWeather API key is not set.")
    exit(1)  # Exit the program if the OpenWeather API key is missing

if TELEGRAM_API_KEY is None:
    print("Error: Telegram API key is not set.")
    exit(1)  # Exit the program if the Telegram API key is missing

# Function to get updates from the bot
def get_updates(token):
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url)
    
    if response.status_code == 200:
        return response.json()['result']
    else:
        print(f"Error fetching updates: {response.status_code}")
        return []

# Function to send a message back to the chat
def send_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Error sending message: {response.status_code}, {response.text}")

# Function to get weather information for a city from OpenWeather API
def get_weather(city_name):
    params = {
        'q': city_name,
        'appid': OWM_API_KEY,
        'units': 'metric',  # Use 'imperial' for Fahrenheit
        'lang': 'en'  # Language for the weather response
    }
    
    response = requests.get(OWM_URL, params=params)
    
    # Debugging: Print the response from OpenWeather API
    print(f"OpenWeather API response: {response.json()}")  # Check the entire response

    if response.status_code == 200:
        data = response.json()
        if data['cod'] == 200:
            # Extract required weather details
            weather_description = data['weather'][0]['description']
            temperature = data['main']['temp']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            
            # Check if rain is expected
            rain_expected = "rain" in [weather['main'].lower() for weather in data['weather']]
            rain_message = ""
            
            # If rain is expected, send an additional message
            if rain_expected:
                rain_message = "⚠️ Rain is expected in this city. Please take necessary precautions."

            # Create a formatted message
            weather_message = (
                f"Weather in {city_name}:\n"
                f"Description: {weather_description.capitalize()}\n"
                f"Temperature: {temperature}°C\n"
                f"Humidity: {humidity}%\n"
                f"Wind Speed: {wind_speed} m/s\n"
                f"{rain_message}"  # Include the rain message if applicable
            )
            return weather_message
        else:
            return "City not found. Please check the spelling or try again with a valid city name."
    else:
        return "Error fetching weather data."

# Function to handle incoming messages and respond only to the latest message after the script started
def mirror_messages(token):
    print("Bot is running. Send a city name to get the current weather.")
    
    # Record the start time of the script
    script_start_time = time.time()
    
    interacted_users = set()  # A set to store user IDs that interacted with the bot
    latest_message_id = None  # To track the last message the bot has replied to

    while True:
        updates = get_updates(token)
        
        for update in updates:
            chat_id = update['message']['chat']['id']
            text = update['message']['text']
            user_id = update['message']['from']['id']
            message_id = update['message']['message_id']  # Get the ID of the message
            message_timestamp = update['message']['date']  # Get the timestamp of the message

            # Ignore messages sent before the script started
            if message_timestamp < script_start_time:
                continue  # Skip this message, as it's older than the script start time
            
            # Add the user to the set of interacted users
            interacted_users.add(user_id)
            
            # Print the user ID for debugging purposes
            print(f"Received message from user ID: {user_id}, message: {text}, message_id: {message_id}")
            
            # Only respond to the latest message from any user in interacted_users
            if user_id in interacted_users and (latest_message_id is None or message_id > latest_message_id):
                # Get the weather info or provide error if city is incorrect
                weather_info = get_weather(text)
                send_message(token, chat_id, weather_info)  # Send the weather data
                latest_message_id = message_id  # Update the latest message ID
                print(f"Replied to message: {text}")

        # Wait for 3 seconds before checking for new updates again
        time.sleep(3)

# Start the bot to respond only to the latest message
mirror_messages(TELEGRAM_API_KEY)
