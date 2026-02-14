"""Тесты для модели ChatMessage"""
from datetime import datetime

from models.chat import ChatMessage


class TestChatMessage:
    """Тесты для модели ChatMessage"""

    def test_repr(self):
        """Тест метода __repr__"""
        message = ChatMessage()
        message.id = 1
        message.user_id = 10
        message.is_user_message = True

        repr_str = repr(message)
        assert "ChatMessage" in repr_str
        assert "id=1" in repr_str
        assert "user_id=10" in repr_str
        assert "is_user=True" in repr_str

    def test_to_dict_basic(self):
        """Тест базового преобразования в словарь"""
        message = ChatMessage()
        message.id = 1
        message.user_id = 10
        message.text = "Hello world"
        message.is_user_message = True
        message.created_at = None

        result = message.to_dict()

        assert result["id"] == 1
        assert result["user_id"] == 10
        assert result["text"] == "Hello world"
        assert result["is_user_message"] is True
        assert result["created_at"] is None

    def test_to_dict_with_datetime(self):
        """Тест преобразования с datetime"""
        message = ChatMessage()
        message.id = 2
        message.user_id = 20
        message.text = "Test message"
        message.is_user_message = False
        message.created_at = datetime(2024, 1, 15, 10, 30, 0)

        result = message.to_dict()

        assert result["id"] == 2
        assert result["user_id"] == 20
        assert result["text"] == "Test message"
        assert result["is_user_message"] is False
        assert result["created_at"] == "2024-01-15T10:30:00"

    def test_tablename(self):
        """Тест имени таблицы"""
        assert ChatMessage.__tablename__ == "chat_messages"

    def test_column_definitions(self):
        """Тест определения колонок"""
        message = ChatMessage()

        # Проверяем, что колонки существуют
        assert hasattr(message, "id")
        assert hasattr(message, "user_id")
        assert hasattr(message, "text")
        assert hasattr(message, "is_user_message")
        assert hasattr(message, "created_at")
        assert hasattr(message, "user")

    def test_user_relationship(self):
        """Тест связи с пользователем"""
        assert hasattr(ChatMessage, "user")

    def test_to_dict_returns_dict_type(self):
        """Тест, что to_dict возвращает словарь"""
        message = ChatMessage()
        message.id = 1
        message.user_id = 1
        message.text = "test"
        message.is_user_message = True
        message.created_at = None

        result = message.to_dict()
        assert isinstance(result, dict)


class TestChatMessageIntegration:
    """Интеграционные тесты для ChatMessage"""

    def test_create_message_with_all_fields(self):
        """Тест создания сообщения со всеми полями"""
        created_at = datetime.now()
        message = ChatMessage(
            id=1,
            user_id=100,
            text="Test message text",
            is_user_message=True,
            created_at=created_at
        )

        assert message.id == 1
        assert message.user_id == 100
        assert message.text == "Test message text"
        assert message.is_user_message is True
        assert message.created_at == created_at

    def test_user_message_flag(self):
        """Тест флага is_user_message"""
        user_msg = ChatMessage()
        user_msg.is_user_message = True

        system_msg = ChatMessage()
        system_msg.is_user_message = False

        assert user_msg.is_user_message is True
        assert system_msg.is_user_message is False
