from lib.data.features.base_feature import BaseFeature
from lib.constants import MetaConstants
import pandas as pd
import numpy as np

IEX_FIELD_NAMES = MetaConstants.IEXDataFields


class CommonFeatures:

    class Year(BaseFeature):
        def extract(self, df):
            return df[IEX_FIELD_NAMES.date].dt.year

    class DayOfYear(BaseFeature):
        def extract(self, df):
            return df[IEX_FIELD_NAMES.date].dt.day_of_year

    class Weekday(BaseFeature):
        def extract(self, df):
            return df[IEX_FIELD_NAMES.date].dt.day_name()

    class HourOfDay(BaseFeature):
        def extract(self, df):
            return df[IEX_FIELD_NAMES.minute].str[:2].astype(int)

    class MinuteOfHour(BaseFeature):
        def extract(self, df):
            return df[IEX_FIELD_NAMES.minute].str[-2:].astype(int)

    class MinuteBucket(BaseFeature):
        def extract(self, df):
            return df['minute_value'] // 6

    class MinuteOfDay(BaseFeature):
        def __init__(self, starting_hour=9, ending_offset_minutes=30):
            self.starting_hour = starting_hour
            self.ending_offset_minutes = ending_offset_minutes

        def extract(self, df):
            return ((df.hour_of_day - self.starting_hour) * 60) + df[IEX_FIELD_NAMES.minute].str[-2:].astype(int) - 30

    class Timestamp(BaseFeature):
        def extract(self, df):
            return df.date + pd.to_timedelta(df.hour_of_day, 'h') + pd.to_timedelta(df.minute_of_hour, 'm')

    class Sinify(BaseFeature):
        def __init__(self, base_feature: str, period=365):
            """
            This function applies `np.sin` to a column of data, and returns the sin of the
            data with the specified period.

            :param base_feature: The base feature to apply sin to
            :type base_feature: str
            :param period: The period to use for sin.
            E.g. if you are sinifying dayOfYear (ranging from 0 to 365), use 365 as the period.
            :type period: int | float
            """
            self.period = period
            self.base_feature = base_feature

        @property
        def name(self):
            return f'{self.base_feature}_sin({self.period})'

        def extract(self, df):
            return np.sin(df[self.base_feature] * (2 * np.pi / self.period))

    class Cosify(BaseFeature):
        def __init__(self, base_feature: str, period=365):
            """
            This function applies `np.cos` to a column of data, and returns the cos of the
            data with the specified period.

            :param base_feature: The base feature to apply sin to
            :type base_feature: str
            :param period: The period to use for cos.
            E.g. if you are cosifying `dayOfYear` (ranging from 0 to 365), use 365 as the period.
            :type period: int | float
            """
            self.period = period
            self.base_feature = base_feature

        @property
        def name(self):
            return f'{self.base_feature}_cos({self.period})'

        def extract(self, df):
            return np.cos(df[self.base_feature] * (2 * np.pi / self.period))

    class OneHotEncoder(BaseFeature):
        def __init__(self, feature_to_encode: str):
            """
            This object generates a one-hot-encoded representation of a categorical variable.
            :param feature_to_encode: The name of the feature to one-hot-encode
            :type feature_to_encode:
            """
            self.feature_to_encode = feature_to_encode

        def extract(self, df: pd.DataFrame):
            return pd.get_dummies(df[self.feature_to_encode], drop_first=True, prefix=self.feature_to_encode)

