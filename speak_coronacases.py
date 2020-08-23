import requests
import json
import speech_recognition as sr
import pyttsx3
import re
import threading
import time


API_KEY = "tzpwYznOc5Fg"
PROJECT_TOKEN = "t5A6emFrTZWN"
RUN_TOKEN = "thqBsQ1iY4As"

class Data:
    def __init__(self, api_key, project_token):
        self.api_key = api_key
        self.project_token = project_token
        self.params = {"api_key": self.api_key}
        self.data = self.get_data()
        
    def get_data(self):
        response = requests.get(f'https://www.parsehub.com/api/v2/projects/{PROJECT_TOKEN}/last_ready_run/data', params={"api_key": API_KEY})
        data = json.loads(response.text)
        return data

    def get_total_cases(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Coronavirus Cases:":
                return content['values']

    def get_total_deaths(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Deaths:":
                return content['values']

    def get_total_recovered(self):
        data = self.data['total']

        for content in data:
            if content['name'] == "Recovered:":
                return content['values']

    def get_country_data(self, country):
        data = self.data['country']

        for content in data:
            if content['name'].lower() == country.lower():
                return content

        return "0"

    def get_list_of_countries(self):
        countries = [country['name'] for country in self.data['country']]

        return countries

    def update_data(self):
        response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.project_token}/run', params=self.params)

        def poll():
            time.sleep(0.1)
            # this allows the other thread i.e. the thread that is running the voice assistant still run while the other thread is also running
            old_data = self.data
            while True:
                new_data = self.get_data()
                if new_data != old_data:
                    self.data = new_data
                    print("Data updated")
                    break
                time.sleep(5)

        t = threading.Thread(target=poll)
        t.start()


def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

# speak("hello")


def get_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
        said = ""

        try:
            said = r.recognize_google(audio)
        except Exception as e:
            print("Exception: ", str(e))

    return said.lower()


def main():
    data = Data(API_KEY, PROJECT_TOKEN)
    print("Started Recognizer")
    END_PHRASE = "exit"
    country_list = data.get_list_of_countries()

    TOTAL_PATTERNS = {
        re.compile(r".* total .* cases"): data.get_total_cases,
        re.compile(r".* total cases"): data.get_total_cases,
        re.compile(r".* total .* cases"): data.get_total_deaths,
        re.compile(r".* total deaths"): data.get_total_deaths,
        re.compile(r".* total .* recovered"): data.get_total_recovered,
        re.compile(r".* total recovered"): data.get_total_recovered,
    }

    COUNTRY_PATTERNS = {
        re.compile(r".* cases .*"): lambda country: data.get_country_data(country)['total_cases'],
        re.compile(r".* deaths .*"): lambda country: data.get_country_data(country)['total_deaths'],
        re.compile(r".* recovered .*"): lambda country: data.get_country_data(country)['total_recovered'],
    }

    UPDATE_COMMAND = "update"

    while True:
        print("Listening")
        text = get_audio()
        result = None
        print(text)


        if text.find(END_PHRASE) != -1:
            print("Exiting")
            speak("Exiting")
            break
        
        if text.find(UPDATE_COMMAND) != -1:
            print("Data is being updated. This may take a moment!")
            data.update_data()


        for patterns, func in TOTAL_PATTERNS.items():
            # print("Entered loop for total patterns")
            if patterns.match(text):
                # print("match found in total")
                result = func()
                break
        
        for patterns, func in COUNTRY_PATTERNS.items():
            # print("Entered loop")
            if patterns.match(text):
                # print("Match found in country")
                words = set(text.split())
                for country in country_list:
                    if country.lower() in words:
                        result = func(country)
                        break

        if result:
            print(result)
            speak(result)

main()