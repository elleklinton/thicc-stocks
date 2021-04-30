import re
import pandas as pd


class BaseFeature(object):
    """
    This class represents a feature that can be generated from input data.

    To use BaseFeature, create a new class that inherits the BaseFeature object and implements the `extract` method like this:

    ```
    class SampleFeature(BaseFeature):
        ...
        ...
        def extract(self, df):
            return ...
    ```
    """

    __string_pattern__ = re.compile(r'(?<!^)(?=[A-Z])')

    def extract(self, df: pd.DataFrame):
        """
        This function take in the original source dataframe, and returns either:
            - a pandas Series of the same length as the number of rows in the original dataframe
            or
            - a dataframe with the same number of rows as the original dataframe,
              where each column represents a new feature

        :param df:
        :type df:
        :return: pd.Series or pd.DataFrame
        :rtype:
        """
        assert False, "Error: this function must be implemented in a BaseFeature"

    @property
    def name(self):
        # Returns a snake_case version of the class name
        return self.__string_pattern__.sub('_', type(self).__name__).lower()
