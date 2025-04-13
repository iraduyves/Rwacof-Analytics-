from flask import Flask
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import json
import html2text
from models import DatabaseService, Commodity

app = Flask(__name__)
app.secret_key = "super secret key"

def main(session):
    '''
        Main App
    '''
    with open("data.csv","w") as f:
        session.query(Commodity).delete()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        html = requests.get("https://tradingeconomics.com/commodities", headers=headers)

        if html.status_code != 200:
            print("Failed to retrieve the page")
            return
        soup = bs(html.content, 'html.parser')
     
        table = soup.find('table')

        head = table.find('thead').find_all('th')
        
        body = table.find('tbody').find_all('tr')

        heads = [" "] * len(head)

        i = 0
        for th in head:
            th = html2text.html2text(th.text).strip()
            heads[i%9] = th
            i = i + 1
        header_row = ",".join(heads)
        print(header_row)

        f.write(header_row + "\n")

        row = [""] * len(head)
        dataset = []
        for tr in body:
            tds = tr.find_all('td')
            j = 0
            for td in tds:
                td = html2text.html2text(td.text).strip()
                row[j%9] = td
                j = j + 1
            arow = ",".join(row)
            new_item = Commodity(
                energy=row[0],
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
            session.commit()
            dataset.append(new_item.serialize())
            f.write(arow + "\n")
        return dataset



@app.get("/")
def index():
    return "Hello World"

@app.route("/api/commodities")
def get_commodities():
    return json.dumps(main(session)), {'Content-Type': 'application/json'}


@app.route("/api/analytics")
def analytics():
   
    main(session)
    data = session.query(Commodity).all()
    df = pd.DataFrame([d.serialize() for d in data])
    print(df.head()) 

  
    for col in ['price', 'percentage', 'weekly', 'monthly', 'ytd', 'yoy']:
      df[col] = pd.to_numeric(df[col], errors='coerce')

    average_price = df['price'].mean()
    min_price_row = df.loc[df['price'].idxmin()]
    max_price_row = df.loc[df['price'].idxmax()]

    top_gainers = df.sort_values(by='percentage', ascending=False).head(3)[['energy', 'percentage']]
    top_losers = df.sort_values(by='percentage').head(3)[['energy', 'percentage']]

    ytd_positive = df[df['ytd'] > 0].shape[0]
    ytd_negative = df[df['ytd'] < 0].shape[0]

    result = {
    "average_price": round(average_price, 2),
    "min_price": {
        "commodity": min_price_row['energy'],
        "price": min_price_row['price']
    },
    "max_price": {
        "commodity": max_price_row['energy'],
        "price": max_price_row['price']
    },
    "top_gainers": top_gainers.to_dict(orient='records'),
    "top_losers": top_losers.to_dict(orient='records'),
    "ytd": {
        "positive": ytd_positive,
        "negative": ytd_negative
    }
   }

    return json.dumps(result), {'Content-Type': 'application/json'}

if __name__ == "__main__":
    try:
        DB = DatabaseService(db_url="mysql+pymysql://root:@localhost:3306/rwacof_analytics")
        DB.drop_all()
        DB.create_all()
        session = DB.create_session()
        app.run(debug=True)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Session Closed")
        session.close_all()