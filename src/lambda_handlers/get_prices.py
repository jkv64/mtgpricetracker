#
# Python program to get all cards being tracked by MTG Price Tracker
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

############################################################
#
# classes
#
class Price:

  def __init__(self, row):
    self.priceid = row[0]
    self.set = row[1]
    self.price = row[2]
    self.name = row[3]
    self.date = row[4]

def lambda_handler(event, context):
  try:
    print("**STARTING**")
    print("**getting prices...**")
    
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
  
    # example sql
    sql = f"SELECT * FROM prices;"
    rows = datatier.retrieve_all_rows(conn, sql)

    prices = []
    for row in rows:
      prices.append(Price(row))

    if len(prices) == 0:
      print("no price records...")
      return
    else:
      print(f"{len(prices)} price records found!")

    ret = []
    for price in prices:
      temp = {"priceid": price.priceid, "set": price.set, "price": price.price, "name": price.name, "date": price.date.strftime('%Y-%m-%d')}
      ret.append(temp)
   
    return {
      'statusCode': 200,
      'body': json.dumps(ret)
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