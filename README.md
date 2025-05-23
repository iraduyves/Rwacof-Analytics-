# Analytics RCF

## Overview
Analytics RCF is a Flask-based web application designed to fetch, process, and analyze commodity data from external sources. The application provides APIs for retrieving raw commodity data and performing analytics on it. It also includes a scheduled job to refresh the data periodically.

## Features
1. **Data Fetching**: Scrapes commodity data from [Trading Economics](https://tradingeconomics.com/commodities) and stores it in a database.
2. **Data Storage**: Uses a MySQL database to store commodity information.
3. **APIs**:
   - `/api/commodities`: Returns all stored commodity data in JSON format.
   - `/api/analytics`: Provides analytical insights, such as average price, top gainers/losers, and year-to-date (YTD) statistics.
4. **Data Analysis**: Performs statistical analysis on commodity data using pandas.
5. **Background Scheduler**: Automatically refreshes commodity data every 30 minutes using APScheduler.

## Synthetic Pharmacy Sales Data API

This application can generate synthetic pharmaceutical sales data for a single pharmacy in Kigali. The generated dataset simulates daily sales of various products, with the `units_sold` column containing random values independent of all other features. This is useful for testing analytics pipelines or demonstrating data workflows without using real sales data.

### Endpoint: `/api/synthetic_sales`

- **Method:** `GET`
- **Description:** Generates a synthetic sales dataset for a single pharmacy in Kigali between the specified dates.
- **Query Parameters:**
  - `start_date` (string, required): Start date in `YYYY-MM-DD` format.
  - `end_date` (string, required): End date in `YYYY-MM-DD` format.
- **Response:**
  - Returns a CSV file containing the generated synthetic sales data.

#### Example Usage

To generate and download synthetic sales data from January 1, 2023 to January 31, 2023:

```
GET http://127.0.0.1:5000/api/synthetic_sales?start_date=2023-01-01&end_date=2023-01-31
```

The response will be a CSV file with columns such as:
- `date`
- `pharmacy_name`
- `location`
- `product_name`
- `units_sold` (random noise)
- `unit_price`
- `total_sales`

**Note:** All data is randomly generated and does not represent real sales.

---

## Technologies Used
- **Python**: Core programming language.
- **Flask**: Web framework for building APIs and serving the application.
- **BeautifulSoup**: For web scraping commodity data.
- **pandas**: For data manipulation and analysis.
- **MySQL**: Database for storing commodity data.
- **APScheduler**: For scheduling periodic tasks.
- **html2text**: For parsing HTML content into plain text.
  
## Project Structure
```
analytics-rcf/
├── app.py          # Main application file
├── models.py       # Database models (not provided in the prompt)
├── README.md       # Project documentation
└── requirements.txt # Python dependencies (not provided in the prompt)
```

## Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd analytics-rcf
   ```

2. **Install Dependencies**:
   Create a virtual environment and install required packages:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Database**:
   Update the database URL in `app.py`:
   ```python
   DB = DatabaseService(db_url="mysql+pymysql://root:@localhost:3306/rwacof_analytics")
   ```

4. **Run the Application**:
   Start the Flask application:
   ```bash
   python app.py
   ```

5. **Access the Application**:
   - Open your browser and navigate to `http://127.0.0.1:5000/`.
   - Use the following endpoints:
     - `/api/commodities`: Fetch all commodity data.
     - `/api/analytics`: Get analytical insights.

## Tasks Performed
1. **Web Scraping**:
   - Scraped commodity data from an external website.
   - Parsed HTML tables using BeautifulSoup.

2. **Data Storage**:
   - Stored scraped data in a MySQL database using SQLAlchemy models.

3. **API Development**:
   - Developed RESTful APIs to expose commodity data and analytics.

4. **Data Analysis**:
   - Used pandas to calculate average prices, identify top gainers/losers, and compute YTD statistics.

5. **Background Job Scheduling**:
   - Implemented a scheduler to refresh data every 30 minutes.

## Future Enhancements
- Add authentication for API endpoints.
- Improve error handling and logging.
- Create a frontend interface for visualizing analytics.

## License
This project is licensed under the MIT License. See the LICENSE file for details.