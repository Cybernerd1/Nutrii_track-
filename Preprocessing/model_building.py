import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential 
from tensorflow.keras.layers import Dense
import joblib 
from preprocessing.data_preparation import x_train,x_test,y_train,y_test

#print shape of traning data for verification
print(f"x_train shape: {x_train.shape}")
print(f"y_train shape: {y_train.shape}")

#define the neural network model with multiple outputs
model = Sequential([
    Dense(128, input_shape=(x_train.shape[1],),activation='relu'),
    Dense(64, activation='relu'),
    Dense(32, activation='relu'),
    Dense(4) #Four outputs : suggested calories,carbs,protein and fat.
])

#compile the model using mean squared error for regression tasks
model.compile(optimizer = 'adam', loss='mean_squared_error',metrics=['mae'])

#Train the model
model.fit(x_train,y_train,epochs=20,batch_size=10,validation_data=(x_test,y_test))

#evaluate the model on the test set to see its performance
loss,mae = model.evaluate(x_test,y_test)
print(f"Test Loss: {loss}, Test Mae: {mae}")

#make predictions on test data
predictions = model.predict(x_test)

#extract predictions from the first test sample
predicted_calories = predictions[0][0]
predicted_carbs = predictions[0][1]
predicted_protein = predictions[0][2]
predicted_fat = predictions[0][3]

print(f"Predicted Calories: {predicted_calories:.2f}")
print(f"Predicted Carbs: {predicted_carbs:.2f}g")
print(f"Predicted Protien: {predicted_protein:.2f}g")
print(f"Predicted Fat: {predicted_fat:.2f}g")

#Save the trained model
model.save('server/model/nutri_track.h5')

print("model training completed,save and food suggestions generated.")