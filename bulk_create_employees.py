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
    for i in range(50):
        form_data = MultiDict([
            ('arab_name', f'موظف{i}'),
            ('english_name', f'Employee{i}'),
            ('email', f'emp{i}@example.com'),
            ('phone', f'555{i:04d}'),
            ('hire_date', (date.today() - timedelta(days=i*10)).isoformat()),
            ('position_id', random.choice(positions).position_id),
            ('department_id', random.choice(departments).department_id),
            ('level_id', random.choice(levels).level_id),
            ('supervisor_emp_id', ''),
            ('skill_name[]', 'Python'),
            ('skill_category[]', '1'),
            ('skill_level[]', 'Advanced'),
            ('certified[]', 'on'),
            ('certificate_type_id[]', str(random.choice(cert_types).cert_type_id)),
            ('issuing_organization[]', 'Test Institute'),
            ('validity_period_months[]', '12'),
            ('general_document_type_id[]', str(random.choice(doc_types).type_id))
        ])
        files = MultiDict([
            ('document_file_0[]', FileStorage(stream=io.BytesIO(b'fake cert content'), filename='cert.png', content_type='image/png')),
            ('general_document_file[]', FileStorage(stream=io.BytesIO(b'fake doc content'), filename='doc.png', content_type='image/png'))
        ])
        try:
            service.create_employee(form_data, files)
            print(f'Inserted employee {i+1}/50')
        except Exception as e:
            print(f'Failed to insert employee {i+1}: {e}')
    print('Done inserting 50 employees with files.') 