# News Poke AWS Lambda.

import feedparser
from dotenv import load_dotenv
from openai import OpenAI
import os
import boto3
from datetime import datetime
import json


def obtain_stories(rss_url: str) -> list:
    rss = feedparser.parse(rss_url)
    items = rss.entries

    # Iterate over feed items.
    stories = []
    while len(items) > 0:
        item = items.pop(0)
        headline = item.title
        thumbnail = item.media_thumbnail[0]['url']
        story = item.description
        origin = item.links[0].href

        stories.append((headline, thumbnail, story, origin))

    return stories


def generate_content(stories: list,
                     humour_style: str,
                     example: str,
                     num_stories: int) -> list:
    """Produce a list of content for a 1 page of the website.
    Each item in the returned list is a tuple (story headline, thumbnail URL, funny version of the story)."""
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    content = []

    # Iterate over stories.
    while len(content) < num_stories and len(stories) > 0:
        headline, thumbnail, story, origin = stories.pop(0)
        prompt = f"""Your task is to impersonate {humour_style}."""

        if example is not None:
            prompt += f"""
Here is an example of their way of talking, inside the XML tag 'example'.
<example>
{example}
</example>"""

        prompt += f"""
I will now give you a real news headline inside the XML tag 'headline' and one sentence from the story inside the XML tag 'story'.
<headline>
{headline}
</headline>
<story>
{story}
</story>

You should respond with a new version of the story, that is in the style of {humour_style}.
Do not include any XML tags in your response.
Do not include any newline characters in your response.
Up to 3 sentences would be the ideal length.
You should think about whether the story I give you is a serious subject that is likely to upset a sensitive person if you make fun of it. For example, war, illness, death, rape, and sexual assault are all serious subjects. If you believe that the subject of the story is a serious one and that it would be tasteless to make fun of it, just respond with 'No comment'."""

        # print(prompt)

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
            content.append((headline, thumbnail, funny, origin))
    return content


def produce_html(title: str,
                 content: list,
                 analytics_tagging: str) -> str:
    html = """
<!DOCTYPE html>
<html lang="en">
<head>
"""

    html += analytics_tagging

    html += """   
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto">
    <title>The Daily Burp</title>
    <style>

body {
    font-family: Roboto, Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f3f3f3;
    min-width: 300px;
}

header {
    background: linear-gradient(to bottom right, darkblue, #4169E1);
    color: #ffffff;
    padding: 10px;
}

.header-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo {
    max-width: 100px;
    margin: 0 20px;
    height: auto;
}

h1 {
    font-size: 2.7rem;
    margin: 0;
    display: inline;
}

h3 {
    margin: 0;
    margin-left: auto;
    margin-right: 30px;
    font-size: 1.75rem;
}

@media (max-width: 768px) {
    h3 {
        font-size:0.1rem;
        visibility: hidden;
    }
}

@media (max-width: 550px) {
    h1 {
        font-size: 2rem;
    }
}

nav {
    background-color: #1e1e1e;
    color: #ffffff;
    padding: 10px;
    text-align: center;
}

nav a,
footer a {
    color: #ffffff;
    text-decoration: none;
    margin: 0 10px;
}

nav a.active {
    color: cyan;
}

section {
    padding: 20px 10px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    max-width: 1800px;
}

.article {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #ffffff !important;
    border: 1px solid #e6e6e6;
    border-radius: 10px;
    margin: 10px;
    padding: 20px;
    box-shadow: 0px 3px 15px rgba(0,0,0,0.3);
    max-width: 300px;
}

.article .content {
    flex: 1;
}

.article .source {
    margin-bottom: 0;
}

.article .source a,
.article .source a:visited,
.article .source a:active,
.article .source a:hover {
    text-decoration: none;
    color: #999;
    font-size: 0.9rem;
    padding: 5px 8px;
    margin-bottom: 0;
    border: 1px solid #aaa;
    border-radius: 8px;
    float: right;
}

.article .content p {
    color: #777;
    font-size: 1rem;
    line-height: 1.25rem;
    text-align: justify;
}

.article .content p:first-of-type {
    font-style: italic;
}

.article .content p:last-of-type {
    margin-bottom: 0;
}

.article .content h2 {
    margin-top: 0;
    margin-bottom: 22px;
    font-size: 1.3rem;
    line-height: 1.45rem;
    color: #333;
    text-align: center;
}

.article .content img {
    width: 100%;
    border: 1px solid #ddd;
}

.rider {
    font-size: 0.8rem;
    line-height: 1.25rem;
    font-style: italic;
    color: #666;
    text-align: center;
    margin: 10px 0 50px 0;
    width: 100%;
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
</head>"""

    html += f"""
<body>
    <header>
        <div class="header-container">
            <img src="website_logo.png" alt="Logo" class="logo">
            <h1>The Daily Burp</h1>
            <h3>{title}</h3>
        </div>
    </header>
    <nav>
        <a href="index.html" class="active">Home</a>
        <a href="sport.html">Sport</a>
        <a href="business.html">Business</a>
    </nav>
    <section>
    <footer>
        <a href="terms.html">Terms</a>
        <a href="cookies.html">Cookies</a>
        <a href="privacy.html">Privacy</a>
    </footer>"""

    # Add the actual stories to the page.
    origin_links = ['boring version', 'snoozefest version', 'grown up version', 'profession version',
                    'not funny version', "you dad's version", 'safe for work version', 'old fashioned version']
    for headline, thumbnail, story, origin in content:
        label = origin_links.pop(0)
        origin_links.append(label)

        html += f"""
        <div class="article">
            <div class="content">
                <h2>{headline}</h2>
                <img src="{thumbnail}">
                <p>{story}</p>
            </div>
            <p class="source"><a href="{origin}">{label}</a></p>
        </div>
"""

    # Add a timestamp to the page footer.
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print("date and time =", dt_string)

    html += f"""
    </section>
    <div class="rider">
        Last refresh: {dt_string}<br/>This website is an experiment in generative AI and intended for amusement purposes only<br/>Honestly relax! Its just a joke
    </div>
    <script>"""

    html += """
const articles = document.querySelectorAll('.article .content');

articles.forEach(article => {
    const prose = article.querySelector('p');
    const parts = (prose.textContent + ' ').split(/([.?!]\s)/).filter(i => i); // adds space to simplify last sentence checking

    for (let i = 0; i < parts.length; i += 2) {
        const text = parts[i].trim();
        const punc = parts[i + 1] || '';

        if (text.length) {
            const alt = document.createElement('p');
            alt.textContent = text + punc;
            prose.after(alt);
        }
    }

    article.removeChild(prose);
});


    </script>
</body>
</html>"""

    return html


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


def obtain_analytics_tagging(filename: str) -> str:
    with open(filename, 'r') as file:
        return file.read()


def main():
    load_dotenv(verbose=True)           # Set operating system environment variables based on contents of .env file.
    for each_page in obtain_pages_list('pages.json')[:1]:
        stories = obtain_stories(rss_url=each_page['rss_url'])
        print(each_page['page'])
        print(stories)
        content = generate_content(stories=stories,
                                   humour_style=each_page['humour_style'],
                                   example=each_page['example'],
                                   num_stories=1)  # 1 story only when testing locally, to save GPT API costs.
        html = produce_html(title=each_page['title'],
                            content=content,
                            analytics_tagging=obtain_analytics_tagging('analytics_tagging.txt'))
        print(html)


def lambda_handler(event, context):
    load_dotenv(verbose=True)           # Set operating system environment variables based on contents of .env file.
    for each_page in obtain_pages_list('pages.json'):
        stories = obtain_stories(rss_url=each_page['rss_url'])
        print(each_page['page'])
        print(stories)
        content = generate_content(stories=stories,
                                   humour_style=each_page['humour_style'],
                                   example=each_page['example'],
                                   num_stories=int(os.environ.get('NUM_STORIES')))
        html = produce_html(title=each_page['title'],
                            content=content,
                            analytics_tagging=obtain_analytics_tagging('analytics_tagging.txt'))
        print(html)

        write_to_s3(bucket=os.environ.get('BUCKET'),
                    object_key=each_page['page'],
                    data=html)
    cloudfront_refresh(distribution_id=os.environ.get('DISTRIBUTION_ID'))


if __name__ == "__main__":
    main()
