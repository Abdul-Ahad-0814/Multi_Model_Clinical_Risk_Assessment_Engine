from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import joblib

app = Flask(__name__)
app.secret_key = "clinical-risk-engine-secret"

# =====================
# Load models (FITTED)
# =====================
heart_stage1 = joblib.load("models/Heart_Stage1_Model.pkl")
diabetes_stage1 = joblib.load("models/Diabetes_Stage1_Model.pkl")
hypertension_stage1 = joblib.load("models/Hypertension_Stage1_Model.pkl")

heart_stage2 = joblib.load("models/Heart_Stage2_Model.pkl")
diabetes_stage2 = joblib.load("models/Diabetes_Stage2_Model.pkl")
hypertension_stage2 = joblib.load("models/Hypertension_Stage2_Model.pkl")

# =====================
# Stage-1 columns
# =====================
STAGE1_COLS = [
    "age", "gender", "systolic_bp", "diastolic_bp",
    "glucose", "cholesterol", "bmi",
    "smoking", "alcohol", "family_history"
]

# =====================
# Stage-1 screening
# =====================
def stage1_screen(df):
    scores = {
        "heart": heart_stage1.predict_proba(df)[0][1],
        "diabetes": diabetes_stage1.predict_proba(df)[0][1],
        "hypertension": hypertension_stage1.predict_proba(df)[0][1]
    }
    top_disease = max(scores, key=scores.get)
    return top_disease, scores

# =====================
# Stage-2 risk calculation
# =====================
def stage2_predict(model, df):
    prob = model.predict_proba(df)[0][1]
    if prob < 0.3:
        risk_level = "Low"
        note = "Risk is low. Maintain a healthy lifestyle and routine check-ups."
    elif prob < 0.6:
        risk_level = "Moderate"
        note = "Risk is moderate. Consider consulting a doctor and reviewing lifestyle habits."
    else:
        risk_level = "High"
        note = "Risk is high. Immediate medical attention and follow-up recommended."
    
    disclaimer = "This prediction is for informational purposes only and is not a medical diagnosis."
    return round(prob,3), risk_level, note, disclaimer

# =====================
# Routes
# =====================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        stage1_data = {
            "age": int(request.form["age"]),
            "gender": 1 if request.form["gender"] == "Male" else 0,
            "systolic_bp": float(request.form["systolic_bp"]),
            "diastolic_bp": float(request.form["diastolic_bp"]),
            "glucose": int(request.form["glucose"]),
            "cholesterol": float(request.form["cholesterol"]),
            "bmi": float(request.form["bmi"]),
            "smoking": int(request.form["smoking"]),
            "alcohol": int(request.form["alcohol"]),
            "family_history": int(request.form["family_history"])
        }

        df = pd.DataFrame([stage1_data])
        ranking_dict = stage1_screen(df)  # returns (top_disease, scores)
        top_disease, scores = ranking_dict

# convert scores dict to list of tuples for template
        ranking_list = sorted(scores.items(), key=lambda x: x[1], reverse=True)

# store for stage-2
        session["stage1_data"] = stage1_data
        session["ranking"] = ranking_list

        return render_template(
        "stage1_result.html",
        ranking=ranking_list,
        top_disease=top_disease
        )


    return render_template("index.html")

@app.route("/stage2/<disease>", methods=["GET", "POST"])
def stage2(disease):
    stage1_data = session.get("stage1_data", {})

    if request.method == "POST":
        if disease == "heart":
            df = pd.DataFrame([{
                "age": int(request.form["age"]),
                "sex": 1 if request.form["sex"]=="Male" else 0,
                "chest_pain_type": request.form["chest_pain_type"],
                "resting_blood_pressure": float(request.form["resting_blood_pressure"]),
                "cholestoral": float(request.form["cholestoral"]),
                "fasting_blood_sugar": 1 if request.form["fasting_blood_sugar"]==">120 mg/ml" else 0,
                "rest_ecg": request.form["rest_ecg"],
                "Max_heart_rate": float(request.form["Max_heart_rate"]),
                "exercise_induced_angina": 1 if request.form["exercise_induced_angina"]=="Yes" else 0,
                "oldpeak": float(request.form["oldpeak"]),
                "slope": request.form["slope"],
                "vessels_colored_by_flourosopy": request.form["vessels"],
                "thalassemia": request.form["thalassemia"]
            }])
            prob, risk, note, disclaimer = stage2_predict(heart_stage2, df)

        elif disease == "hypertension":
            df = pd.DataFrame([{
                "Age": int(request.form["Age"]),
                "Salt_Intake": float(request.form["Salt_Intake"]),
                "Stress_Score": int(request.form["Stress_Score"]),
                "BP_History": request.form["BP_History"],
                "Sleep_Duration": float(request.form["Sleep_Duration"]),
                "BMI": float(request.form["BMI"]),
                "Medication": request.form["Medication"],
                "Family_History": request.form["Family_History"],
                "Exercise_Level": request.form["Exercise_Level"],
                "Smoking_Status": request.form["Smoking_Status"]
            }])
            prob, risk, note, disclaimer = stage2_predict(hypertension_stage2, df)

        else:  # diabetes
            df = pd.DataFrame([{
                "Pregnancies": int(request.form["Pregnancies"]),
                "Glucose": float(request.form["Glucose"]),
                "BloodPressure": float(request.form["BloodPressure"]),
                "SkinThickness": float(request.form["SkinThickness"]),
                "Insulin": float(request.form["Insulin"]),
                "BMI": float(request.form["BMI"]),
                "DiabetesPedigreeFunction": float(request.form["DPF"]),
                "Age": int(request.form["Age"])
            }])
            prob, risk, note, disclaimer = stage2_predict(diabetes_stage2, df)

        return render_template("stage2_result.html",
                               disease=disease.upper(),
                               prob=prob,
                               risk=risk,
                               note=note,
                               disclaimer=disclaimer)

    return render_template(f"{disease}_stage2.html", stage1_data=stage1_data)

if __name__ == "__main__":
    app.run(debug=True)
