# Article Scraper

## Description
An article scraper is used to extract all the necessary information from news and articles. The motivation for this project emerged when I tried to read content online but always got blocked by unnecessary paywalls or sign up/sign in banners. Now, with this scraper, one can extract the content from digital news and articles, bypassing these banner popups and accessing our favourite content.

## Input & Output:

<strong>Input:</strong> { 'url': string }

<strong>Output:</strong> 
        {   'article_title': string | None,
            'description': string | None,
            'article_content': string | None,
            'author': string | None,
            'publish_date': string | None,
            'article_url': string | None,
            'canonical_url': string | None,
            'publisher_name': string | None,
            'image': string | None,
            'keywords': string | None,
            'video_url': string | None,
            'audio_url': string | None
        }

## Tech Stack:
Python 3.7, Beautiful Soup, Docker, AWS Lambda, AWS ECR, Github and GitHub Actions for CI/CD

## Deployment:
This project has been deployed as an AWS Lambda function using a container image from the AWS ECR service and made available. AWS Lambda functions are cost effective solutions for personal projects that don't have a lot of network traffic. GitHub Actions is used for CI/CD pipelines where every git push triggers the pipeline and the updated docker container is pushed to AWS ECR.