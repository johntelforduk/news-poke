# News Poke
Use generative AI to poke fun at the news. This program takes the RSS feed from a news website and uses generative AI to invent funny versions of the stories. The result is published to a news-like comedy website.

For example: [www.burp.news](www.burp.news)

### Installation
```commandline
pip install rss-parser
pip install requests
pip install python-dotenv
pip install openai
pip install boto3
```
Or do `pip install -r requirements.txt`
### Configuration
Please set the following environment variables. For example, by creating a `.env` file.

| Environment Variable | Description                                                             |
| --- |-------------------------------------------------------------------------|
| OPENAI_API_KEY | Your OpenAI API key                                                     |
| TEMPERATURE | 'Temperature' of Gen AI model's response. Between 0.0 and 1.0           |
| RSS_URL | The URL of your choice of RSS feed for the program to base funny stories on. |
| HUMOUR_STYLE | Will be included in the prompt sent to Gen AI model. For example "Barry Cryer" |
| DISTRIBUTION_ID | Id of your Amazon Cloudfrount distribution. |
| BUCKET | Name of the Amazon S3 bucket to use for website hosting. |

### Overview
The main Lambda does the following when run in an AWS Lambda function.

* Reads items from an RSS feed.
* Send prompts based on the RSS feed items to OpenAI GPT-4. 
* Makes some HTML based on the responses.
* Puts the HTML into the object `index.html` on an Amazon S3 bucket.
* Invalidates the Amazon CloudFront distribution that serves the website. This is so that the latest data can be seen by visitors to the site.