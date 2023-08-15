from flask import Flask, jsonify, request
import requests
import time

app = Flask(__name__)


TRAIN_API_BASE_URL = "http://20.244.56.144/train"
NUMBERS_API_BASE_URL = "http://localhost:3000/numbers"


def get_auth_token():
    auth_data = {
        "companyName": "Train Central",
        "ownerName": "Rahul",
        "rollNo": "1",
        "ownerEmail": "rahul@abc.edu",
        "accessCode": "FKDje"
    }
    response = requests.post(f"{TRAIN_API_BASE_URL}/auth", json=auth_data)
    return response.json()["access_token"]


def get_train_data(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{TRAIN_API_BASE_URL}/trains", headers=headers)
    return response.json()


def fetch_numbers_from_service(urls):
    numbers = set()
    for url in urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                numbers.update(data.get("numbers", []))
        except requests.exceptions.RequestException:
            pass
    return sorted(numbers)


@app.route('/trains', methods=['GET'])
def get_trains_with_numbers():
    auth_token = get_auth_token()
    train_data = get_train_data(auth_token)
    
    current_time = time.time()
    twelve_hours_later = current_time + 12 * 60 * 60
    
    valid_trains = []
    for train in train_data:
        departure_time = train["departureTime"]
        departure_seconds = (departure_time["Hours"] * 3600 +
                             departure_time["Minutes"] * 60 +
                             departure_time["Seconds"])
        if current_time + 1800 < departure_seconds < twelve_hours_later:
            valid_trains.append(train)
    
    valid_trains.sort(key=lambda x: (x["price"]["sleeper"], 
                                     -x["seatsAvailable"]["sleeper"], 
                                     -x["departureTime"]["Hours"]*60 - x["departureTime"]["Minutes"]))
    

    number_urls = request.args.getlist('url')
    merged_numbers = fetch_numbers_from_service(number_urls)
    
    response_data = {
        "trains": valid_trains,
        "numbers": merged_numbers
    }
    return jsonify(response_data)

if __name__ == '__main__':
  app.run(debug=True)