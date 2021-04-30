import pyEX
import json
from dateutil.parser import parse
from datetime import timedelta
import pandas as pd
from lib.constants import ScraperConstants
from lib.scraper.ticker import Ticker
from pathlib import Path
import time

CONFIG_CONSTANTS = ScraperConstants.Config


class Scraper:
    def __init__(self, config_file: str = 'config/iexcloud-config.json', should_print: bool = True):
        """
        This function initializes the Scraper class, which is a scraping object designed to scrape data from IEXCloud.

        :param config_file: A configuration file with IEX credentials.
        Must contain keys: {'api_token':str, 'api_secret':str, 'sandbox':str}.
        See `config/iexcloud-config.json` as an example.
        :type config_file: str
        :param should_print: Whether to print the status of scraping or not.
        :type should_print: bool
        """
        self.timestamp = int(time.time())

        with open(config_file) as file:
            config = json.load(file)

        self.access_token = config[CONFIG_CONSTANTS.API_TOKEN]
        self.access_secret = config[CONFIG_CONSTANTS.API_SECRET]
        self.sandbox_mode = config[CONFIG_CONSTANTS.SANDBOX_MODE]
        self.stage = ScraperConstants.Stage.SANDBOX if self.sandbox_mode else ScraperConstants.Stage.STABLE
        self.should_print = should_print

        self.client = pyEX.Client(
            api_token=self.access_secret,
            version=self.stage
        )

    def __get_intraday_price_helper__(self, ticker, date):
        """
        :return: Returns a tuple (should_continue, df), with whether the scraping should be continued (boolean) as the
        first element, and a DataFrame as the second element.
        """
        try:
            df = self.client.chartDF(ticker, date=date, sort=ScraperConstants.SortMethods.ASC)
        except Exception as e:
            if self.__should_proceed__(e):
                return self.__get_intraday_price_helper__(ticker, date)
            else:
                return False, pd.DataFrame()
        return True, df

    def get_intraday_stock_data(self, ticker: Ticker, start: str, end: str, time_delta: timedelta = timedelta(days=1),
                                save_data: bool = True):
        """
        This function uses the IEXCloud API to fetch stock data in 1-minute intervals, with the time_delta being the
        interval, in stock time, of each request.

        :param ticker: The stock ticker to fetch.
        :type ticker: Ticker
        :param start: The starting date (YYYY-MM-DD) to fetch data from (e.g. '2020-01-01')
        :type start: str
        :param end: The ending date (YYYY-MM-DD) to fetch data from (e.g. '2020-12-31')
        :type end: str
        :param time_delta: The amount of time of stock data to fetch in each request to IEXCloud.
        Default is 1 day, timedelta(days=1).
        :type time_delta: timedelta
        :param save_data: Boolean value of whether or not to save the data to disk upon completion. Data will be saved
        in $project_root/data/scraping/timestamp/TICKER.csv
        :type save_data: bool
        :return: Returns a Tuple of:
            Tuple Element 1 (pd.DataFrame): Pandas DataFrame with one row for every record/minute returned by IEXCloud
            Tuple Element 2 (str): filename where data is stored. If save_data=False, this will be None.
        :rtype: (pd.DataFrame, str)
        """
        thicc_df = pd.DataFrame()
        start_date = parse(start)
        end_date = parse(end)

        curr_date = start_date
        while curr_date <= end_date:
            if self.should_print:
                print(f"Scraping {curr_date}")

            should_continue, res = self.__get_intraday_price_helper__(ticker.ticker, curr_date)
            if not should_continue:
                break

            curr_date += time_delta
            thicc_df = pd.concat([thicc_df, res]) if thicc_df.size > 0 else res

        filename = None
        if save_data:
            filename = self.__save_data__(thicc_df, ticker)

        return thicc_df, filename

    def __should_proceed__(self, error):
        if self.should_print:
            print(f"Error during data scraping: {error}\n\n")

        x = input('Continue? (Y/N)')
        return x.upper() == 'Y'

    def __save_data__(self, df, ticker):
        directory = f"{ScraperConstants.OUTPUT_DIR}/{self.timestamp}/"
        Path(directory).mkdir(parents=True, exist_ok=True)
        filename = f"{ticker.ticker}.csv"

        df.to_csv(directory + filename)
        if self.should_print:
            print(f"Successfully saved result to {directory + filename}")

        return directory + filename
