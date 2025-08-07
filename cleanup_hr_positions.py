from database.connection import SessionLocal
from models.position import Position
from models.employee import Employee

session = SessionLocal()

# Find all HR positions
hr_positions = session.query(Position).filter(Position.position_name == 'HR').all()

if hr_positions:
    main_hr = hr_positions[0]
    # Update all employees to use the main HR position
    for pos in hr_positions[1:]:
        session.query(Employee).filter(Employee.position_id == pos.position_id).update({'position_id': main_hr.position_id})
        session.delete(pos)
    session.commit()
    print('Cleaned up duplicate HR positions, only one remains.')
else:
    print('No HR positions found.')

session.close() 