import pandas as pd
from lib.constants import MetaConstants
from lib.data.features.base_feature import BaseFeature
from lib.data.features.common_features import CommonFeatures

IEX_FIELD_NAMES = MetaConstants.IEXDataFields


class FeatureGenerator:
    def __init__(self, filename: str, auto_clean: bool = True, parse_dates: bool = True):
        """
        This function initializes the FeatureGenerator object. FeatureGenerator is useful for generating additional
        features from the raw IEXCloud output data. FeatureGenerator allows custom features to be added by implementing
        the BaseFeature class (lib.data.features.base_feature.BaseFeature).

        :param filename: The name of the csv file that contains the raw data from IEXCloud, generated from the scraper.
        :type filename: str
        :param auto_clean: Whether the data should be auto-cleaned upon initialization.
        If `auto_clean=False`, you can still clean the data by calling the method `feature_generator.__cleanup__()`
        :type auto_clean: bool
        :param parse_dates: Whether or not to parse the IEXCloud dates into properly typed date fields.
        If set to true, the data will be sorted by timestamp and the following fields will be generated:
            - `year`
            - `day_of_year`
            - `weekday`
            - `hour_value`
            - `minute_value`
            - `minute_bucket`
            - `minutes_elapsed_in_day`
            - `timestamp`
        :type parse_dates: bool
        """
        self.df = pd.read_csv(filename)
        self.df[IEX_FIELD_NAMES.date] = pd.to_datetime(self.df[IEX_FIELD_NAMES.date])
        self.df.loc[:, 'exclude'] = False
        self.data_fields = [
            'marketHigh', 'marketLow', 'marketAverage', 'marketVolume', 'marketNotional',
            'marketNumberOfTrades', 'marketOpen', 'marketClose', 'marketChangeOverTime'
        ]

        if auto_clean:
            self.__cleanup__()

        if parse_dates:
            self.__parse_dates__()

    def __parse_dates__(self):
        """
        This function adds the following features to the dataframe:
            - `year`
            - `day_of_year`
            - `weekday`
            - `hour_value`
            - `minute_value`
            - `minute_bucket`
            - `minutes_elapsed_in_day`
            - `timestamp`
        """
        self.build_feature(CommonFeatures.Year())
        self.build_feature(CommonFeatures.DayOfYear())
        self.build_feature(CommonFeatures.Weekday(), should_export=False)
        self.build_feature(CommonFeatures.HourOfDay())
        self.build_feature(CommonFeatures.MinuteOfHour())
        self.build_feature(CommonFeatures.MinuteOfDay())
        self.build_feature(CommonFeatures.Timestamp(), should_export=False)

        # Finally, ensure that our data is sorted by the timestamp
        self.df = self.df.sort_values('timestamp')
        self.df = self.df.set_index('timestamp')
        self.df['timestamp'] = self.df.index

    def __cleanup__(self):
        """
        This function identifies "bad rows" in the data (e.g. rows with 0 volume), and then replaces the bad values with
        pure emptiness (None) to mark them as incomplete rows. Since these rows are 'incomplete'/missing data, they will
        be removed in a later preprocessing step before the final model inputs are generated.
        """
        # Find "bad rows", for example rows with 0 volume/numberOfTrades to make data more stable
        bad_rows = self.df[IEX_FIELD_NAMES.numberOfTrades] <= 0
        bad_rows = bad_rows | (self.df[IEX_FIELD_NAMES.marketNumberOfTrades] <= 0)
        bad_rows = bad_rows | (self.df[IEX_FIELD_NAMES.marketVolume] <= 0)
        bad_rows = bad_rows | (self.df[IEX_FIELD_NAMES.volume] <= 0)

        # Purge the data on these rows, so they can be forward/backward filled in the next step
        self.df.loc[bad_rows, self.data_fields[2:]] = None

        # Forward fill rows with bad values and then backward fill to make sure everything is covered
        self.df = self.df.fillna(method='ffill').fillna(method='bfill')

    def build_features(self, features: list[BaseFeature], remove_missing_rows: bool = True,
                       should_export: bool = True):
        """
        This is a MUTATING function that takes in a list of BaseFeature objects, and creates new columns in the
        dataframe with the computed feature.

        If `remove_bad_rows=True`, this function label the rows with a missing target to be removed. This happens, for example,
        if you try to get the stock price 1 hour into the future, but there are only 30 minutes left in the market. For
        most use cases, remove_bad_rows should be set to True.


        :param features: The list of features to generate
        :type features: list[str]
        :param remove_missing_rows: Whether to mark the rows with missing targets as droppable
        :type remove_missing_rows: bool
        :param should_export: Whether this feature should be included in the exported data.
        :type should_export: bool
        """
        for f in features:
            self.build_feature(f, remove_missing_rows, should_export)

    def build_feature(self, feature: BaseFeature, remove_missing_rows: bool = True,
                      should_export: bool = True):
        """
        This is a MUTATING function that takes in a BaseFeature, and creates a new column, base_feature, in the
        dataframe with the computed feature.

        If `remove_bad_rows=True`, this function label the rows with a missing target to be removed. This happens, for example,
        if you try to get the stock price 1 hour into the future, but there are only 30 minutes left in the market. For
        most use cases, remove_bad_rows should be set to True.

        :param should_export: Whether this feature should be included in the exported data.
        :type should_export: bool
        :param feature: The feature to generate
        :type feature: BaseFeature
        :param remove_missing_rows: Whether to mark the rows with missing targets as droppable
        :type remove_missing_rows: bool
        """
        assert feature.name not in self.df.columns, f'Error: feature {feature.name} is already in dataframe.'
        assert isinstance(feature, BaseFeature), f'Error: expected BaseFeature but got {type(feature)}.'

        computed_feature = feature.extract(self.df)

        if isinstance(computed_feature, pd.Series):
            computed_feature = pd.concat([computed_feature], axis=1)
            computed_feature.columns = [feature.name]
            feature_names = [feature.name]
        else:
            feature_names = list(computed_feature.columns)

        self.df = pd.concat([self.df, computed_feature], axis=1)

        if remove_missing_rows:
            missing_rows = pd.isnull(self.df).any(axis=1)
            self.df.loc[missing_rows, 'exclude'] = True

        if should_export:
            self.data_fields.extend(feature_names)

    def export(self, target_feature: str, features_to_exclude: list[str] = None):
        """
        This function export the data as a pandas DataFrame.

        :param target_feature: The feature you would like to predict.
        This feature will be placed at the last column-wise index.
        :type target_feature: str
        :param features_to_exclude: Any features you want to exclude from the final exported numpy array.
        :type features_to_exclude: list[str]
        :return: Returns a dataframe of the data you would like to export.
        :rtype: pd.DataFrame
        """
        if not features_to_exclude:
            features_to_exclude = [target_feature]
        else:
            features_to_exclude.append(target_feature)

        features_to_exclude = [f.lower() for f in features_to_exclude]

        final_cols = list(filter(lambda x: x.lower() not in features_to_exclude, self.data_fields)) + [target_feature]

        # assert not any(pd.isna(to_return)), 'Error: rows with nan values are present in the base DataFrame.'

        return self.df.loc[~self.df.exclude, final_cols].astype(float)
