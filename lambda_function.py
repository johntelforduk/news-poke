from rss_parser import RSSParser
from requests import get  # noqa
from dotenv import load_dotenv
from openai import OpenAI
import os
import boto3
from datetime import datetime
import json


def produce_html(content: list) -> str:
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Daily Burp</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f3f3f3;
        }
        header {
            background-color: #fe1a30;
            color: #ffffff;
            padding: 40px 10px; /* Increased vertical padding */
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        nav {
            background-color: #1e1e1e;
            color: #ffffff;
            padding: 10px;
            text-align: center;
        }
        nav a {
            color: #ffffff;
            text-decoration: none;
            margin: 0 10px;
        }
        section {
            padding: 20px;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
        }
        .article {
            background-color: #ffffff;
            border: 1px solid #e6e6e6;
            margin: 10px;
            padding: 20px;
            width: 30%;
            max-width: 300px;
        }
        .article h2 {
            margin-top: 0;
            font-size: 18px;
            color: #1e1e1e;
        }
        .article p {
            color: #4d4d4d;
            font-size: 14px;
        }
        .logo {
            max-width: 300px; /* Adjust as needed */
            height: auto;
            background-color: #fe1a30; /* Background color of the logo */
        }
        footer {
            background-color: #1e1e1e;
            color: #ffffff;
            text-align: center;
            padding: 10px;
            position: fixed;
            bottom: 0;
            width: 100%;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <header>
        <img src="logo.png" alt="Logo" class="logo">
    </header>
    <nav>
        <a href="index.html">Home</a>
        <a href="sport.html">Sport</a>
        <a href="business.html">Business</a>
    </nav>
   <section>"""

    # Add a timestamp to the page footer.
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)
    html += f"""
    <footer>
        Last refresh: {dt_string}
    </footer>
"""
    # Add the actual stories to the page.
    for headline, story in content:
        html += f"""        <div class="article">
            <h2>{headline}</h2>
            <p>{story}</p>
        </div>
"""

    # Close remaining tags.
    html += """    </section>
</body>
</html>"""
    return html


def produce_content(rss_url: str,
                    humour_style: str,
                    num_stories: int) -> list:
    """Produce a list of content for a 1 page of the website.
    Each item in the returned list is a tuple (story headline, funny version of the story)."""

    response = get(rss_url)
    rss = RSSParser.parse(response.text)

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    # Iteratively over feed items.
    content = []
    items = rss.channel.items
    while len(content) < num_stories and len(items) > 0:
        item = items.pop(0)
        headline = item.title.content
        story = item.description.content

        prompt = f"""Your task is to impersonate {humour_style}.
    I will now give you a real news headline inside the XML tag 'headline' and one sentence from the story inside the XML tag 'story'.
    <headline>
    {headline}
    </headline>
    <story>
    {story}
    </story>
    Your should respond with a new version of the story, that is in the style of {humour_style}.
    Do not include any XML tags in your response.
    Do not put your headline in quotation marks.
    Do not include any newline characters in your response.
    Up to 3 sentences would be the ideal length.
    If you believe that the subject of the story is a serious one and that it would be tasteless to make fun of it, just respond with 'No comment'."""

        completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4-0613",
            temperature=float(os.environ.get('TEMPERATURE'))
        )

        funny = completion.choices[0].message.content

        print(f'Original Headline: {headline}')
        print(f'Original Story: {story}')
        print(f'Funny version: {funny}')
        print('---')

        if 'No comment' not in funny:
            content.append((headline, funny))
    return content


def write_to_s3(bucket: str, object_key: str, data: str) -> None:
    """For parm bucket name, object key and data string, write the object to S3 containing the data."""
    s3_resource = boto3.resource("s3")
    s3_resource.Object(bucket, object_key).put(Body=bytes(data, "utf-8"),ContentType='text/html')


def cloudfront_refresh(distribution_id: str):
    """Create an invalidation for the parm CloudFront distribution_id. This has the effect of allowing users
    to see a refreshed version of the website."""
    cf_client = boto3.client('cloudfront')
    now = str(datetime.now())                   # Using timestamp is a way of producing a unique CallerReference.

    cf_client.create_invalidation(
        DistributionId=distribution_id,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': [
                    '/*',                       # Wildcard, to invalidate the whole website.
                ]
            },
            'CallerReference': now
        }
    )


def obtain_pages_list(filename: str) -> list:
    """Read file with parm filename. The contents of the file is JSON list, where each item in the list
    is a dictionary. Return the list of dictionaries."""
    with open(filename, 'r') as file:
        return json.loads(file.read())


def main():
    load_dotenv(verbose=True)           # Set operating system environment variables based on contents of .env file.
    for each_page in obtain_pages_list('pages.json'):
        print(each_page['page'])
        produce_content(rss_url=each_page['rss_url'],
                        humour_style=each_page['humour_style'],
                        num_stories=1)  # 1 story only when testing locally, to save GPT API costs.


def lambda_handler(event, context):
    load_dotenv(verbose=True)           # Set operating system environment variables based on contents of .env file.
    for each_page in obtain_pages_list('pages.json'):
        print(each_page['page'])
        content = produce_content(rss_url=each_page['rss_url'],
                                  humour_style=each_page['humour_style'],
                                  num_stories=8)

        html = produce_html(content)
        print(html)
        write_to_s3(bucket=os.environ.get('BUCKET'), object_key=each_page['page'], data=html)
    cloudfront_refresh(distribution_id=os.environ.get('DISTRIBUTION_ID'))


if __name__ == "__main__":
    main()
