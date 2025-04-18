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
import datetime

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**adding cards to tracking...**")
    
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
  
    url = "https://api.scryfall.com/cards/search?q=game%3Apaper+"

    # expecting the request body  to have a query parameter
    if "body" in event:
      print(event["body"])
      body = json.loads(event["body"])
      if "query" in body:
        query = body["query"]
      else:
        raise Exception("requires query parameter in request body")
    else:
      raise Exception("requires body with data")

    print("User's query: ", query)

    # can't have spaces in the url, but should be able to process other special characters
    new_query = query.replace(" ", "+")

    search = url + new_query
    res = webservice.web_service_get(search)
    body = json.loads(res.data)

    # let's look at what we got back:
    if res.status == 200: #success
        pass
    else:
        # failed:
        print("Failed with status code:", res.status)
        if res.status >= 400:
            # we'll have an error message
            print("Error message:", body)
        
        #Scryfall error objects have a "code" and a "details" field:
        if "code" in body and "details" in body:
          code = body["code"]
          print("Error code:", code)
          details = body["details"]
          print("Error details:", details)
          raise Exception(f"Scryfall request returned error \"{code}\" and additional warnings: {details}")
        else:
          raise Exception(f"Scryfall request failed with status code {res.status}")

      
    #otherwise we can get ready to add names to the tracking database
    today = datetime.date.today()
    if datetime.datetime.now().hour >= 9:
      today += datetime.timedelta(days=1) #cards have already been updated today
    today = today.strftime("%Y-%m-%d")
    cutoff = 5
    i = 0
    numadded = 0

    # deserialize and add name to database if it's not already there:
    for row in body["data"]:
      # don't want to add too many cards at a time
      if i >= cutoff:
        break

      name = row["name"].replace(" ", "+")
      print(name)

      sql = f"""SELECT * FROM cards WHERE cardname = '{name}';"""
      rows = datatier.retrieve_all_rows(conn, sql)
      if len(rows) == 0:
        print("Card name not present; inserting...")
        sql = f"""INSERT INTO cards(cardname, dateadded)
                  values('{name}', '{today}');"""
        num = datatier.perform_action(conn, sql)
        if num != 1:
          raise Exception(f"Failed to insert into database. Affected {num} rows.")
        else:
          print(f"Added {name} to the database.")
          numadded += 1
      i += 1

    print(f"{numadded}/{i} cards from search were added to tracking!")

    return {
      'statusCode': 200,
      'body': json.dumps(f"Done! Added {numadded} new cards to tracking!")
    }
  
  #
  # on an error, output error from Scryfall:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }