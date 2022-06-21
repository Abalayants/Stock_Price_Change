import requests
from twilio.rest import Client
import datetime
from datetime import datetime as dt
import time
from config import NEWS_API, STOCK_API, twilio_sid, twilio_auth_token


# Choose a company
STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

# STOCK ENDPOINT
STOCK_ENDPOINT = "https://www.alphavantage.co/query"

# NEWS ENDPOINT
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

news_parameters = {
    "apiKey": NEWS_API,
    "q": COMPANY_NAME
}

# TWILIO
client = Client(twilio_sid, twilio_auth_token)

# STEP 1: STOCK PRICE
# When STOCK price increase/decreases by 5% between yesterday and the day before yesterday then get news:

stock_parameters = {
    "function": "TIME_SERIES_DAILY",
    "symbol": STOCK,
    "apikey": STOCK_API
}

stock_price_response = requests.get(STOCK_ENDPOINT, params=stock_parameters)
stock_price_response.raise_for_status()
stock_data = stock_price_response.json()
daily_stock_price = stock_data['Time Series (Daily)']

# Set dates
day = time.strftime("%d")
month = time.strftime("%m")
year = time.strftime("%Y")
one_day = datetime.timedelta(days=1)

# Function to get date to circumvent Sunday when the market is not open.
def get_date():
    if time.strftime("%a") == "Sun":
        yesterdays_day = dt.today().day - (one_day.days * 2)
        day_before_yesterday = yesterdays_day - (one_day.days * 3)
    else:
        yesterdays_day = dt.today().day - one_day.days
        day_before_yesterday = yesterdays_day - one_day.days
    yesterday_full = f"{year}-{month}-{yesterdays_day}"
    day_before_full = f"{year}-{month}-{day_before_yesterday}"
    return yesterday_full, day_before_full


# Get the closing price for yesterday and the day before yesterday.
def get_closing_price():
    yesterday = get_date()[0]
    day_before = get_date()[1]
    try:
        yesterday_close = round(float(daily_stock_price[yesterday]["4. close"]), 2)
        day_before_close = round(float(daily_stock_price[day_before]["4. close"]), 2)
    except KeyError:
        yesterdays_day = dt.today().day - (one_day.days * 3)
        day_before_yesterday = yesterdays_day - (one_day.days * 4)
        yesterday = f"{year}-{month}-{yesterdays_day}"
        day_before = f"{year}-{month}-{day_before_yesterday}"
        yesterday_close = round(float(daily_stock_price[yesterday]["4. close"]), 2)
        day_before_close = round(float(daily_stock_price[day_before]["4. close"]), 2)
    return yesterday_close, day_before_close


# Work out the value of 5% of yesterday's closing stock price.
yesterday_close = get_closing_price()[0]
day_before_close = get_closing_price()[1]
percent_change = round(round(yesterday_close - day_before_close, 2) / day_before_close)
change_emoji = "🔺" if yesterday_close > day_before_close else "🔻"

# Actually fetch the first 3 articles for the COMPANY_NAME.
news_response = requests.get(f"{NEWS_ENDPOINT}", params=news_parameters)
news_response.raise_for_status()
news_data = news_response.json()

# Top three articles related to company being researched. In this case - Tesla Inc
top_three_articles = news_data["articles"][:3]
titles = [title["title"] for title in top_three_articles]
content = [body["content"] for body in top_three_articles]

# Send Message
twilio_number = "+1 803 592 3344"
my_number = "+1 224 636 1050"

if percent_change >= 5:
    for i in range(3):
        message = client.messages \
                .create(
                    body=f"{STOCK}: {change_emoji}{percent_change}%\n"
                         f"HEADLINE: {titles[i]}\n"
                         f"BRIEF: {content[i]}",
                    from_=twilio_number,
                    to=my_number,
                )
