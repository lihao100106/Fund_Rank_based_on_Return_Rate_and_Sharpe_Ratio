import os
import random
import numpy as np
import pandas as pd
import keras
from keras.models import Sequential
from keras.layers import Dense, LSTM, Dropout
from keras.losses import mean_squared_error
from keras.optimizers import adam_v2
from keras.backend import std
import keras.backend
# random.seed(68)

data_directory = './data/history_Net_Asset_Value'
data_filenames = [_ for _ in os.listdir(data_directory)
                  if '2022-06-15' in _]  # and (_.startswith('hh_') or _.startswith('gp_'))]
prefix_length = len('**_fund_value_')


def data_filename_to_fund_id(filename: str):
    return int(filename[prefix_length:prefix_length+6])


def get_X_Y():
    filename = random.choice(data_filenames)
    csv_file = pd.read_csv(os.path.join(data_directory, filename))
    columns = csv_file.shape[0]
    starting_day = random.randint(0, columns - 5 - 68 - 1)
    # print(f'Chosen {filename} {csv_file.iloc[starting_day+68, 0]}')
    X = csv_file.iloc[starting_day:starting_day+68, 1] - 1
    y = csv_file.iloc[starting_day+68+5, 1] - csv_file.iloc[starting_day+68, 1] - 1
    return X, y


def custom_loss(y_true, y_pred):
    mask = keras.backend.less(y_true, y_pred)  # true < pred gets mask == 1; we will probably suffer a loss
    return (2 + mask) * mean_squared_error(y_true, y_pred)


def train(model: keras.Model=None):
    training_set_size = 6868
    X_train, y_train = [], []
    for i in range(training_set_size):
        if i % 1000 == 0:
            print(f'\rSelecting {i}/{training_set_size} training sample', end='')
        X, y = get_X_Y()
        X_train.append(X)
        y_train.append(y)
    print()
    X_train, y_train = np.array(X_train), np.array(y_train)
    X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))
    
    if not model:
        model = Sequential()
        model.add(LSTM(units=68, return_sequences=True, input_shape=(X_train.shape[1], 1)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=68, return_sequences=True))
        model.add(Dropout(0.25))
        model.add(LSTM(units=68, return_sequences=True))
        model.add(Dropout(0.25))
        model.add(LSTM(units=68))
        model.add(Dropout(0.25))
        model.add(Dense(units=1))
        model.compile(optimizer=adam_v2.Adam(), loss=custom_loss)
    
    model.fit(X_train, y_train, epochs=100, batch_size=64)
    
    model.save('next_week_profit_model')
    return model


# model = train()
model: keras.Model = keras.models.load_model('next_week_profit_model')
# model = train(model)
test_set_size = 68
X_test, y_test = [], []
for i in range(test_set_size):
    X, y = get_X_Y()
    X_test.append(X)
    y_test.append(y)
X_test, y_test = np.array(X_test), np.array(y_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

y_predict = model.predict(X_test)
y_predict = keras.backend.reshape(y_predict, y_predict.shape[0])
print(f'stderror: {std(y_predict - y_test)}')


def get_X(filename: str):
    csv_file = pd.read_csv(os.path.join(data_directory, filename))
    columns = csv_file.shape[0]
    starting_day = columns - 5 - 68
    X = csv_file.iloc[starting_day:starting_day+68, 1] - 1
    return X


print('predicting all funds for the next week')
all_X = []
fund_ids = []
for filename in data_filenames:
    X = get_X(filename)
    all_X.append(X)
    fund_ids.append(data_filename_to_fund_id(filename))
all_X = np.array(all_X)
all_X = np.reshape(all_X, (all_X.shape[0], all_X.shape[1], 1))
y_predict: np.ndarray = model.predict(all_X)
fund_id_and_y = [(fund_id, y + 1) for fund_id, y in zip(fund_ids, y_predict)]
fund_id_and_y.sort(key=lambda item: item[1], reverse=True)
print(fund_id_and_y)
print(y_predict.mean() + 1)
