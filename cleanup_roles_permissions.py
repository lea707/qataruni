from database.connection import SessionLocal
from users.models.models import Role, Permission, role_permission

session = SessionLocal()

# Remove all old role-permission associations
session.execute(role_permission.delete())
# Remove all old roles and permissions
session.query(Role).delete()
session.query(Permission).delete()
session.commit()

# Define new permissions
permissions = [
    Permission(permission_name='add_employee', description='Can add employees'),
    Permission(permission_name='edit_department', description='Can edit department'),
    Permission(permission_name='view_department', description='Can view department'),
    Permission(permission_name='view_direct_reports', description='Can view direct reports'),
    Permission(permission_name='edit_own_profile', description='Can edit own profile'),
    Permission(permission_name='full_access', description='Full system access'),
]

for perm in permissions:
    session.add(perm)
session.commit()

# Helper to get permission by name
def get_perm(name):
    return session.query(Permission).filter_by(permission_name=name).first()

# Create roles and assign permissions
roles = [
    Role(role_name='Admin', description='System administrator', permissions=[
        get_perm('full_access')
    ]),
    Role(role_name='Director', description='Department director', permissions=[
        get_perm('edit_department'),
        get_perm('view_department'),
        get_perm('add_employee'),
    ]),
    Role(role_name='HR', description='HR staff', permissions=[
        get_perm('add_employee'),
        get_perm('view_department'),
    ]),
    Role(role_name='Supervisor', description='Supervisor', permissions=[
        get_perm('view_direct_reports'),
        get_perm('view_department'),
    ]),
    Role(role_name='Employee', description='Regular employee', permissions=[
        get_perm('edit_own_profile'),
        get_perm('view_department'),
    ]),
]

for role in roles:
    session.add(role)
session.commit()

print('Cleaned out old roles/permissions and created new recommended set.')
session.close() 