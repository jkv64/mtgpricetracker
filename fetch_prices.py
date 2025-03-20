#
# Python program to poll the Scryfall API for fetchland information
# and update a database
#
# Written by Jack Vogel using template code from Joe Hummel (Northwestern CS310)
#

import json
import boto3
import os
import uuid
import base64
import pathlib
import datatier
import webservice
import urllib.parse
import string
import cryptography
from datetime import date

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**fetching fetchland info...**")
    
    #
    # setup AWS based on config file:
    #
    config_file = 'mtgpricetracker.ini'
    os.environ['AWS_SHARED_CREDENTIALS_FILE'] = config_file
    
    configur = ConfigParser()
    configur.read(config_file)
    
    #
    # configure for S3 access:
    #
    s3_profile = 's3readwrite'
    boto3.setup_default_session(profile_name=s3_profile)
    
    bucketname = configur.get('s3', 'bucket_name')
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucketname)
    
    #
    # configure for RDS access
    #
    rds_endpoint = configur.get('rds', 'endpoint')
    rds_portnum = int(configur.get('rds', 'port_number'))
    rds_username = configur.get('rds', 'user_name')
    rds_pwd = configur.get('rds', 'user_pwd')
    rds_dbname = configur.get('rds', 'db_name')

    conn = datatier.get_dbConn(rds_endpoint, rds_portnum, rds_username, rds_pwd, rds_dbname)
  
    #need to check the cards table for what cards we should update
    sql = "SELECT cardname FROM cards;"
    rows = datatier.retrieve_all_rows(conn, sql)


    url = "https://api.scryfall.com/cards/search?q=%21%27"
    footer = "%27+include%3Aextras+game%3Apaper+-is%3Amemorabilia&unique=prints"

    rowsupdated = 0
    for row in rows:
      name = row[0]
      print(name)
      query = url + name + footer
      res = webservice.web_service_get(query)
      body = json.loads(res.data)

      # let's look at what we got back:
      if res.status == 200: #success
        pass
      else:
        # failed:
        print("Failed with status code:", res.status)
        print("url: " + url)
        if res.status == 500:
          # we'll have an error message
          print("Error message:", body)
        #
        raise Exception("Scryfall request failed with error: ", body)

      # deserialize and extract prices:
      b_price = 10000
      b_set = ""
      for row in body["data"]:
        p = row["prices"]["usd"]
        if p is None:
          continue
        else:
          p = float(p)

        if p < b_price:
          b_price = p
          b_set = row["set"]

      print(f"The best printing for {name} is in {b_set} at ${b_price}")
      print("Updating database...")

      # date code from https://stackoverflow.com/questions/32490629/getting-todays-date-in-yyyy-mm-dd-in-python
      # datetime.today().strftime('%Y-%m-%d')

      sql = f"""INSERT INTO prices(setcode, price, cardname, pricedate, imagekey)
                values('{b_set}', {b_price}, '{name}', '{date.today().strftime('%Y-%m-%d')}', '---')"""
      
      num = datatier.perform_action(conn, sql)
      if num != 1:
        raise Exception(f"Failed to insert into database. Affected {num} rows.")
      else:
        print(f"Added {name}'s entry to the database.")
        rowsupdated += 1

    return {
      'statusCode': 200,
      'body': json.dumps(f"Done! Added prices for {rowsupdated} cards!")
    }
  
  #
  # on an error, try to upload error message to S3:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }