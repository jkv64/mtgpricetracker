# mtgpricetracker

This is a webservice that records the prices of the fetchlands (and more cards) every day using [the Scryfall API](https://scryfall.com/docs/api/). It started as a final project for [Northwestern's CS310 class](https://www.mccormick.northwestern.edu/computer-science/academics/courses/descriptions/310.html) taught by Prof. Joe Hummel. However, as a modern player, I've often wanted an easy way to check the prices of the fetchlands and other staples (and their price history), as a way to check if I should buy them. As such, I want to build this out more to the point where someone can personalize a dashboard of cards they are tracking.

The service is built using AWS Lambda functions executed through AWS Cloudwatch events or the AWS API Gateway. This repository has the lambda function handlers as [lambda_fxn_name].py, as well as datatier.py and webservice.py which are sets of helper methods built by Prof. Hummel and edited by me. exampleconfig.ini shows the framework of the config file that the python file parses to be able to access AWS resources. It needs to be filled in with appropriate credentials if you want to build this service yourself.

Current API services at https://5mvvd2iv46.execute-api.us-east-2.amazonaws.com/prod
 - GET /pricedrop/{numdays}
    - Gives the fetchland with the largest pricedrop over the last *numdays* days

 - PUT /newcards
    - Adds up to five cards to the tracking table based on the Scryfall search given by a query passed in the request body
    - Note that the query is passed directly to Scryfall, without the niceties that the in browser version gives, so you'll have to use the exact syntax you want
  
 - GET /cards
    - Returns all cards that are currently being tracked

 - GET /prices
    - Returns all price records in the tracker

 - GET /cardprice/{cardname}
    - Returns the most recent price of *cardname*
    - Can specify a target date instead of using the most recent price by adding a *date* query string (Ex. /cardprice/{cardname}?date=YYYY-MM-DD)

If you've downloaded this repo, you can follow the steps in _docker_readme.txt to get a working environment set up, then just run python3 src/client.py to use these web services!

Detailed steps for server side setup:
1. Create IAM users (I called them s3readwrite and s3readonly). The readonly user can use AWS's readonly policy, but you will have to make your own policy that allows the readwrite user to access your S3 buckets.
2. Make a copy of exampleconfig.ini (or just edit that I guess), and add start updating it as setup goes. The first step is going to Security Credentials for each of your users and generating access keys. You will need to copy the access key and secret access key into your .ini file.
3. Create an S3 bucket to hold the zip files for your Lambda layers. Alternatively, you can just upload the zips. If you are using an S3 bucket, be sure to update your config.ini file.
4. Create a directory called 'python' and pip install the following dependencies in that directory. Then zip up that directory and either upload it to s3 or directly to Lambda when needed.
    a. pymysql
    b. requests
    c. datetime
    d. cryptography
5. In AWS Lambda, go to Layers, and make a new layer by uploading that zip file when prompted.
6. If you do not already have an RDS database server, create one (make sure to add your RDS endpoint to your config file). Then, connect to your server, and execute the SQL in src/mtgpricetracker.sql to generate the needed database for this web service.
7. For each python file in src/lambda_handlers, create a Lambda function and insert that code into the lambda_handler.py function AWS generates. You will also need to add the python files in src/helpers and your config.ini to each Lambda function. Uploading from the zip file example_lambda_base.zip will speed things up, though you will have to rename lambda_skeleton.py to lambda_function.py and add your actual config file.
Go to the configuration tab and make sure the timeout for each is at least 5 minutes. On the code tab, scroll down to layers, and add the layer you made. You will want to make tests for each Lambda function, which can be done in the Lambda console or in API Gateway once you get there. I've left some of my tests in src/tests for reference (for most methods).
8. Go to Amazon EventBridge in the AWS Console then Schedules under Scheduler. Create a schedule that executes your fetch_prices Lambda function every day. I chose 3:00 AM Central Time, but that was totally arbitrary.
9. Go to API Gateway, and create a new REST API. Add your remaining Lambda functions as resources with the appropriate parameters. I chose /pricedrop/{numdays} for find_best_fetch and /newcards/{query} for update_tracking. Make sure find_best_fetch is a GET method and update_tracking is a PUT.
10. Once you're sure that everything is deployed and your database is running, you're good to go! I like to use "SELECT * FROM prices;" in MySQL Workbench every so often to make sure that the scheduled event is still firing.
