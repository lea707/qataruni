Developed for Qatar University
HR Development Team
Doha, Qatar

Employee Skills Tracker - Qatar University

![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

A Flask web application for tracking employee skills and certifications at Qatar University.

                                  ___Features___
 
- Employee directory with department filtering
- Skills tracking (Technical, Business, Languages)
- Search functionality across all employee attributes
- Department overview pages
- Responsive web design

                                ___Installation___
  Requirments:
blinker==1.9.0
click==8.2.1
colorama==0.4.6
Flask==3.1.1
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
greenlet==3.2.3
itsdangerous==2.2.0
Jinja2==3.1.6
MarkupSafe==3.0.2
SQLAlchemy==2.0.41
typing_extensions==4.14.0
Werkzeug==3.1.3
WTForms==3.2.1

 Setup:
 1. Clone the repository:
   ```bash
   git clone https://github.com/lea707/qataruni.git
   cd employee_tracker
2.Install dependencies:
  pip install -r requirements.txt
Running the Application
- Start the development server:
python app.py
- Open your browser to:
http://localhost:5000

                        ___project structure___

employee_tracker/
├── app.py                # Main application entry point
├── routes.py             # All application routes
├── requirements.txt      # Python dependencies
├── static/               # Static files (CSS, JS, images)
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── employees.html    # Employee directory
│   └── ...               # Other templates
└── README.md             # This file




