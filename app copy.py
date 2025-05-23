from flask import Flask
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import json
import html2text
import random
from datetime import datetime, timedelta
from models import DatabaseService, Commodity
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

app = Flask(__name__)
app.secret_key = "super secret key"


def main(session):
    try:
        with open("data.csv", "w") as f:
            session.query(Commodity).delete()
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
            html = requests.get("https://tradingeconomics.com/commodities", headers=headers)

            if html.status_code != 200:
                print("Failed to retrieve the page")
                return

            soup = bs(html.content, 'html.parser')
            tables = soup.find_all('table')
            table = tables[2]  

            head = table.find('thead').find_all('th')
            body = table.find('tbody').find_all('tr')
            heads = [" "] * len(head)

            for i, th in enumerate(head):
                heads[i % 9] = html2text.html2text(th.text).strip()
            f.write(",".join(heads) + "\n")

            row = [""] * len(head)
            dataset = []
            for tr in body:
                tds = tr.find_all('td')
                for j, td in enumerate(tds):
                    row[j % 9] = html2text.html2text(td.text).strip()
                if len(row) < 9:
                    continue
                new_item = Commodity(
                    agricultural=row[0],
                    price=row[1],
                    day=row[2],
                    percentage=row[3],
                    weekly=row[4],
                    monthly=row[5],
                    ytd=row[6],
                    yoy=row[7],
                    date=row[8]
                )
                session.add(new_item)
                dataset.append(new_item.serialize())
                f.write(",".join(row) + "\n")

            session.commit()
            return [commodity.serialize() for commodity in session.query(Commodity).all()]
    except Exception as e:
        print(f"Error during main execution: {e}")
        session.rollback()
        return {"error": str(e)}


@app.get("/")
def index():
    return "Hello World"

@app.route("/api/commodities")
def get_commodities():
    main(session)
    data = session.query(Commodity).all()
    return json.dumps([d.serialize() for d in data]), {'Content-Type': 'application/json'}

@app.route("/api/analytics")
def analytics():
    data = session.query(Commodity).all()
    df = pd.DataFrame([d.serialize() for d in data])

    for col in ['price', 'percentage', 'weekly', 'monthly', 'ytd', 'yoy']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    result = {
        "average_price": round(df['price'].mean(), 2),
        "min_price": {
            "commodity": df.loc[df['price'].idxmin()]['agricultural'],
            "price": df['price'].min()
        },
        "max_price": {
            "commodity": df.loc[df['price'].idxmax()]['agricultural'],
            "price": df['price'].max()
        },
        "top_gainers": df.sort_values(by='percentage', ascending=False).head(3)[['agricultural', 'percentage']].to_dict(orient='records'),
        "top_losers": df.sort_values(by='percentage').head(3)[['agricultural', 'percentage']].to_dict(orient='records'),
        "ytd": {
            "positive": int((df['ytd'] > 0).sum()),
            "negative": int((df['ytd'] < 0).sum())
        }
    }

    return json.dumps(result), {'Content-Type': 'application/json'}



if __name__ == "__main__":
    try:
        DB = DatabaseService(db_url="mysql+pymysql://root:@localhost:3306/rwacof_analytics")
        DB.drop_all()
        DB.create_all()
        session = DB.create_session()

        scheduler = BackgroundScheduler()
        scheduler.start()

        scheduler.add_job(
            func=lambda: main(session),
            trigger=IntervalTrigger(minutes=30),
            id='refresh_commodities',
            name='Fetch commodity data every 30 minutes',
            replace_existing=True
        )

        atexit.register(lambda: scheduler.shutdown())

        app.run(debug=True)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Session Closed")
        session.close_all()
