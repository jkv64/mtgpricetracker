#
# Python program to pull and compare price data from a database of daily mtg card prices
#
# Written by Jack Vogel using template code from Joe Hummel (Northwestern CS310)
#

import json
import boto3
import os
import uuid
import base64
import pathlib
import src.datatier as datatier
import src.webservice as webservice
import urllib.parse
import string
import datetime

from configparser import ConfigParser

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**finding the best fetchland...**")
    
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

    # expecting the body of the request to have a num_days parameter
    if "numdays" in event:
      num_days = event["numdays"]
    elif "pathParameters" in event:
      if "numdays" in event["pathParameters"]:
        num_days = event["pathParameters"]["numdays"]
      else:
        raise Exception("requires numdays parameter in pathParameters")
    else:
        raise Exception("requires numdays parameter in event")

    if type(num_days) is not int:
        num_days = int(num_days)
        # this will raise an error if it's not an int-like string

    today = datetime.date.today()
    # the prices are fetched at 3am Central so we will update based on yesterday's if it's 4am or earlier
    if datetime.datetime.now().hour < 9:
      today = today - datetime.timedelta(days=1)

    target_day = today - datetime.timedelta(days=num_days)

    if target_day < datetime.date(2025, 3, 9):
      raise Exception("Tracking started March 9th, 2025. Please select a smaller number of days.")

    sql = f"""SELECT cardname, price, pricedate, setcode from prices WHERE pricedate = '{today.strftime('%Y-%m-%d')}'
            OR pricedate = '{target_day.strftime('%Y-%m-%d')}' ORDER BY cardname, pricedate ASC"""

    rows = datatier.retrieve_all_rows(conn, sql)

    best_diff = 100
    for i in range(len(rows)):
        row = rows[i]
        #print(row)
        #going to be comparing backwards so can skip the first row
        if i == 0:
          continue

        prev_row = rows[i-1]

        # recall order is 0=name, 1=price, 2=date, 3=setcode
        if row[0] == prev_row[0] and row[3] != prev_row[2]:
          diff = row[1] - prev_row[1]
          if diff < best_diff:
            best_diff = diff
            best_card = row[0]
            best_price = row[1]
            best_set = row[3]

    print(f"The card with the biggest price drop was {best_card} with a {str(best_diff)} change!")
    print(f"The best printing is {best_set} at ${best_price}.")



    return {
      'statusCode': 200,
      'body': json.dumps({
        'cardname': best_card,
        'diff': best_diff,
        'price': best_price,
        'setcode': best_set
      })
    }
  
  #
  # on an error, output error message:
  #
  except Exception as err:
    print("**ERROR**")
    print(str(err))

    return {
      'statusCode': 500,
      'body': json.dumps(str(err))
    }