# -*- coding: utf-8 -*-
"""Submission_TS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1QcEhrwcMBkswrlmOnkZodfQYmyojzAg8

# Time Series Model
### Beberapa gambaran dari proses dan hasil dalam submission ini yaitu,
1. Dataset memiliki 20000 sampel.
2. Validation set sebesar 20% dari total dataset.
3. Menggunakan LSTM dan Embedding dalam model.
4. Menggunakan model sequential.
5. Menggunakan Learning Rate pada Optimizer.
6. Mengimplementasikan callback.
7. MAE < 10% skala data.
8. Membuat plot loss dan akurasi pada saat training dan validation.

## 1. Download Dataset kemudian ekstrak.
"""

!wget --no-check-certificate \
  http://archive.ics.uci.edu/ml/machine-learning-databases/00235/household_power_consumption.zip \
  -O "drive/My Drive/Pengembangan-ML/Submission_TS/dataset/household_power_consumption.zip"

import zipfile

# melakukan ekstraksi pada file zip
local_zip = 'drive/My Drive/Pengembangan-ML/Submission_TS/dataset/household_power_consumption.zip'
zip_ref = zipfile.ZipFile(local_zip, 'r')
zip_ref.extractall('drive/My Drive/Pengembangan-ML/Submission_TS/dataset')
zip_ref.close()

"""## 2. Import library yang dibutuhkan. Read file sebagai DataFrame"""

# Commented out IPython magic to ensure Python compatibility.
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
import datetime, os
# %load_ext tensorboard

df = pd.read_csv('drive/My Drive/Pengembangan-ML/Submission_TS/dataset/household_power_consumption.txt', sep=';', parse_dates={'Date_Time' : ['Date', 'Time']}, infer_datetime_format=True, 
                 low_memory=False, na_values=['nan','?'])

df.head()

df.info()

"""## 3. Pre-Processing.
Data yang disediakan berjumlah 2 juta. Tetapi, hanya 10000-20000 data saja yang akan digunakan.
"""

df.shape

# variable
prediksi = 'Global_active_power' #Kolom yang akan di training
n = 20000 # Jumlah data

df = df.head(n).reset_index(drop=True)
df.shape

"""Drop column selain Date_Time dan Global_active_power."""

df.drop(df.columns.difference(['Date_Time', prediksi]), 1, inplace=True)

"""Pengecekan missing value"""

df.isnull().sum()

"""pengisian missing value dengan rata-rata dari data."""

df[prediksi].fillna(df[prediksi].mean(), inplace = True)

df.isnull().sum()

dates = df['Date_Time'].values
temp  = df[prediksi].values

"""ploting untuk mengetahui distribusi data."""

plt.figure(figsize=(15,5))
plt.plot(dates, temp)
plt.xlabel('Date Time')
plt.title(prediksi,
          fontsize=20);

"""## 4. Training
Mendefinisikan function window dari data.
"""

def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[1:]))
    return ds.batch(batch_size).prefetch(1)

"""Split data untuk training dan testing 20 %. Karena untuk permasalahan time series maka pembagian data tidak secara random. Oleh karena itu terdapat penambahan ```shuffle = False ```"""

from sklearn.model_selection import train_test_split
data_train, data_test = train_test_split(temp, test_size=0.2, shuffle=False)

train_set = windowed_dataset(data_train, window_size=60, batch_size=100, shuffle_buffer=1000)
test_set = windowed_dataset(data_test, window_size=60, batch_size=100, shuffle_buffer=1000)

"""Create Model"""

def create_model():
  return tf.keras.models.Sequential([
    tf.keras.layers.LSTM(64, return_sequences=True),
    tf.keras.layers.LSTM(64),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1),
  ])

"""Callback untuk mae < 10% skala data"""

skala = (df[prediksi].max()-df[prediksi].min())*10/100
print('Data tertinggi : ', df[prediksi].max())
print('Data terendah : ', df[prediksi].min())
print('10% dari sekala data adalah ',skala)
class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if(logs.get('val_mae') is not None and logs.get('val_mae') <= skala and logs.get('mae') <= skala):
      print("\nMAE Training dan Testing mencapai  < 10% skala data!")
      self.model.stop_training = True
callbacks = myCallback()

"""Trainning dan Testing"""

def train_model():

  model = create_model()
  optimizer = tf.keras.optimizers.SGD(learning_rate = 1.0000e-05, momentum=0.9) # menggunakan learning rate
  model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])
  
  logdir = os.path.join("logs", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
  tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=logdir, histogram_freq=1)

  history = model.fit(train_set, validation_data=(test_set), verbose=2, epochs=500, callbacks=[callbacks, tensorboard_callback])

train_model()

"""## 5. Plotting
penggunaan tensorboard untuk plotting
"""

# Commented out IPython magic to ensure Python compatibility.
# %tensorboard --logdir logs

