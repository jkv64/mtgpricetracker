#
# Python program to _________________________________
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
import datetime

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**[doing task]...**")
    
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

    # structure for getting path parameters
    if "cardname" in event:
      cardname = event["cardname"]
    elif "pathParameters" in event:
      if "cardname" in event["pathParameters"]:
        cardname = event["pathParameters"]["cardname"]
      else:
        raise Exception("requires cardname parameter in pathParameters")
    else:
        raise Exception("requires cardname parameter in event")
    
    # structure for getting query string parameters
    date = datetime.date.today().strftime('%Y-%m-%d')
    if "queryStringParameters" in event:
        if "date" in event["queryStringParameters"]:
            date = event["queryStringParameters"]["date"]
        else:
            raise Exception("date is the only expected query parameter")

  
    # example sql
    sql1 = f"SELECT * FROM cards WHERE cardname='{cardname}';"
    rows = datatier.retrieve_all_rows(conn, sql1)
    if len(rows) == 0:
        raise Exception("This card's price is not being tracked")
    
    # example Scryfall query
    url = "https://api.scryfall.com/cards/search?"

    query = "Crag Saurian"

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
        
    # TODO
    # do your work!
       
    return {
      'statusCode': 200,
      'body': json.dumps({"price": rows[0][0]})
    }
  
  #
  # on an error, try to output error message:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }