
import pandas as pd
from bs4 import BeautifulSoup as bs
import requests
import json
import html2text
from models import DatabaseService, Commodity

def main():
    '''
        Main App
    '''
    with open("data.csv","w") as f:
        print("Application started successfullyyyyy.")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        html = requests.get("https://tradingeconomics.com/commodities", headers=headers)

        if html.status_code != 200:
            print("Failed to retrieve the page")
            return
        soup = bs(html.content, 'html.parser')
        # Get the table
        table = soup.find('table')

        head = table.find('thead').find_all('th')
        
        body = table.find('tbody').find_all('tr')

        # print(head)
        print(len(head))
        # return
        heads = [" "] * len(head)
        rows = [{}] * len(head)
        i = 0
        for th in head:
            th = html2text.html2text(th.text).strip()
            heads[i%9] = th
            i = i + 1
        header_row = ",".join(heads)

        print(header_row)

        f.write(header_row + "\n")

        row = [""] * len(head)
        for tr in body:
            tds = tr.find_all('td')
            j = 0
            for td in tds:
                td = html2text.html2text(td.text).strip()
                row[j%9] = td
                j = j + 1
            arow = ",".join(row)
            f.write(arow + "\n")
        print("Data written to file successfullyyyyy.")

main()