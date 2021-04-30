import numpy as np
import time
from pathlib import Path
import h5py
import json
from lib.constants import DatasetConstants
import pandas as pd


class Dataset:
    def __init__(self, df: pd.DataFrame = None, lookback_size: int = 60, train_fraction: float = 0.8,
                 folder_path: str = None, target_max_threshold: float = 0.03):
        """
        Can be initialized by providing the values: (df, lookback_size, train_fraction) or (folder_path).
        :param df: The dataframe generated by the FeatureGenerator class.
        :type df: pd.DataFrame
        :param lookback_size: The lookback/window size (e.g. how many preceding values to feed into the model)
        :type lookback_size: int
        :param train_fraction: The fraction of data to be used as training data. Typical value is 0.8
        :type train_fraction: float
        :param folder_path: (Optional) The folder path that contains the data already saved from this class
        :type folder_path: str
        :param target_max_threshold: The maximum acceptable target. Use this to remove outliers.
        E.g. if you want to remove all targets above 0.05, `target_max_threshold=0.05`.
        If you don't want to remove have any max threshold, use `target_max_threshold=float('inf')`.
        :type target_max_threshold: float
        """
        if df is not None:
            self.arr = self.__convert_df_to_window_array__(df, lookback_size, target_max_threshold)
            self.train_fraction = train_fraction
            self.column_names = list(df.columns)
            self.f_min, self.f_max = self.__calculate_stats__()
            self.timestamp = int(time.time())
        elif folder_path:
            with open(f"{folder_path}/{DatasetConstants.META_FILENAME}") as file:
                config = json.load(file)
            self.train_fraction = config['train_fraction']
            self.column_names = config['column_names']
            # self.split_ix_train = config['split_ix_train']
            self.timestamp = config['timestamp']

            with h5py.File(f"{folder_path}/{config['data_file']}") as h5f:
                self.arr = h5f[config['arr_name']][:]
                self.f_min = h5f[config['f_min_name']][:]
                self.f_max = h5f[config['f_max_name']][:]
                h5f.close()

    @staticmethod
    def __convert_df_to_window_array__(df: pd.DataFrame, lookback_size: int, target_max_threshold: float = 0.03):
        """
        This function converts our 2-dimensional pandas DataFrame into a 3 dimensional numpy array,
        with the following shape: (num_windows, lookback_size, num_features)

        For example, if your window/lookback size is 60 (you feed the preceding 60 minutes as input),
        and you have 10,000 distinct windows in your dataset, and each datapoint has 25 features,
        your shape would look like (10000, 60, 25).
        """
        # First, iterate over the finite dates (since each window can only contain values for one date)
        data_points = []
        unique_dates = sorted(set(df.index.date))

        for d in unique_dates:
            # Next, extract all of the windows for each given day
            rows_in_day = df.index.date == d
            day_df = df[rows_in_day]

            # Remove days that have unusual data or that don't have enough rows
            if np.any(day_df.iloc[:, -1].abs() >= target_max_threshold) or day_df.shape[0] < lookback_size:
                continue

            i = 0
            max_i = day_df.shape[0] - lookback_size
            while i <= max_i:
                window = day_df.iloc[i:i + lookback_size, :]
                data_points.append(window.values)
                i += 1

        return np.array(data_points)

    def __calculate_stats__(self):
        """
        This function calculates the min and max, column-wise, for every column in the train_X data
        :return: tuple of (feature_min, feature_max)
        :rtype:
        """
        f_min = self.train_X.min(axis=1).min(axis=0)
        f_max = self.train_X.max(axis=1).max(axis=0)
        return f_min, f_max

    @property
    def split_ix_train(self):
        return int(self.arr.shape[0] * self.train_fraction)

    @property
    def split_ix_val(self):
        val_weight = 2/3
        return self.split_ix_train + int((self.arr.shape[0] * (1 - self.train_fraction)) * val_weight)

    @property
    def train(self):
        return self.arr[:self.split_ix_train, :, :]

    @property
    def val(self):
        return self.arr[self.split_ix_train:self.split_ix_val:, :, :]

    @property
    def test(self):
        return self.arr[self.split_ix_val:, :, :]

    @property
    def train_X(self):
        return self.train[:, :, :-1]

    @property
    def train_y(self):
        return self.train[:, :, -1:]

    @property
    def val_X(self):
        return self.val[:, :, :-1]

    @property
    def val_y(self):
        return self.val[:, :, -1:]

    @property
    def test_X(self):
        return self.test[:, :, :-1]

    @property
    def test_y(self):
        return self.test[:, :, -1:]

    @property
    def num_inputs(self):
        return len(self.column_names)

    def save_to_disk(self, name: str = "data"):
        """
        This function saves the dataset to exported_data/datasets/{name}/*. It preserves the state of
        the Dataset object completely. The core data is efficiently saved via h5py.

        After saving, you can re-instantiate the saved class with the build-in init function by passing
        the `folder_path` at initialization, which is the same as the `name` passed to this function.

        :param name: The name to reference the data by, usually the stock ticker symbol.
        :type name:
        :return: Returns the path to the folder where the dataset is stored
        :rtype: str
        """

        base_path = f"{DatasetConstants.OUTPUT_DIR}/{self.timestamp}-{name}"

        metadata = {
            "name": name,
            "data_shape": self.arr.shape,
            "train_fraction": self.train_fraction,
            "column_names": self.column_names,
            "timestamp": self.timestamp,
            "data_file": "data.h5",
            "meta_file": DatasetConstants.META_FILENAME,
            "arr_name": "arr",
            "f_min_name": "f_min",
            "f_max_name": "f_max"
        }

        Path(base_path).mkdir(parents=True, exist_ok=True)

        with h5py.File(f'{base_path}/{metadata["data_file"]}', 'w') as array_file:
            array_file.create_dataset(metadata['arr_name'], data=self.arr)
            array_file.create_dataset(metadata['f_min_name'], data=self.f_min)
            array_file.create_dataset(metadata['f_max_name'], data=self.f_max)
            array_file.close()

        with open(f'{base_path}/{metadata["meta_file"]}', 'w') as outfile:
            json.dump(metadata, outfile, ensure_ascii=False, indent=4)

        print(f"Successfully saved dataset to `{base_path}/*`")
        return base_path

    def __verify_df__(self, df):
        assert df[:, :, :self.num_inputs].shape[1:] == self.arr[:, :, :self.num_inputs].shape[1:]

    def transform(self, df):
        """
        This function applies the MinMax scaler column-wise to the dataframe passed in. It uses only the training
        data statistics that were computed during initialization, so the same transformation will be applied to
        all data. This will give each column a mean of 0 and standard deviation of 1.
        """
        self.__verify_df__(df)
        return (df[:, :, :self.num_inputs] - self.f_min) / (self.f_max - self.f_min)

    def reverse_transform(self, df):
        """
        This function inverts the transform function.
        E.g. reverseTransform(transform(df)) == transform(reverse_transform(df))
        """
        self.__verify_df__(df)
        return df[:, :, :self.num_inputs] * (self.f_max - self.f_min) + self.f_min