import io
import os
import pytest

os.environ['TESTING'] = '1'

from app import app
from database.connection import db
from models.department import Department
from models.position import Position
from models.level import EmployeeLevel
from models.employee import Employee
from services.employee_service import EmployeeService


def ensure_seed(session):
    dept = session.query(Department).first()
    if not dept:
        dept = Department(department_name="QA")
        session.add(dept)
        session.flush()
    pos = session.query(Position).first()
    if not pos:
        pos = Position(position_name="Engineer")
        session.add(pos)
        session.flush()
    lvl = session.query(EmployeeLevel).first()
    if not lvl:
        lvl = EmployeeLevel(level_name="Junior")
        session.add(lvl)
        session.flush()
    session.commit()
    return dept, pos, lvl


def test_edit_upload_displays_document():
    with app.app_context():
        session = db()
        try:
            # seed basics
            dept, pos, lvl = ensure_seed(session)

            # create employee
            service = EmployeeService()
            emp_id = service.create_employee({
                'arab_name': 'تجربة',
                'english_name': 'Test Emp',
                'email': 'test@example.com',
                'hire_date': '2024-01-01',
                'position_id': str(pos.position_id),
                'department_id': str(dept.department_id),
                'level_id': str(lvl.level_id),
                'is_active': 'true'
            })

            client = app.test_client()

            # Login as Admin for edit access
            with client.session_transaction() as sess:
                sess['user_id'] = 'test-user'
                sess['role_name'] = 'Admin'
                sess['emp_id'] = emp_id

            # Upload a document via Edit POST
            data = {
                'general_document_type_id[]': '1',
            }
            file_data = {
                'general_document_file[]': (io.BytesIO(b"hello world"), 'test_doc.pdf')
            }
            # Merge data and files into one dict for test_client
            multipart = {}
            multipart.update(data)
            multipart.update(file_data)

            resp = client.post(f"/employees/edit/{emp_id}", data=multipart, content_type='multipart/form-data', follow_redirects=True)
            assert resp.status_code == 200

            # Now open edit page and verify the document appears by name
            resp2 = client.get(f"/employees/edit/{emp_id}")
            assert resp2.status_code == 200
            html = resp2.get_data(as_text=True)
            assert 'test_doc.pdf' in html

            # And verify the details page also shows it
            resp3 = client.get(f"/employees/{emp_id}")
            assert resp3.status_code == 200
            assert 'test_doc.pdf' in resp3.get_data(as_text=True)
        finally:
            session.close()


