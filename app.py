from flask import Flask, render_template, request
import requests
import json
import pandas as pd
import numpy as np
import pandas_gbq
from google.cloud import bigquery
from google.oauth2 import service_account

app = Flask(__name__)

# Replace YOUR_API_KEY with your own Geolocation API key
api_key = 'AIzaSyCKNHFdNnZD67DhBHblNxeFRLcqd2mMwso'

key_path = r"C:\Users\user\Downloads\ev-charge-station-381513-91e94e41baf7.json"
credentials = service_account.Credentials.from_service_account_file(key_path)


# Replace PROJECT_ID and DATASET_NAME with your own project ID and dataset name
project_id = 'ev-charge-station-381513'
dataset_id = 'USA_EV_Charging'
table_name = 'Charge_station_data2`'
client = bigquery.Client(credentials=credentials, project=project_id)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/locate', methods=['POST'])
def locate():
    # Send a request to the Geolocation API to get the user's location
    url = 'https://www.googleapis.com/geolocation/v1/geolocate?key=' + api_key
    response = requests.post(url)
    location = json.loads(response.content.decode('utf-8'))

    # Get the latitude and longitude values from the response
    user_lat = location['location']['lat']
    user_long = location['location']['lng']

    # Modify the SQL query with the user's latitude and longitude values
    query = f"""
 SELECT 
          AddressInfo_Title, 
          AddressInfo_Latitude,
          AddressInfo_Longitude,
          AddressInfo_Town, 
          AddressInfo_StateOrProvince,AddressInfo_Postcode,
          CASE
                WHEN CAST(Level_ID AS STRING) = '1' THEN 'Slow charging 120 V [ 2-4 miles of range per hour]'
                WHEN CAST(Level_ID AS STRING) = '2' THEN 'Fast charging 240 V [10-20 miles of range per hour]'
                WHEN CAST(Level_ID AS STRING) = '3' THEN 'DC ultra fast charging [80% charge in 20-30 minutes]'
                ELSE 'Unknown level'
                 END AS Level,
          CASE
                WHEN CAST(anomaly_class AS STRING) = '1' THEN 'Good'
                ELSE 'Might Fail'
                end as Charging_station_Status,
          CASE 
            WHEN anomaly_class = 1 THEN CONCAT(ROUND(anomaly_percent), '% ')
            ELSE CONCAT(ROUND(anomaly_percent), '% ')
          END AS Predicted_Status_Probablity ,
          AddressInfo_AccessComments,
          ST_GEOGPOINT(CAST(AddressInfo_Longitude AS FLOAT64), CAST(AddressInfo_Latitude AS FLOAT64)) AS geo_point,
      ST_DISTANCE(ST_GEOGPOINT(CAST(AddressInfo_Longitude AS FLOAT64), CAST(AddressInfo_Latitude AS FLOAT64)), ST_GEOGPOINT({user_long}, {user_lat})) AS distance,
             FROM `ev-charge-station-381513.USA_EV_Charging.Charging_Station_Anamoly_prediction`
        ORDER BY
      distance ASC
    LIMIT
      5
    """

    # Execute the modified SQL query and get the results
    results = client.query(query).to_dataframe()

    # Render the results page with the results
    return render_template('results.html', results=results, user_lat=user_lat, user_long=user_long)



if __name__ == '__main__':
    app.run(debug=True)
