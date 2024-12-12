from flask import Flask,request,jsonify
from flask_cors import CORS
import numpy as np
import spacy
import tensorflow as tf
from tensorflow.keras.models import load_model
import joblib
import os

app=Flask(__name__)
app.secret_key = ''

#Allow CORS from any origin and with specific headers and methods
CORS(app,resources= {r"/*":{"origin": "https://localhost:3000"}})

#load NLP model for text processing
nlp = spacy.load('en_core_web_sm')

#load the trained model and preprocessing objects
model = load_model('server/model/nutri_track.h5')
label_encoders = joblib.load('server/model/label_encoders.pkl')
scaler =joblib.load('server/model/scaler.pkl')

#Initialize conversation context (in memory storage)
conversation_context = {} 

def extract_user_info(user_input):
    doc = nlp(user_input.lower())
    user_info = {}

    #Extract age
    for ent in doc.ents:
        if ent.label_ == 'DATE' or ent.label_ == 'CARDINAL':
            if ent.text.isdigit():
                age = int(ent.text)
                if 0 < age < 120:
                    user_info['age'] = age
                    break

    #Extract gender
    if 'male' in user_input.lower():
        user_info['gender'] = 'male'
    elif  'female' in user_info.lower():
        user_info['gender'] = 'female'

    #Extract activity level
    for level in['low','moderate','high']:
        if level in user_input.lower():
            user_info['activity_level'] = level
            break

    #Extract goal
    for goal in['weight loss','muscle gain','maintenance']:
        if goal in user_input.lower():
            user_info['goal'] = goal
            break

    #Extract weight,height,current_calories
    tokens = user_input.split()
    for token in tokens:
        if 'kg' in token:
            weight = token.replace('kg','').strip()
            if weight.isdigit():
                user_info['weight'] = int(weight)
        if 'cm' in token:
            height = token.replace('cm','').strip()
            if height.isdigit():
                user_info['height']= int(height)
        if 'calories' in token or 'cal' in token:
            calories = token.replace('calories','').replace('cal','').strip()
            if calories.isdigit():
                user_info['current_calories'] = int(calories)

    return user_info

def check_conversation_complete(user_info):
    required_keys = ['age','gender','activity_level','goal','weight','height','current_calories']
    return all(key in user_info for key in required_keys)

#Define the food suggestion function
def suggest_foods(calories,carbs,protein,fat):
    suggestions = []

    if calories < 1800:
        suggestions.append("Consider meals in high protein,like grilled chicken or fish.")
    elif 1800<= calories <=2500:
        suggestions.append("  Incorporate balanced meals with lean meats, whole grains and vegetables")
    else:
        suggestions.append("Include calorie dense food like avocados,nuts and seeds.")

    if carbs < 150:
        suggestions.append("Add complex carbohyrates like sweet potato,quinoa or oats")
    elif carbs > 200:
        suggestions.append(" Reduce high carbs food and focus on vegetable and legumes")

    if protein < 70:
        suggestions.append("Increase protein intake with options like egg , tofu or protein shakes")
    elif carbs > 120:
        suggestions.append("Maintain high protein meal including lean meats and dairy.")

    if fat < 50:
        suggestions.append("Increase healthy fats with olive oil,nuts and seeds.")
    elif fat > 90:
        suggestions.append("Cut down on fat by reducing fried foods and opting for grilled options.")

    return ''.join(suggestions)


@app.route('/predict', methods=['POST','OPTIONS'])
def predict():
    if request.methods == 'OPTIONS':
        #This is a preflight request, send appropriate headers
        response = jsonify({'status': 'CORS preflight'})
        response.headers.add('Access-Control-Allow-Origin','*')
        response.headers.add('Access-Control-Allow-Headers','Content-Type')
        response.headers.add('Access-Control-Allow-Methods','GET, POST, OPTIONS')
        return response,200
    

user_message = request.json.get('message')
user_id = request.json.get('user_id', 'default_user') #In production, use a real user Id
user_info = conversation_context.get(user_id, {})

#Extract and update user info based on the message
extracted_info = extract_user_info(user_message)
user_info.update(extracted_info)
conversation_context[user_id] = user_info

if not check_conversation_complete(user_info):
    missing_info = [key for key in ['age', 'gender', 'activity_level', 'goal', 'weight', 'height', 'current_calories'] if key not in user_info]

    if missing_info:
        prompts = {
            'age': "What is your age?",
            'gender': "What is your gender?",
            'activity_level': "What is your activity level (low, moderate, or high?)",
            'goal': "What is your goal (weight loss, muscle gain, or maintenance?)",
            'weight': "What is your weight (in kg)?",
            'height': "What is your height (in cm)?",
            'current_calories': "What is your current calorie intake?"
        }

        next_question = prompts[missing_info[0]]
        return jsonify({'response': next_question})
    else:
        return jsonify({'response': "All required information is already provided!"})

else:
    # Prepare input data for prediction
    age = user_info['age']
    gender = user_info['gender']
    activity_level = user_info['activity_level']
    goal = user_info['goal']
    weight = user_info['weight']
    height = user_info['height']
    current_calories = user_info['current_calories']

    # Scale numerical features
    scaled_data = scaler.transform([[age, weight, height, current_calories]])

    # Encode categorical features
    gender_encoded = np.array([label_encoders['genders'].transform([gender])[0]]).reshape(1, -1)
    activity_level_encoded = np.array([label_encoders['activity_level'].transform([activity_level])[0]]).reshape(1, -1)
    goal_encoded = np.array([label_encoders['goal_encoded'].transform([goal])[0]]).reshape(1, -1)

    # Combine all features like a single input array
    final_input = np.concatenate((scaled_data, gender_encoded, activity_level_encoded, goal_encoded), axis=1)

    # Make prediction using the model
    predictions = model.predict(final_input)

    # Extract prediction results
    predicted_calories = predictions[0][0]
    predicted_carbs = predictions[0][1]
    predicted_protein = predictions[0][2]
    predicted_fat = predictions[0][3]

    # Log predicted value for debugging
    print(f"Calories: {predicted_calories}, Carbs: {predicted_carbs}, Protein: {predicted_protein}, Fat: {predicted_fat}")

    # Get food suggestion based on the prediction
    food_suggestion = suggest_foods(predicted_calories, predicted_carbs, predicted_protein, predicted_fat)

    # Clear conversation context after prediction
    conversation_context.pop(user_id, None)

    # Return prediction and food suggestion response
    return jsonify({
        'response': f"Suggested daily intake: {predicted_calories:.2f} calories, {predicted_carbs:.2f}g carbs, {predicted_protein:.2f}g protein, {predicted_fat:.2f}g fat.",
        'food suggestion': food_suggestion
    })

if __name__ == '__main__':
    app.run(debug=True)
