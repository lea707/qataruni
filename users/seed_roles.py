from users.models import Role, Permission
from database.connection import db, engine
from sqlalchemy.orm import Session

# Define roles and their permissions
role_permissions = {
    "Admin": [
        "view_employees", "add_employee", "edit_employee", "delete_employee",
        "manage_roles", "manage_permissions",
        "view_departments", "add_department", "edit_department", "delete_department",
        "view_documents", "upload_documents"
    ],
    "HR": [
        "view_employees", "add_employee", "edit_employee",
        "view_documents", "upload_documents",
        "view_departments", "add_department", "edit_department"
    ],
    "Viewer": [
        "view_employees",
        "view_departments"
    ]
}
# ... your existing code ...

def seed_roles_and_permissions():
    print("🔄 Starting role and permission seeding...")
    with Session(engine) as session:
        # Fetch existing permissions from DB
        existing_perms = {
            p.permission_name: p
            for p in session.query(Permission).all()
        }
        print(f"🔍 Found {len(existing_perms)} existing permissions.")

        # Create or reuse permissions
        permission_objs = {}
        for perm_name in {p for perms in role_permissions.values() for p in perms}:
            if perm_name in existing_perms:
                permission_objs[perm_name] = existing_perms[perm_name]
            else:
                print(f"➕ Adding new permission: {perm_name}")
                new_perm = Permission(permission_name=perm_name, description=f"Allows {perm_name.replace('_', ' ')}")
                session.add(new_perm)
                permission_objs[perm_name] = new_perm

        session.flush()

        # Fetch existing roles
        existing_roles = {
            r.role_name: r
            for r in session.query(Role).all()
        }
        print(f"🔍 Found {len(existing_roles)} existing roles.")

        # Create or update roles
        for role_name, perms in role_permissions.items():
            if role_name in existing_roles:
                print(f"🔁 Updating role: {role_name}")
                role = existing_roles[role_name]
                role.permissions = [permission_objs[p] for p in perms]
            else:
                print(f"➕ Creating role: {role_name}")
                role = Role(
                    role_name=role_name,
                    description=f"{role_name} role with permissions: {', '.join(perms)}",
                    permissions=[permission_objs[p] for p in perms]
                )
                session.add(role)

        session.commit()
        print("✅ Roles and permissions seeded or updated.")

# ✅ This must be at the global level
if __name__ == "__main__":
    seed_roles_and_permissions()