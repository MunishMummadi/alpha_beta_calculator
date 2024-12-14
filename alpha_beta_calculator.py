import yfinance as yf
import numpy as np
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta

# Example user performance from statement(day 1-5)
user_performance = [0.005, -0.002, 0.01, -0.003, 0.007]

def fetch_sp500_data():
    """
    Fetch SP500 data for the last 5 trading days using Yahoo Finance.
    Returns a list of daily percentage changes.
    """
    sp500 = yf.Ticker("^GSPC")
    end_date = datetime.today()
    start_date = end_date - timedelta(days=10)  # Fetch 10 days of data to account for weekends/holidays
    data = sp500.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))

    if data.empty:
        raise ValueError("No SP500 data available for the given period.")

    daily_returns = data['Close'].pct_change().dropna().tolist()

    # Check if we have at least 5 trading days
    if len(daily_returns) < 5:
        raise ValueError("Insufficient SP500 data: less than 5 trading days found.")

    print(f"SP500 Daily Returns: {daily_returns}")
    return daily_returns[-5:]

def calculate_alpha_beta(user, market):
    """
    Calculate alpha and beta for user vs. market performance.
    Args:
        user (list): User performance as daily percentage changes.
        market (list): Market (SP500) performance as daily percentage changes.
    Returns:
        tuple: (alpha, beta)
    """
    market = np.array(market)
    user = np.array(user)

    # Debugging Print statement for user and market data
    print(f"User Performance: {user}")
    print(f"Market Performance: {market}")

    # Calculating beta
    covariance = np.cov(user, market)[0, 1]
    market_variance = np.var(market)
    beta = covariance / market_variance

    # Debugging Print statements for covariance and variance
    print(f"Covariance: {covariance}")
    print(f"Market Variance: {market_variance}")

    # Calculating alpha
    market_mean = np.mean(market)
    user_mean = np.mean(user)
    alpha = user_mean - beta * market_mean

    # Debugging Print statements for means and alpha/beta values
    print(f"Market Mean: {market_mean}")
    print(f"User Mean: {user_mean}")
    print(f"Calculated Alpha: {alpha}")
    print(f"Calculated Beta: {beta}")

    return alpha, beta

def push_to_firebase(alpha, beta):
    """
    Push alpha and beta results to Firebase Firestore.
    """
    try:
        # Initialize Firebase
        cred = credentials.Certificate("firebase_credentials.json")
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()

        # Create data payload
        data = {
            "alpha": alpha,
            "beta": beta,
            "timestamp": datetime.now().isoformat()
        }

        # Push to Firestore
        db.collection("performance_metrics").add(data)
        print("Alpha and Beta successfully pushed to Firebase!")
    except Exception as e:
        print(f"Failed to push data to Firebase: {e}")

if __name__ == "__main__":
    try:
        # Fetching data
        sp500_performance = fetch_sp500_data()

        # Calculating alpha and beta
        alpha, beta = calculate_alpha_beta(user_performance, sp500_performance)

        # Push to Firebase
        push_to_firebase(alpha, beta)
    except ValueError as ve:
        print(f"Data Error: {ve}")
    except firebase_admin.exceptions.FirebaseError as fe:
        print(f"Firebase Error: {fe}") 
    except Exception as e:
        print(f"Unexpected Error: {e}\n"
              f"Possible causes could be:\n"
              f"- No internet connection\n"
              f"- Invalid API response from Yahoo Finance\n"
              f"- Firebase credentials misconfigured\n"
              f"Please review the script and try again.")