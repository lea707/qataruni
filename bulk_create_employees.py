import io
import random
from datetime import date, timedelta
from app import create_app
from services.employee_service import EmployeeService
from database.connection import db
from models import Department, Position, EmployeeLevel, CertificateType, DocumentType
from werkzeug.datastructures import MultiDict, FileStorage

app = create_app()

with app.app_context():
    session = db()
    departments = session.query(Department).all()
    positions = session.query(Position).all()
    levels = session.query(EmployeeLevel).all()
    cert_types = session.query(CertificateType).all()
    doc_types = session.query(DocumentType).all()
    if not (departments and positions and levels and cert_types and doc_types):
        print('Seed departments, positions, levels, certificate types, and document types first!')
        exit(1)
    service = EmployeeService()
    scenarios = [
        # Active, 4 skills, with documents
        {
            'active': True,
            'skills': [
                {'name': 'Python', 'category': '1', 'level': 'Advanced'},
                {'name': 'SQL', 'category': '1', 'level': 'Intermediate'},
                {'name': 'Excel', 'category': '1', 'level': 'Expert'},
                {'name': 'Project Management', 'category': '1', 'level': 'Advanced'}
            ],
            'documents': True
        },
        # Inactive, no skills, no documents
        {
            'active': False,
            'skills': [],
            'documents': False
        },
        # Active, 1 skill, with documents
        {
            'active': True,
            'skills': [
                {'name': 'Java', 'category': '1', 'level': 'Beginner'}
            ],
            'documents': True
        },
        # Inactive, 2 skills, no documents
        {
            'active': False,
            'skills': [
                {'name': 'C++', 'category': '1', 'level': 'Intermediate'},
                {'name': 'Linux', 'category': '1', 'level': 'Advanced'}
            ],
            'documents': False
        },
        # Active, no skills, with documents
        {
            'active': True,
            'skills': [],
            'documents': True
        },
        # Inactive, 4 skills, with documents
        {
            'active': False,
            'skills': [
                {'name': 'HTML', 'category': '1', 'level': 'Beginner'},
                {'name': 'CSS', 'category': '1', 'level': 'Beginner'},
                {'name': 'JavaScript', 'category': '1', 'level': 'Intermediate'},
                {'name': 'React', 'category': '1', 'level': 'Intermediate'}
            ],
            'documents': True
        },
        # Active, 2 skills, no documents
        {
            'active': True,
            'skills': [
                {'name': 'Docker', 'category': '1', 'level': 'Intermediate'},
                {'name': 'Kubernetes', 'category': '1', 'level': 'Beginner'}
            ],
            'documents': False
        },
        # Inactive, 1 skill, with documents
        {
            'active': False,
            'skills': [
                {'name': 'Go', 'category': '1', 'level': 'Beginner'}
            ],
            'documents': True
        },
        # Active, no skills, no documents
        {
            'active': True,
            'skills': [],
            'documents': False
        }
    ]
    for i, scenario in enumerate(scenarios):
        form_data = MultiDict([
            ('arab_name', f'موظف_سيناريو{i+1}'),
            ('english_name', f'EmployeeScenario{i+1}'),
            ('email', f'scenario{i+1}@example.com'),
            ('phone', f'555{i+1000}'),
            ('hire_date', (date.today() - timedelta(days=i*5)).isoformat()),
            ('position_id', random.choice(positions).position_id),
            ('department_id', random.choice(departments).department_id),
            ('level_id', random.choice(levels).level_id),
            ('supervisor_emp_id', ''),
        ])
        if scenario['active']:
            form_data.add('is_active', 'on')
        # Add skills
        for skill in scenario['skills']:
            form_data.add('skill_name[]', skill['name'])
            form_data.add('skill_category[]', skill['category'])
            form_data.add('skill_level[]', skill['level'])
            form_data.add('certified[]', 'on')  # Assume all are certified for demo
            form_data.add('certificate_type_id[]', str(random.choice(cert_types).cert_type_id))
            form_data.add('issuing_organization[]', 'Test Org')
            form_data.add('validity_period_months[]', '12')
        files = MultiDict()
        if scenario['documents']:
            # Add one general document
            form_data.add('general_document_type_id[]', str(random.choice(doc_types).type_id))
            files.add('general_document_file[]', FileStorage(stream=io.BytesIO(b'fake doc content'), filename=f'doc_{i}.png', content_type='image/png'))
            # If skills exist, add a certificate file for each
            for idx, skill in enumerate(scenario['skills']):
                files.add(f'document_file_{idx}[]', FileStorage(stream=io.BytesIO(b'fake cert content'), filename=f'cert_{i}_{idx}.png', content_type='image/png'))
        try:
            service.create_employee(form_data, files)
            print(f'Inserted scenario employee {i+1}/9')
        except Exception as e:
            print(f'Failed to insert scenario employee {i+1}: {e}')
    print('Done inserting 9 scenario employees.') 