# mtgpricetracker

This is a webservice that records the prices of the fetchlands (and more cards) every day using [the Scryfall API](https://scryfall.com/docs/api/). It started as a final project for [Northwestern's CS310 class](https://www.mccormick.northwestern.edu/computer-science/academics/courses/descriptions/310.html) taught by Prof. Joe Hummel. However, as a modern player, I've often wanted an easy way to check the prices of the fetchlands and other staples (and their price history), as a way to check if I should buy them. As such, I want to build this out more to the point where someone can personalize a dashboard of cards they are tracking.

The service is built using AWS Lambda functions executed through AWS Cloudwatch events or the AWS API Gateway. This repository has the lambda function handlers as [lambda_fxn_name].py, as well as datatier.py and webservice.py which are sets of helper methods built by Prof. Hummel and edited by me. exampleconfig.ini shows the framework of the config file that the python file parses to be able to access AWS resources. It needs to be filled in with appropriate credentials if you want to build this service yourself.

Detailed steps for that setup:
[WRITE STEPS]

Current API services at https://5mvvd2iv46.execute-api.us-east-2.amazonaws.com/prod
 - /pricedrop/{numdays}
    - Gives the fetchland with the largest pricedrop over the last *numdays* days

 - /newcards/{query}
    - Adds up to five cards to the tracking table based on the Scryfall search given by *query*
    - Note that *query* is passed directly to Scryfall, without the niceties that the in browser version gives, so you'll have to use the exact syntax you want