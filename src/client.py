#
# Client-side python app for mtgpricetracker app, which is calling
# a set of lambda functions in AWS through API Gateway.
# The overall purpose of the app is to track prices of Magic: the Gathering
# cards and the changes of those prices over time.
#
# Authors:
#   Jack Vogel
#
#   Prof. Joe Hummel (initial template)
#   Northwestern University
#   CS 310
#

import requests
import jsons

import uuid
import pathlib
import logging
import sys
import os
import base64
import time

from configparser import ConfigParser
from getpass import getpass


############################################################
#
# classes
#
class User:

  def __init__(self, row):
    self.userid = row[0]
    self.username = row[1]
    self.pwdhash = row[2]


class Job:

  def __init__(self, row):
    self.jobid = row[0]
    self.userid = row[1]
    self.status = row[2]
    self.originaldatafile = row[3]
    self.datafilekey = row[4]
    self.resultsfilekey = row[5]


###################################################################
#
# web_service_get
#
# When calling servers on a network, calls can randomly fail. 
# The better approach is to repeat at least N times (typically 
# N=3), and then give up after N tries.
#
def web_service_get(url, headers=None):
  """
  Submits a GET request to a web service at most 3 times, since 
  web services can fail to respond e.g. to heavy user or internet 
  traffic. If the web service responds with status code 200, 400 
  or 500, we consider this a valid response and return the response.
  Otherwise we try again, at most 3 times. After 3 attempts the 
  function returns with the last response.
  
  Parameters
  ----------
  url: url for calling the web service
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.get(url, headers=headers)
        
      if response.status_code in [200, 400, 480, 481, 482, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_get() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None
    
def web_service_put(url, data):
  """
  
  Parameters
  ----------
  url: url for calling the web service
  data: json to be included in the body of the request
  
  Returns
  -------
  response received from web service
  """

  try:
    retries = 0
    
    while True:
      response = requests.put(url, json=data)
        
      if response.status_code in [200, 400, 500]:
        #
        # we consider this a successful call and response
        #
        break;

      #
      # failed, try again?
      #
      retries = retries + 1
      if retries < 3:
        # try at most 3 times
        time.sleep(retries)
        continue
          
      #
      # if get here, we tried 3 times, we give up:
      #
      break

    return response

  except Exception as e:
    print("**ERROR**")
    logging.error("web_service_put() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return None

############################################################
#
# prompt
#
def prompt():
  """
  Prompts the user and returns the command number

  Parameters
  ----------
  None

  Returns
  -------
  Command number entered by user (0, 1, 2, ...)
  """
  try:
      print()
      print(">> Enter a command:")
      print("   0 => end")
      print("   1 => cards")
      print("   2 => prices")
      print("   3 => find best fetch")
      print("   4 => add more cards")
      print("   5 => card price")

      cmd = input()

      if cmd == "":
        cmd = -1
      elif not cmd.isnumeric():
        cmd = -1
      else:
        cmd = int(cmd)

      return cmd

  except Exception as e:
      print("**ERROR")
      print("**ERROR: invalid input")
      print("**ERROR")
      return -1


############################################################
#
# users
#
def best_fetch(baseurl, numdays):
  """
  Finds the fetchland with the largest price drop over numdays days

  Parameters
  ----------
  baseurl: baseurl for web service
  numdays: the interval to look for price changes over

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/pricedrop/'
    url = baseurl + api + numdays

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    #
    # deserialize and extract datapoints:
    #
    body = res.json()

    best_card = body["cardname"]
    price_diff = body["diff"]
    curr_price = body["price"]
    best_set = body["setcode"]

    print(f"The card with the biggest price drop was {best_card} with a {str(price_diff)} change!")
    print(f"The best printing is {best_set} at ${curr_price}.")
    return

  except Exception as e:
    logging.error("**ERROR: best_fetch() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# add_cards
#
def add_cards(baseurl):
  """
  Adds cards to be tracked based on an input Scryfall search

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    query = input("Enter a valid Scryfall search. The first five (or less) new cards will be added to tracking> ")

    query = query.replace(" ", "+")
    #
    # call the web service:
    #
    api = '/newcards'
    url = baseurl + api

    # res = requests.put(url)
    res = web_service_put(url, {"query": query})

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    # if it's successful, we can just print the return message saying how many cards were added
    body = res.json()
    print(body)
    return

  except Exception as e:
    logging.error("**ERROR: add_cards() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# cards
#
def cards(baseurl):
  """
  Returns all cards being tracked

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/cards'
    url = baseurl + api

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    # if it's successful, we have a list of cards
    body = res.json()

    for card in body:
      print(f"   {card["cardid"]}: {card["name"]} added on {card["date"]}")
    
    return

  except Exception as e:
    logging.error("**ERROR: cards() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# prices
#
def prices(baseurl):
  """
  Returns all price records in the database

  Parameters
  ----------
  baseurl: baseurl for web service

  Returns
  -------
  nothing
  """

  try:
    #
    # call the web service:
    #
    api = '/prices'
    url = baseurl + api

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    # if it's successful, we have a list of cards
    body = res.json()

    for price in body:
      print(f"   {price["priceid"]}: {price["name"]}'s {price["set"]} printing was ${price["price"]} on {price["date"]}")
    
    return

  except Exception as e:
    logging.error("**ERROR: prices() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# get_price
#
def get_price(baseurl, cardname):
  """
  Return a price record for a specific card

  Parameters
  ----------
  baseurl: baseurl for web service
  cardname: the name of the card to find the price of

  Returns
  -------
  nothing
  """

  try:

    date = input("Input a target date in YYYY-MM-DD format or hit enter to use the most recent price> ")

    #
    # call the web service:
    #
    api = '/cardprice/'
    url = baseurl + api + cardname.replace(' ', '+')

    if date is not "":
      url += "?date=" + date

    # res = requests.get(url)
    res = web_service_get(url)

    #
    # let's look at what we got back:
    #
    if res.status_code == 200: #success
      pass
    else:
      # failed:
      print("**ERROR: failed with status code:", res.status_code)
      print("url: " + url)
      if res.status_code == 500:
        # we'll have an error message
        body = res.json()
        print("Error message:", body)
      #
      return

    # if it's successful, we have a price
    body = res.json()

    print(f"Price: ${body["price"]}")
    
    return

  except Exception as e:
    logging.error("**ERROR: prices() failed:")
    logging.error("url: " + url)
    logging.error(e)
    return
  
############################################################
#
# check_url
#
def check_url(baseurl):
  """
  Performs some checks on the given url, which is read from a config file.
  Returns updated url if it needs to be modified.

  Parameters
  ----------
  baseurl: url for a web service

  Returns
  -------
  same url or an updated version if it contains an error
  """

  #
  # make sure baseurl does not end with /, if so remove:
  #
  if len(baseurl) < 16:
    print("**ERROR: baseurl '", baseurl, "' is not nearly long enough...")
    sys.exit(0)

  if baseurl == "https://YOUR_GATEWAY_API.amazonaws.com":
    print("**ERROR: update config file with your gateway endpoint")
    sys.exit(0)

  if baseurl.startswith("http:"):
    print("**ERROR: your URL starts with 'http', it should start with 'https'")
    sys.exit(0)

  lastchar = baseurl[len(baseurl) - 1]
  if lastchar == "/":
    baseurl = baseurl[:-1]
    
  return baseurl


############################################################
# main
#
try:
  print('** Welcome to MTG Price Tracker! **')
  print()

  # eliminate traceback so we just get error message:
  sys.tracebacklimit = 0

  #
  # we have two config files:
  # 
  #    1. benfordapp API endpoint
  #    2. authentication service API endpoint
  #
  #
  config = 'mtgpricetracker-client.ini'

  print("First, enter name of mtgpricetracker client config file to use...")
  print("Press ENTER to use default, or")
  print("enter config file name>")
  s = input()

  if s == "":  # use default
    pass  # already set
  else:
    config = s

  #
  # does config file exist?
  #
  if not pathlib.Path(config).is_file():
    print("**ERROR: mtgpricetracker config file '", config, "' does not exist, exiting")
    sys.exit(0)

  #
  # setup base URL to web service:
  #
  configur = ConfigParser()
  configur.read(config)
  baseurl = configur.get('client', 'webservice')
  
  baseurl = check_url(baseurl)

  #
  # main processing loop:
  #
  cmd = prompt()

  while cmd != 0:
    #
    if cmd == 1:
      cards(baseurl)
    elif cmd == 2:
      prices(baseurl)
    elif cmd == 3:
      numdays = input("Enter interval (in days) to check prices over> ")
      best_fetch(baseurl, numdays)
    elif cmd == 4:
      add_cards(baseurl)
    elif cmd == 5:
      cardname = input("What card do you want to know the price of?> ")
      get_price(baseurl, cardname)

    else:
      print("** Unknown command, try again...")
    #
    cmd = prompt()

  #
  # done
  #
  print()
  print('** done **')
  sys.exit(0)

except Exception as e:
  logging.error("**ERROR: main() failed:")
  logging.error(e)
  sys.exit(0)
