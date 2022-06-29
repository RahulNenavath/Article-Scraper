# Article Scraper AWS Lambda Handler

import json
import logging
import traceback
from scraper import ArticleScraper

logging.basicConfig(level=logging.INFO)

logging.info(f'Initiating Article Scraper')
scraper = ArticleScraper(wait_time=5)


def handler(event, context):

    if event['rawPath'] == '/':
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "Service": "Article Scraper API",
                "Status": "Active"
            })
        }

    elif event['rawPath'] == '/ping':
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "Service": "Article Scraper API",
                "Status": "Active",
                "Ping": "Success"
            })
        }

    elif event['rawPath'] == '/scrape':

        request_body = json.loads(event['body'])
        request_url = str(request_body['url'])

        try:
            scraped_content = scraper.run(article_url=request_url)

            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "scraped_content": scraped_content,
                })
            }
        except Exception as e:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json"
                },
                "body": json.dumps({
                    "Error": str(traceback.format_exc),
                    "Exception": str(e)
                })
            }
    else:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "Service": "Article Scraper API",
                "Status": "Active",
                "Message": "API method not allowed"
            })
        }