from auth.user_manager import UserManager

manager = UserManager()

manager.create_user(
    "superadmin",
    "ChangeMe123",
    "superadmin"
)

print(
    "Super Admin Created"
)