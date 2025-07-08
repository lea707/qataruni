import pytest
from datetime import datetime, timedelta
from io import BytesIO
from werkzeug.datastructures import FileStorage
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

# Test data builders
def build_employee_data():
    return {
        'arab_name': 'Test Arabic',
        'english_name': 'Test English',
        'email': 'test@example.com',
        'hire_date': '2023-01-01',
        'position_id': '1',
        'department_id': '1',
        'level_id': '1',
        'is_active': 'true',
        'skill_ids[]': ['1', '2']
    }

def build_document_data():
    return {
        'cert_types[]': ['1', '2'],
        'doc_types[]': ['1', '1'],
        'expiry_dates[]': ['2024-01-01', '2024-02-01']
    }

def mock_file(filename='test.pdf', content_type='application/pdf'):
    return FileStorage(
        stream=BytesIO(b'Test file content'),
        filename=filename,
        content_type=content_type,
        name='document_files[]'
    )

# Main test class
class TestEmployeeSaving:
    @pytest.fixture
    def mock_request(self):
        with patch('flask.request') as mock:
            mock.form = build_employee_data()
            mock.files = {'document_files[]': [mock_file(), mock_file()]}
            yield mock

    def test_skill_saving(self, app, client, mock_request):
        """Test that skills are properly associated with employees"""
        from models.employee import Employee
        from services.employee_service import EmployeeService
        
        with app.app_context():
            # Mock the form data with skills
            mock_request.form.update(build_employee_data())
            mock_request.form.update(build_document_data())
            
            service = EmployeeService()
            employee_id = service.create_employee(mock_request.form)
            
            # Verify skills were saved
            employee = Employee.query.options(
                joinedload(Employee.skills) # type: ignore
            ).get(employee_id)
            
            assert len(employee.skills) == 2
            assert {s.skill_id for s in employee.skills} == {1, 2}

    def test_document_saving(self, app, client, mock_request):
        """Test that documents are properly saved and linked"""
        from models.employee_document import EmployeeDocument
        
        with app.app_context():
            # Mock the form data with documents
            mock_request.form.update(build_employee_data())
            mock_request.form.update(build_document_data())
            
            # Call the service that handles document saving
            from services.employee_document_service import EmployeeDocumentService
            doc_service = EmployeeDocumentService()
            
            # We need an employee ID first - could use a fixture in real tests
            from services.employee_service import EmployeeService
            emp_service = EmployeeService()
            employee_id = emp_service.create_employee(mock_request.form)
            
            # Save documents
            result = doc_service.save_employee_documents(
                employee_id=employee_id,
                form_data=mock_request.form,
                files=mock_request.files
            )
            
            assert result is True
            
            # Verify documents were saved
            documents = EmployeeDocument.query.filter_by(employee_id=employee_id).all()
            assert len(documents) == 2
            assert all(doc.file_path is not None for doc in documents)
            assert documents[0].cert_type_id == 1
            assert documents[1].cert_type_id == 2

    def test_certificate_association(self, app, client, mock_request):
        """Test that certificates are properly linked to documents"""
        from models.employee_document import EmployeeDocument
        
        with app.app_context():
            # Setup test data
            mock_request.form.update(build_employee_data())
            mock_request.form.update(build_document_data())
            
            # Get services
            from services.employee_service import EmployeeService
            from services.employee_document_service import EmployeeDocumentService
            
            emp_service = EmployeeService()
            doc_service = EmployeeDocumentService()
            
            # Create employee and documents
            employee_id = emp_service.create_employee(mock_request.form)
            doc_service.save_employee_documents(
                employee_id=employee_id,
                form_data=mock_request.form,
                files=mock_request.files
            )
            
            # Verify certificate associations
            documents = EmployeeDocument.query.filter_by(employee_id=employee_id).all()
            assert documents[0].certificate_type is not None
            assert documents[0].cert_type_id == int(mock_request.form['cert_types[]'][0])
            assert documents[1].certificate_type is not None
            assert documents[1].cert_type_id == int(mock_request.form['cert_types[]'][1])

    def test_transaction_rollback(self, app, client, mock_request):
        """Test that failed document saves don't leave partial data"""
        from models.employee import Employee
        from models.employee_document import EmployeeDocument
        
        with app.app_context():
            # Setup failing case
            mock_request.form.update(build_employee_data())
            mock_request.form.update(build_document_data())
            
            # Force a failure on second document
            original_save = FileStorage.save
            def failing_save(*args, **kwargs):
                if args[0].endswith('test2.pdf'):
                    raise IOError("Simulated save failure")
                original_save(*args, **kwargs)
            
            with patch('werkzeug.datastructures.FileStorage.save', new=failing_save):
                from services.employee_service import EmployeeService
                from services.employee_document_service import EmployeeDocumentService
                
                emp_service = EmployeeService()
                doc_service = EmployeeDocumentService()
                
                employee_id = emp_service.create_employee(mock_request.form)
                
                with pytest.raises(Exception):
                    doc_service.save_employee_documents(
                        employee_id=employee_id,
                        form_data=mock_request.form,
                        files={'document_files[]': [
                            mock_file('test1.pdf'),
                            mock_file('test2.pdf')
                        ]}
                    )
                
                # Verify no documents were saved
                assert EmployeeDocument.query.filter_by(employee_id=employee_id).count() == 0
                
                # But employee should still exist
                assert Employee.query.get(employee_id) is not None

    def test_form_data_handling(self, app, client):
        """Test that form data is properly parsed"""
        from services.employee_service import EmployeeService
        
        with app.app_context():
            # Test with array-style form data
            form_data = {
                'arab_name': 'Test',
                'english_name': 'Test',
                'email': 'test@test.com',
                'hire_date': '2023-01-01',
                'position_id': '1',
                'department_id': '1',
                'level_id': '1',
                'skill_ids[]': ['1', '2', '3'],
                'document_files[]': ['file1', 'file2'],
                'cert_types[]': ['1', '2'],
                'doc_types[]': ['1', '1'],
                'expiry_dates[]': ['2024-01-01', '']
            }
            
            service = EmployeeService()
            
            # Test skill processing
            with patch.object(service.repository, '_process_employee_skills') as mock_skills:
                with patch.object(service.repository, '_save_to_database') as mock_save:
                    mock_save.return_value = 1
                    service.create_employee(form_data)
                    
                    # Verify skills were processed correctly
                    mock_skills.assert_called_once()
                    args, _ = mock_skills.call_args
                    assert args[0] == 1  # employee_id
                    assert args[1] == ['1', '2', '3']  # skill_ids

            # Test with comma-separated skill IDs
            form_data = {
                **form_data,
                'skill_ids': '1,2,3',  # Not array format
                'skill_ids[]': None     # Simulate different form submission
            }
            
            with patch.object(service.repository, '_process_employee_skills') as mock_skills:
                with patch.object(service.repository, '_save_to_database') as mock_save:
                    mock_save.return_value = 1
                    service.create_employee(form_data)
                    
                    # Verify skills were processed correctly
                    args, _ = mock_skills.call_args
                    assert args[1] == '1,2,3'  # Should handle string input