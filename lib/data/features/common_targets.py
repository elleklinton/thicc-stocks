import pandas as pd
from lib.data.features.base_feature import BaseFeature
from datetime import timedelta
import numpy as np

class CommonTargets:

    class FutureValue(BaseFeature):

        def __init__(self, feature: str = 'marketLow', target_time_delta: timedelta = timedelta(minutes=1)):
            """
            FutureValue represents the value of a field at some time interval into the future.
            E.g. if you set feature_to_predict='marketLow' and target_time_delta=timedelta(minutes=1), the output of
            this target will be the value of the 'marketLow' feature 1 minute into the future.

            If no matching future timestamp is found for a datapoint, the value for this target on the original
            datapoint will be empty.

            :param feature: The name of the feature to use as the basis for this target
            :type feature: str
            :param target_time_delta: The timedelta into the future that you would like to retrieve
            :type target_time_delta: timedelta
            """
            self.target_time_delta = target_time_delta
            self.feature = feature

        def extract(self, df: pd.DataFrame):
            return df.timestamp.map(lambda row_timestamp: self.__target_helper__(df, row_timestamp))

        def __target_helper__(self, df, row_timestamp):
            try:
                target = df.loc[row_timestamp + self.target_time_delta, self.feature]
                rv = target
                if type(rv) == pd.Series and len(rv) > 0:
                    # In very rare cases, there will be > 1 row for each timestamp. In this case,
                    # take the last matching row. This is very rare so effects are negligible.
                    rv = rv[0]
                assert type(rv) == np.float64
                return rv
            except KeyError:
                # If no matching row is found, return emptiness (None)
                return None

    class FutureValueChange(FutureValue):
        """
        This class inherits from FutureValue, and is equivalent except that it will compute PERCENT CHANGE between
        the original feature_to_predict and the future feature_to_predict instead of the pure future value.
        """

        def extract(self, df):
            target_value: pd.Series = df.timestamp.map(lambda row_timestamp: self.__target_helper__(df, row_timestamp))
            return (target_value - df[self.feature]) / df[self.feature]
