# Self-Learning Intelligent Plant Recommendation System

This project implements a hybrid plant recommendation system that combines rule-based filtering with feedback-driven learning. It suggests suitable indoor or outdoor plants to users based on environmental factors, care habits, and personal preferences. Over time, the system adapts to user feedback (likes/dislikes) to improve its recommendations.

## Project Objective

To develop a self-improving plant recommendation engine that:
- Provides suggestions using expert-defined rules
- Learns from user feedback to refine results
- Offers transparency and traceability in plant selection logic

## Features

- Rule-based filtering engine (parsed from JSON rules)
- Feedback-driven model using a lightweight learning engine
- Compatibility with real-time user preferences
- Batch prediction and rule generation modules
- Streamlit-based web interface for interactive use

## Technologies

- Language: Python
- Libraries: scikit-learn, pandas, json, Streamlit
- Learning Model: Feedback-integrated custom recommender
- Data Encoding: DictVectorizer
- Files Used:
  - `parsed_rules.json` – preprocessed plant rules
  - `generated_rules.txt` – human-readable rule descriptions
  - `learning_engine.py / v2` – learning and feedback handling
  - `app.py` – Streamlit UI
  - `plant_dataset.csv` – base plant profile dataset

## How It Works

1. The user fills out a preference form (light, watering, environment, etc.)
2. The system applies rule-based filtering based on parsed rules
3. If feedback data exists, it reorders suggestions using a trained feedback model
4. User selects "like" or "dislike" → feedback stored for future learning
5. Rules and model are updated accordingly

## Project Structure

├── app.py
├── learning_engine.py
├── learning_engine_v2.py
├── rule_parser.py
├── parsed_rules.json
├── generated_rules.txt
├── feedback_data.csv
├── plant_dataset.csv
└── streamlit_app/
├── pages/
├── style/


## How to Run

1. Install required libraries:
pip install -r requirements.txt

2. Launch the Streamlit interface:
streamlit run app.py


3. Interact with the form and give feedback during/after recommendation.

## Future Improvements

- Add user login system for persistent feedback
- Visual similarity analysis (image-based plant matching)
- Integration with a plant care API

## Author

Shakhobiddin Urinov  
Computer Engineering – Dokuz Eylul University  

