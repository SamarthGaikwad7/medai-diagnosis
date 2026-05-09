import stripe
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.platypus import Paragraph
from reportlab.platypus import Table, TableStyle
import joblib
import json
import io

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
db = SQLAlchemy(app)

# Stripe
stripe.api_key = "YOUR_STRIPE_SECRET_KEY"
# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    payment_valid_until = db.Column(db.DateTime, nullable=True)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ LOAD MODELS ------------------
models = {
    'Diabetes': joblib.load('diabetes_model.pkl'),
    'Hypertension': joblib.load('hypertension_model.pkl'),
    'Cardiovascular': joblib.load('cardiovascular_model.pkl'),
    'CKD': joblib.load('ckd_model.pkl')
}

# ------------------ CLEAN OLD REPORTS ------------------
def clean_expired_reports():
    expiration_time = datetime.utcnow() - timedelta(hours=24)
    expired_reports = Report.query.filter(Report.created_at < expiration_time).all()
    for report in expired_reports:
        db.session.delete(report)
    db.session.commit()

# ------------------ ROUTES ------------------

@app.route('/')
def index():
    return render_template('index.html')

# SIGNUP
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("User already exists!")
            return redirect(url_for('login'))

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Signup successful!")
        return redirect(url_for('login'))

    return render_template('signup.html')

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id

            if not user.payment_valid_until or datetime.utcnow() > user.payment_valid_until:
                return redirect(url_for('payment'))

            return redirect(url_for('dashboard'))

        flash("Invalid credentials")

    return render_template('login.html')

# ------------------ DIAGNOSIS ------------------
@app.route('/diagnosis_form', methods=['GET', 'POST'])
def diagnosis_form():

    # ✅ CHECK LOGIN
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # ✅ FORM SUBMIT
    if request.method == 'POST':

        try:

            # ✅ GET USER NAME
            name = request.form['name']
            session['name'] = name

            # ✅ GET INPUTS
            age = int(request.form['age'])
            height = int(request.form['height'])
            weight = int(request.form['weight'])

            blood_sugar = float(request.form['blood_sugar'])

            blood_pressure_sys = int(request.form['blood_pressure_sys'])
            blood_pressure_dia = int(request.form['blood_pressure_dia'])

            cholesterol = float(request.form['cholesterol'])

            smoking = int(request.form['smoking'])
            snoring = int(request.form['snoring'])
            exercise = int(request.form['exercise'])

            # ✅ GENDER
            gender = 1 if request.form['gender'] == 'Male' else 0

            # ✅ BMI CALCULATION
            bmi = round(weight / ((height / 100) ** 2), 2)

            # ✅ BMI CATEGORY
            if bmi < 18.5:
                bmi_status = "Underweight"

            elif bmi < 25:
                bmi_status = "Normal"

            elif bmi < 30:
                bmi_status = "Overweight"

            else:
                bmi_status = "Obese"

            # ✅ SAVE BMI
            session['bmi'] = bmi
            session['bmi_status'] = bmi_status

            # ✅ MODEL INPUTS
            inputs = [
                age,
                height,
                weight,
                blood_sugar,
                blood_pressure_sys,
                blood_pressure_dia,
                cholesterol,
                smoking,
                snoring,
                exercise,
                gender
            ]

            # ✅ DISEASE PREDICTION
            diagnosis = {}

            for disease, model in models.items():

                prob = model.predict_proba([inputs])[0][1]

                diagnosis[disease] = round(prob * 100, 2)

            # =====================================================
            # ✅ HEALTH RECOMMENDATIONS
            # =====================================================
            recommendations = {}

            for disease, value in diagnosis.items():

                # ---------------- DIABETES ----------------
                if disease.lower() == "diabetes":

                    if value > 50:

                        recommendations[disease] = [
                            "Exercise regularly",
                            "Reduce sugar intake",
                            "Monitor glucose levels",
                            "Eat healthy foods"
                        ]

                    else:

                        recommendations[disease] = [
                            "Maintain balanced diet",
                            "Drink more water",
                            "Walk daily"
                        ]

                # ---------------- HYPERTENSION ----------------
                elif disease.lower() == "hypertension":

                    if value > 50:

                        recommendations[disease] = [
                            "Reduce salt intake",
                            "Do regular exercise",
                            "Manage stress",
                            "Sleep properly"
                        ]

                    else:

                        recommendations[disease] = [
                            "Maintain healthy routine",
                            "Avoid stress"
                        ]

                # ---------------- CARDIOVASCULAR ----------------
                elif disease.lower() == "cardiovascular":

                    if value > 50:

                        recommendations[disease] = [
                            "Do cardio exercise",
                            "Eat fruits and vegetables",
                            "Monitor heart health"
                        ]

                    else:

                        recommendations[disease] = [
                            "Maintain heart healthy diet",
                            "Walk regularly"
                        ]

                # ---------------- CKD ----------------
                elif disease.lower() == "ckd":

                    if value > 50:

                        recommendations[disease] = [
                            "Drink more water",
                            "Reduce sodium intake",
                            "Avoid processed foods"
                        ]

                    else:

                        recommendations[disease] = [
                            "Maintain hydration",
                            "Eat healthy foods"
                        ]

            # ✅ SAVE RECOMMENDATIONS
            session['recommendations'] = recommendations

            # ✅ SAVE REPORT
            report = Report(
                user_id=session['user_id'],
                diagnosis=json.dumps(diagnosis)
            )

            db.session.add(report)
            db.session.commit()

            # ✅ REDIRECT
            return redirect(url_for('dashboard'))

        except Exception as e:

            return f"Error: {e}"

    # ✅ OPEN FORM PAGE
    return render_template('diagnosis_form.html')
# ------------------ DASHBOARD ------------------
@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    clean_expired_reports()

    report = Report.query.filter_by(
        user_id=user.id
    ).order_by(
        Report.created_at.desc()
    ).first()

    if report:
        report.diagnosis = json.loads(report.diagnosis)

    # ✅ GET RECOMMENDATIONS
    recommendations = session.get('recommendations', {})

    return render_template(
        'dashboard.html',
        report=report,
        valid_until=user.payment_valid_until,
        bmi=session.get('bmi'),
        bmi_status=session.get('bmi_status'),
        recommendations=recommendations
    )
    
# PAYMENT
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        user = User.query.get(session['user_id'])
        user.payment_valid_until = datetime.utcnow() + timedelta(hours=24)
        db.session.commit()
        return redirect(url_for('dashboard'))

    return render_template('payment.html')

# ------------------ PDF DOWNLOAD ------------------
@app.route('/download_report')
def download_report():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    report = Report.query.filter_by(
        user_id=session['user_id']
    ).order_by(
        Report.created_at.desc()
    ).first()

    if not report:
        return "No report found"

    # ================= LOAD DATA =================
    diagnosis = json.loads(report.diagnosis)

    name = session.get('name', 'User')
    bmi = session.get('bmi', 'N/A')
    bmi_status = session.get('bmi_status', 'N/A')

    # ================= PDF SETUP =================
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    content = []

    # =====================================================
    # ✅ TITLE
    # =====================================================
    title = Paragraph(
        "MedAI Diagnosis Report",
        styles['Title']
    )

    content.append(title)

    content.append(Spacer(1, 20))

    # =====================================================
    # ✅ USER DETAILS TABLE
    # =====================================================
    user_data = [
        ['Field', 'Value'],
        ['Name', name],
        ['Generated Date', str(report.created_at)],
        ['BMI Value', str(bmi)],
        ['BMI Status', bmi_status]
    ]

    user_table = Table(
        user_data,
        colWidths=[140, 200]
    )

    user_table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),

        ('BOTTOMPADDING', (0,0), (-1,-1), 10),

    ]))

    content.append(user_table)

    content.append(Spacer(1, 12))

    # =====================================================
    # ✅ DISEASE PREDICTION TABLE
    # =====================================================
    disease_title = Paragraph(
        "Disease Prediction Results",
        styles['Heading2']
    )

    content.append(disease_title)

    content.append(Spacer(1, 10))

    disease_data = [['Disease', 'Risk Percentage']]

    for disease, value in diagnosis.items():

        disease_data.append([
            disease,
            f"{value}%"
        ])

    disease_table = Table(
        disease_data,
        colWidths=[140, 200]
    )

    disease_table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BACKGROUND', (0,1), (-1,-1), colors.beige),

        ('BOTTOMPADDING', (0,0), (-1,-1), 10),

    ]))

    content.append(disease_table)

    content.append(Spacer(1, 12))

    # =====================================================
    # ✅ HEALTH RECOMMENDATIONS
    # =====================================================
    recommendation_title = Paragraph(
        "Health Recommendations",
        styles['Heading2']
    )

    content.append(recommendation_title)

    content.append(Spacer(1, 10))

    recommendation_data = [[
        'Disease',
        'Foods To Eat',
        'Foods To Avoid'
    ]]

    for disease, value in diagnosis.items():

        eat = ""
        avoid = ""

        # ================= DIABETES =================
        if disease.lower() == "diabetes":

            if value > 50:

                eat = (
                    "Vegetables\n"
                    "Brown rice\n"
                    "Oats\n"
                    "Sugar-free foods"
                )

                avoid = (
                    "Sugar\n"
                    "Soft drinks\n"
                    "Chocolate\n"
                    "Junk food"
                )

            else:

                eat = (
                    "Balanced diet\n"
                    "Fresh fruits\n"
                    "Healthy meals"
                )

                avoid = (
                    "Too much sugar"
                )

        # ================= HYPERTENSION =================
        elif disease.lower() == "hypertension":

            if value > 50:

                eat = (
                    "Bananas\n"
                    "Green vegetables\n"
                    "Low-salt food"
                )

                avoid = (
                    "Salt\n"
                    "Packed foods\n"
                    "Alcohol"
                )

            else:

                eat = (
                    "Healthy homemade food"
                )

                avoid = (
                    "Excess salt"
                )

        # ================= CARDIOVASCULAR =================
        elif disease.lower() == "cardiovascular":

            if value > 50:

                eat = (
                    "Fruits\n"
                    "Fish\n"
                    "Nuts\n"
                    "Healthy oils"
                )

                avoid = (
                    "Smoking\n"
                    "Oily food\n"
                    "Fast food"
                )

            else:

                eat = (
                    "Healthy heart diet"
                )

                avoid = (
                    "Too much oily food"
                )

        # ================= CKD =================
        elif disease.lower() == "ckd":

            if value > 50:

                eat = (
                    "Water\n"
                    "Fresh vegetables\n"
                    "Low sodium foods"
                )

                avoid = (
                    "Salt\n"
                    "Processed food\n"
                    "Cold drinks"
                )

            else:

                eat = (
                    "Hydrating foods"
                )

                avoid = (
                    "Too much sodium"
                )

        recommendation_data.append([
            disease,
            eat,
            avoid
        ])

    recommendation_table = Table(
        recommendation_data,
        colWidths=[100, 120, 140]
    )

    recommendation_table.setStyle(TableStyle([

        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),

        ('GRID', (0,0), (-1,-1), 1, colors.black),

        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),

        ('BACKGROUND', (0,1), (-1,-1), colors.whitesmoke),

        ('BOTTOMPADDING', (0,0), (-1,-1), 10),

        ('TOPPADDING', (0,0), (-1,-1), 10),

        ('LEFTPADDING', (0,0), (-1,-1), 8),

        ('RIGHTPADDING', (0,0), (-1,-1), 8),

        ('VALIGN', (0,0), (-1,-1), 'TOP'),

    ]))

    content.append(recommendation_table)

    content.append(Spacer(1, 12))

    # =====================================================
    # ✅ FOOTER
    # =====================================================
    footer = Paragraph(
        "Generated by MedAI Diagnosis - AI Healthcare Platform",
        styles['Italic']
    )

    content.append(footer)

    # =====================================================
    # ✅ BUILD PDF
    # =====================================================
    doc.build(content)

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="MedAI_Report.pdf",
        mimetype='application/pdf'
    )
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# RUN
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
    