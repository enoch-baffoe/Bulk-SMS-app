import requests
def sendSMS(message,phoneNumbers):
    endPoint = 'https://api.mnotify.com/api/sms/quick'
    apiKey = 'nY32mlBDbgITrxHlFzt507UgynPxpb8N9bPwxq9IHRC8p'
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