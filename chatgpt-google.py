#!/usr/bin/env python3

import os
import sys
import openai
import re
from googlesearch import search
from newspaper import Article

openai.api_key = os.getenv("OPENAI_API_KEY")

query = sys.argv[1]
 
results = []
all_results = ""
for index, result in enumerate(search(query, num=10, stop=10, pause=2)):
    results.append(result)
    all_results += f"{index + 1}. {result}\n"


SYSTEM_PROMPT = "I am an expert search engine results selector. I can select a maximum of three results. I will only select the best results to show the user. To show a result I will wrap the result's number in an OPEN() syntax. I will not select links that are images, videos, or pdfs."
USER_PROMPT = f"{all_results}\n\nQuery: {query}"

def get_best_search_results():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": """1) http://t3.gstatic.com/licensed-image?q=tbn:ANd9GcTg7KNGcDDNqQ0BJbTb2X6qEFhBct63mNP_67cjwqaMndhdj1Fe68Lbr3IlD9kQwhbW
2) https://en.wikipedia.org/wiki/Flower_Mound,_Texas
3) https://www.flower-mound.com/112/Upcoming-Events
4) https://www.flower-mound.com/1943/Special-Events
5) https://www.eventbrite.com/d/tx--flower-mound/events--this-weekend/
6) https://www.eventbrite.com/d/tx--flower-mound/events/
7) https://www.groupon.com/local/flower-mound-tx/tickets-and-events
8) https://allevents.in/flower%20mound/this-weekend
9) https://www.facebook.com/4fortyEvents/
10) https://www.partyslate.com/venues/4forty-events

Query: events flower mound tx"""},
            {"role": "assistant", "content": """Here are the three best search results for "events flower mound tx":

1) OPEN(2) https://en.wikipedia.org/wiki/Flower_Mound,_Texas - This Wikipedia page provides general information about Flower Mound, including a section on local events.

2) OPEN(3) https://www.flower-mound.com/112/Upcoming-Events - This is the official website of Flower Mound, Texas and has a dedicated page for upcoming events in the area.

3) OPEN(7) https://www.groupon.com/local/flower-mound-tx/tickets-and-events - This Groupon page features discounted tickets and deals for various events in Flower Mound.
            """},
            {"role": "user", "content": USER_PROMPT},
        ]
    )
    response = completion.choices[0].message.content

    match = re.findall(r'OPEN\(([1-9]|10)\)', response)
    for number in match:
        number = int(number)
        url = results[number - 1]
        summarize_url(url)

def get_article_from_url(url):
    # Note: This is a hacky way to get the text from a website.
    # using newspaper3k does a better job of grabbing just the relavent text
    # command = f'lynx -dump -nolist "{url}"'
    # try:
    #     output = subprocess.check_output(command, shell=True).decode()
    # except subprocess.CalledProcessError as e:
    #     output = e
    #     print(f'\nERROR:\n{output}')
    #     exit()
    article = Article(url)
    try:
        article.download()
        article.parse()
    except Exception as e:
        pass

    output = f"TITLE: {article.title}\n\nTEXT:\n{article.text}"

    # leave some room for chatGPT
    if len(output) > 10000:
        output = output[:10000]

    return output


def summarize_url(url):
    output = get_article_from_url(url)

    output += f"\n\nQUERY: \"{query}\""
    
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "I am an expert website summarization tool. Given a search query and a text dump of a website, I will generate a concise summary of the site's key details that are relevant to the search query. I will ignore details that a not relevant to the query."},
            {"role": "user", "content": output},
        ]
    )

    response = completion.choices[0].message.content
    print(f"URL: {url}\n\nSUMMARY:\n{response}\n\n")


get_best_search_results()