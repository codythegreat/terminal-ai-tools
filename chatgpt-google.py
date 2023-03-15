#!/usr/bin/env python3

import os
import sys
import openai
import re
import subprocess
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
            {"role": "user", "content": """1) http://t3.gstatic.com/licensed-image?q=tbn:ANd9GcTg7KNGcDDNqQ0BJbTb2X6qEFhBct63mNP_67cjwqaMndhdj1Fe68Lbr3IlD9kQwhbW\n2) https://en.wikipedia.org/wiki/Flower_Mound,_Texas\n3) https://www.flower-mound.com/112/Upcoming-Events\n4) https://www.flower-mound.com/1943/Special-Events\n5) https://www.eventbrite.com/d/tx--flower-mound/events--this-weekend/\n6) https://www.eventbrite.com/d/tx--flower-mound/events/\n7) https://www.groupon.com/local/flower-mound-tx/tickets-and-events\n8) https://allevents.in/flower%20mound/this-weekend\n9) https://www.facebook.com/4fortyEvents/\n10) https://www.partyslate.com/venues/4forty-events\n\nQuery: events flower mound tx"""},
            {"role": "assistant", "content": """Here are the three best search results for "events flower mound tx":\n\n1) OPEN(2) https://en.wikipedia.org/wiki/Flower_Mound,_Texas - This Wikipedia page provides general information about Flower Mound, including a section on local events.\n\n2) OPEN(3) https://www.flower-mound.com/112/Upcoming-Events - This is the official website of Flower Mound, Texas and has a dedicated page for upcoming events in the area.\n\n3) OPEN(7) https://www.groupon.com/local/flower-mound-tx/tickets-and-events - This Groupon page features discounted tickets and deals for various events in Flower Mound.\n            """},
            {"role": "user", "content": USER_PROMPT},
        ]
    )
    response = completion.choices[0].message.content

    match = re.findall(r'OPEN\(([1-9]|10)\)', response)
    parsed_urls = []
    for number in match:
        number = int(number)
        url = results[number - 1]
        article = get_article_from_url(url)
        parsed_urls.append({
            'content': article,
            'url': url,
        })

        summarize_url(parsed_urls[-1])

    if len(parsed_urls) == 0:
        exit()

    option = input(f"Press {1 if len(parsed_urls) == 1 else f'1 - {len(parsed_urls)}'} to select a URL to view, or 0 to exit: ")

    if not (option.isdigit() and 1 <= int(option) <= len(parsed_urls)):
        print("exiting...")
        exit()

    # Launch vim with the content as input
    cmd = ['vim', '-']
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    p.communicate(input=parsed_urls[int(option) - 1]['content'].encode('utf-8'))

def get_article_from_url(url):
    article = Article(url)
    try:
        article.download()
        article.parse()
        output = f"TITLE: {article.title}\n\nTEXT:\n{article.text}"
    except Exception as e:
        # Note: This is a hacky way to get the text from a website.
        title = subprocess.check_output(f'lynx -source -dump -nolist "{url}" | sed -n "s/<title>\\(.*\\)<\\/title>/\\1/p"', shell=True).decode()
        article = subprocess.check_output(f'lynx -dump -nolist "{url}"', shell=True).decode()
        output = f"TITLE: {title}\n\nTEXT:\n{article}"

    return output


def summarize_url(parsed_url):
    output = parsed_url['content']

    # leave some room for chatGPT
    if len(output) > 10000:
        output = output[:10000]

    output += f"\n\nQUERY: \"{query}\""
    
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "I am an expert website summarization tool. Given a search query and a text dump of a website, I will generate a concise summary of the site's key details that are relevant to the search query. I will ignore details that a not relevant to the query."},
            {"role": "user", "content": output},
        ]
    )

    response = completion.choices[0].message.content
    print(f"URL: {parsed_url['url']}\n\nSUMMARY:\n{response}\n\n")


get_best_search_results()