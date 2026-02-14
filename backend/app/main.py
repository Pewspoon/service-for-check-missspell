from sqlmodel import Session
from models.user import UserBase, UserRole
from database.create_tables import engine


def main():
    with Session(engine) as session:
        user = UserBase(
            username="Bob",
            email='123@test.com',
            full_name='Fullname',
            role=UserRole.USER
        )
        user_2 = UserBase(
            username="Bob",
            email='1234@test.com',
            full_name='Fullname',
            role=UserRole.USER
        )
        user_3 = UserBase(
            username="Bob",
            email='1235@test.com',
            full_name='Fullname',
            role=UserRole.USER
        )
        user_4 = UserBase(
            username="Bob",
            email='1236@test.com',
            full_name='Fullname',
            role=UserRole.USER
        )
        session.add_all([user, user_2, user_3, user_4])
        session.commit()


if __name__ == "__main__":
    main()
