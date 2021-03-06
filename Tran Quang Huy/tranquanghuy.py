# -*- coding: utf-8 -*-
"""TranQuangHuy.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1JkxtRFjGI4PTbFvrl4MdmAi8rzYpP9w0
"""

from google.colab import drive 
drive.mount('/content/mydrive/')
import sys
sys.path.append("/content/mydrive/My Drive/app/")

!pip install -U -q PyDrive

from __future__ import absolute_import, division, print_function
import numpy as np
import os
import time
import tensorflow as tf
import cv2 #
import matplotlib.pyplot as plt 
import functools
from random import shuffle #
from tensorflow import keras
from array import array
from vgg16 import VGG16
from keras.preprocessing import image
from keras.applications.imagenet_utils import preprocess_input
from imagenet_utils import decode_predictions
from keras.layers import Dense, Activation, Flatten
from keras.layers import merge, Input
from keras.models import Model
from keras.utils import np_utils
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from google.colab import auth
from oauth2client.client import GoogleCredentials
from keras.backend.tensorflow_backend import set_session

auth.authenticate_user()
gauth = GoogleAuth()
gauth.credentials = GoogleCredentials.get_application_default()
drive = GoogleDrive(gauth)

# Loading the training data
PATH = os.getcwd()
# Define data path
data_path = PATH + '/mydrive/My Drive/app' +'/dataset'
data_dir_list = os.listdir(data_path)


labels = {}

# Loop through all data and set the path for each image in data set
for c in data_dir_list:
    img_list = os.listdir(data_path + "/" + c)
    
    for image in img_list:
        if c == 'bullmastiff':
          labels[c + "/" + image] = 0
        elif c == 'chowchow':
          labels[c + "/" + image] = 1
        elif c == 'pug':
          labels[c + "/" + image] = 2
        elif c == 'maltese':
          labels[c + "/" + image] = 3
        elif c == 'huskysibir':
          labels[c + "/" + image] = 4
        elif c == 'dachshund':
          labels[c + "/" + image] = 5
        elif c == 'dalmatian':
          labels[c + "/" + image] = 6
        elif c == 'corgi':
          labels[c + "/" + image] = 7
        elif c == 'chihuahua':
          labels[c + "/" + image] = 8
        elif c == 'yorkshire':
          labels[c + "/" + image] = 9

# Return image with w*h: 224*224
def PreprocessImage(img):
  w,h = 224, 224 
  
  img = cv2.resize(img, (w, h))
  img = img/255. 
  
  return img

# Return yield a 32 images to train each batch 
def ImageGenerator(input_ids, batch_size = 32):
  
  while True:
    batch_paths = np.random.choice(a= input_ids, size = batch_size)
    
    batch_input = []
    batch_output = []
    
    
    
    for input_id in batch_paths:
      input = cv2.imread(data_path + "/" + input_id)
      output = labels[input_id]
      
      input = PreprocessImage(input)
      
      batch_input += [input]
      batch_output += [output]
      
    batch_x = np.array(batch_input)
    batch_y = np.array(batch_output)
    
    batch_x = np.reshape(batch_x, (batch_size, 224, 224, 3))
    batch_y = np.reshape(batch_y, (batch_size,1))
    
    # One-hot encode the labels
    batch_y = np_utils.to_categorical(batch_output, num_classes)
    
    # Yield the batch to the calling function
    yield (batch_x, batch_y)

batch_size = 32 

img_ids = list(labels.keys())
shuffle(img_ids)

split = int(0.8 * len(img_ids))

# Split data tranning set and validiton set img[x] = index of class (x: path to some image)
train_ids = img_ids[0:split]
valid_ids = img_ids[split:]

train_generator = ImageGenerator(train_ids, batch_size = batch_size)
valid_generator = ImageGenerator(valid_ids, batch_size = batch_size)

config = tf.ConfigProto()
config.gpu_options.allow_growth=True
sess = tf.Session(config=config)

# Define the number of classes
num_classes = 10

image_input = Input(shape=(224, 224, 3))

# Load model vgg16 
model = VGG16(input_tensor=image_input, include_top=True, weights='imagenet')

#model.summary()

last_layer = model.get_layer('block5_pool').output
x= Flatten(name='flatten')(last_layer)
x = Dense(128, activation='relu', name='fc1')(x)
x = Dense(128, activation='relu', name='fc2')(x)
out = Dense(num_classes, activation='softmax', name='output')(x)
custom_vgg_model2 = Model(image_input, out)
custom_vgg_model2.summary()

#create the path to save weighted 
checkpoint_path = PATH + '/mydrive/My Drive/app/cp.ckpt'

checkpoint_dir = os.path.dirname(checkpoint_path)

# Create checkpoint callback
cp_callback = tf.keras.callbacks.ModelCheckpoint(checkpoint_path, save_weights_only=True, verbose=1)

# Freeze all the layers except the dense layers
for layer in custom_vgg_model2.layers[:-3]:
  layer.trainable = False

#custom_vgg_model2.summary()

top3_acc = functools.partial(keras.metrics.top_k_categorical_accuracy, k=3)

top3_acc.__name__ = 'top3_acc'

custom_vgg_model2.compile(loss='categorical_crossentropy',optimizer='adadelta',metrics=['accuracy', 'top_k_categorical_accuracy', top3_acc])

#t=time.time()
# t = now()

# Compute trainning and validtion step for each epoch
train_steps = len(train_ids) // batch_size 
valid_steps = len(valid_ids) // batch_size 
           
# Start trainning ...
custom_vgg_model2.fit_generator(train_generator, validation_data= valid_generator, epochs = 20, steps_per_epoch = train_steps, validation_steps = valid_steps, callbacks = [cp_callback])

# Save model to predict 
custom_vgg_model2.save(PATH + '/mydrive/My Drive/app/my_model.h5')


#print('Training time: %s' % (t - time.time()))

# Load model saved to predict 
new_model = keras.models.load_model(PATH + '/mydrive/My Drive/app/my_model.h5')

# Load weight and evaluate model 
new_model.load_weights(checkpoint_path)
(loss, accuracy) = new_model.evaluate_generator(valid_generator, steps = valid_steps, verbose=1)
print("[INFO] loss={:.4f}, accuracy: {:.4f}%".format(loss, accuracy * 100))