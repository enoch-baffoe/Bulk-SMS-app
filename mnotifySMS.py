import requests
import os
from dotenv import load_dotenv

load_dotenv()
apiKey = os.environ.get('API_KEY')

def sendSMS(message,phoneNumbers):
    endPoint = 'https://api.mnotify.com/api/sms/quick'
    data = {
    'recipient[]': phoneNumbers,
    'sender': 'MOCWO',
    'message': message,
    'is_schedule': False,
    'schedule_date': ''
    }
    url = endPoint + '?key=' + apiKey
    response = requests.post(url, data)
    data = response.json()
    print (data,flush=True)
    return data
    

def getBalance():
    endPoint = 'https://api.mnotify.com/api/balance/sms'
    url = endPoint + '?key=' + apiKey
    response = requests.get(url)
    print(response)
    data = response.json()
    return data
