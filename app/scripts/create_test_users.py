from app.database import SessionLocal
from app.models.account import Account
from app.models.role import Role
from app.models.account_role import AccountRole
from app.schemas.auth_service import AuthService

db = SessionLocal()

admin_role = Role(name="admin")
teacher_role = Role(name="teacher")
student_role = Role(name="student")

db.add(admin_role)
db.add(teacher_role)
db.add(student_role)
db.commit()

teacher = Account(
    username="teacher1",
    hashed_password=AuthService.get_password_hash("teacherpassword123"),
    first_name="Test",
    last_name="Teacher",
    is_active=True
)
db.add(teacher)
db.commit()
db.refresh(teacher)

teacher_role_assignment = AccountRole(account_id=teacher.id, role_id=teacher_role.id)
db.add(teacher_role_assignment)

student = Account(
    username="student1",
    hashed_password=AuthService.get_password_hash("studentpassword123"),
    first_name="Test",
    last_name="Student",
    is_active=True
)
db.add(student)
db.commit()
db.refresh(student)

student_role_assignment = AccountRole(account_id=student.id, role_id=student_role.id)
db.add(student_role_assignment)

db.commit()
db.close()

print("Test users created successfully")