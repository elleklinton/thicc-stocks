from lib.data.feature_generator import FeatureGenerator
from lib.data.features.common_features import CommonFeatures
from lib.data.features.common_targets import CommonTargets
from lib.scraper.ticker import CommonTickers
from lib.data.dataset import Dataset
from lib.scraper.scraper import Scraper

from datetime import timedelta
import numpy as np
import pandas as pd

# Step 1: Scrape the stock data from IEXCloud
s = Scraper(
    config_file='lib/scraper/config/iexcloud-sandbox-private.json'
)
disney_data, disney_filename = s.get_intraday_stock_data(
    ticker=CommonTickers.DISNEY,
    start='2021-04-20',
    end='2021-04-29',
    time_delta=timedelta(days=1),
    save_data=True
)

# Step 2: Clean the data and generate new features from the data
# This is a dummy data file, stock data here has been randomized

# Initialize the feature generator
# sample_iex_filename = 'exported_data/scraping/1619661954/T.csv'
feature_generator = FeatureGenerator(
    filename=disney_filename,
    auto_clean=True,
    parse_dates=True
)
# Add some new features to the data
feature_generator.build_features(
    [
        CommonFeatures.Sinify('day_of_year', period=365),
        CommonFeatures.Cosify('day_of_year', period=365),
        CommonFeatures.Sinify('minute_of_day', period=(60 * 24)),
        CommonFeatures.Cosify('minute_of_day', period=(60 * 24)),
        CommonFeatures.OneHotEncoder('weekday'),
        CommonFeatures.OneHotEncoder('hour_of_day')
    ]
)
# Generate our target(s)
feature_generator.build_features(
    [
        CommonTargets.FutureValue(feature='marketLow', target_time_delta=timedelta(minutes=1)),
        CommonTargets.FutureValueChange(feature='future_value')  # This is the feature generated directly above
    ]

)

# Create a dataset from our cleaned and featurized data

# We don't want to include the original value of the one-hot-encoded variables
features_to_exclude = ['weekday', 'hour_of_day']
exported_data = feature_generator.export(
    target_feature='future_value_change',
    features_to_exclude=features_to_exclude
)

dataset = Dataset(
    df=exported_data,
    train_fraction=0.7,
    target_max_threshold=float('inf')
)

data_path = dataset.save_to_disk(CommonTickers.ATT.ticker)

# Similarly, we can re-instantiate this data from disk like this:
dataset_from_disk = Dataset(folder_path=data_path)

