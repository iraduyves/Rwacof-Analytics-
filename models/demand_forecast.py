import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib

class DemandForecaster:
    def __init__(self, data_path):
        self.data_path = data_path
        self.model = None
        self.feature_names = None

    def load_and_preprocess(self):
        df = pd.read_csv(self.data_path, parse_dates=['Date'])
        # Feature engineering: encode categorical variables, extract season, etc.
        df['Month'] = df['Date'].dt.month
        df['DayOfWeek'] = df['Date'].dt.dayofweek
        df = pd.get_dummies(df, columns=['Province', 'Health_Center', 'ATC_Code', 'Season', 'Supply_Chain_Delay', 'Center_Type', 'Income_Level', 'Population_Density'])
        self.feature_names = [col for col in df.columns if col not in ['units_sold', 'Date', 'Drug_ID', 'sale_timestamp', 'stock_entry_timestamp', 'expiration_date']]
        X = df[self.feature_names]
        y = df['units_sold']
        return X, y, df

    def train(self):
        X, y, _ = self.load_and_preprocess()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        print(f"Test MSE: {mse:.2f}")
        joblib.dump(self.model, 'demand_forecast_model.pkl')
        return mse

    def feature_importance(self):
        if self.model is None:
            self.model = joblib.load('demand_forecast_model.pkl')
        importances = self.model.feature_importances_
        return sorted(zip(self.feature_names, importances), key=lambda x: x[1], reverse=True)

    def predict(self, future_df):
        if self.model is None:
            self.model = joblib.load('demand_forecast_model.pkl')
        X_future = future_df[self.feature_names]
        return self.model.predict(X_future)

    def restock_recommendation(self, days_ahead=7):
        # Example: recommend restock based on predicted demand for next N days
        _, _, df = self.load_and_preprocess()
        last_date = df['Date'].max()
        recommendations = {}
        for drug in df['Drug_ID'].unique():
            drug_df = df[df['Drug_ID'] == drug].copy()
            # Create future dates
            future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days_ahead)
            # Use last known values for categorical features
            last_row = drug_df.iloc[-1]
            future_rows = []
            for date in future_dates:
                row = last_row.copy()
                row['Date'] = date
                row['Month'] = date.month
                row['DayOfWeek'] = date.dayofweek
                future_rows.append(row)
            future_df = pd.DataFrame(future_rows)
            # One-hot encode as before
            future_df = pd.get_dummies(future_df)
            # Align columns
            for col in self.feature_names:
                if col not in future_df:
                    future_df[col] = 0
            future_df = future_df[self.feature_names]
            pred = self.model.predict(future_df)
            recommendations[drug] = int(np.sum(pred))
        return recommendations
