from auth.user_manager import UserManager

manager = UserManager()

print(
    manager.get_users()
)