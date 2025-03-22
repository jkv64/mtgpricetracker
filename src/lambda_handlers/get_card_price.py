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
import datetime

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**fetching card price info...**")
    
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

    # get cardname and optional date
    if "cardname" in event:
      cardname = event["cardname"]
    elif "pathParameters" in event:
      if "cardname" in event["pathParameters"]:
        cardname = event["pathParameters"]["cardname"]
      else:
        raise Exception("requires cardname parameter in pathParameters")
    else:
        raise Exception("requires cardname parameter in event")
    
    date = datetime.date.today().strftime('%Y-%m-%d')
    if "queryStringParameters" in event:
        if "date" in event["queryStringParameters"]:
            date = event["queryStringParameters"]["date"]
        else:
            raise Exception("date is the only expected query parameter")

  
    #need to check the cards table to see if we're tracking this
    sql1 = f"SELECT * FROM cards WHERE cardname='{cardname}';"
    rows = datatier.retrieve_all_rows(conn, sql1)
    if len(rows) == 0:
        raise Exception("This card's price is not being tracked")

    sql2 = f"SELECT price FROM prices WHERE cardname='{cardname}' AND pricedate='{date}';"
    rows = datatier.retrieve_all_rows(conn, sql2)

    if len(rows) == 0:
        raise Exception("There's no price record for that date.")
       
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