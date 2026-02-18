import streamlit as st
import requests
from datetime import datetime

# Конфигурация API (имя контейнера бэкенда в Docker-сети)
API_BASE_URL = "http://app:8080/api"
LOGIN_URL = f"{API_BASE_URL}/login"
CHAT1_URL = f"{API_BASE_URL}/chat1"   # предположим, у вас разные endpoints для двух чатов
CHAT2_URL = f"{API_BASE_URL}/chat2"   # или один общий с идентификатором чата

# Заголовок страницы
st.set_page_config(page_title="Мой личный кабинет", layout="wide")
st.title("Service for check missspell")

# --- Инициализация состояния сессии ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_info = None
    st.session_state.messages_chat1 = []   # история первого чата
    st.session_state.messages_chat2 = []   # история второго чата


# --- Функция для отправки запроса на авторизацию ---
def perform_login(username, password):
    try:
        response = requests.post(LOGIN_URL, json={"username": username, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data.get("access_token")   # предположим, токен в поле access_token
            st.session_state.user_info = data.get("user")
            # Можно сразу загрузить историю чатов, если бэкенд её хранит
            return True, "Успешный вход"
        else:
            return False, f"Ошибка: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Ошибка соединения: {e}"


# --- Функция для отправки сообщения в чат ---
def send_message(chat_endpoint, message, history):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    payload = {"message": message, "timestamp": datetime.now().isoformat()}
    try:
        response = requests.post(chat_endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            reply = response.json().get("reply", "Ответ не получен")
        else:
            reply = f"Ошибка API: {response.status_code}"
    except Exception as e:
        reply = f"Ошибка соединения: {e}"
    # Добавляем сообщение пользователя и ответ ассистента в историю
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})


# --- БЛОК АВТОРИЗАЦИИ ---
if not st.session_state.authenticated:
    st.header("Вход в личный кабинет")
    with st.form("login_form"):
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти")
        if submitted:
            success, message = perform_login(username, password)
            if success:
                st.success(message)
                st.rerun()   # перезапускаем скрипт, чтобы перейти к чатам
            else:
                st.error(message)
    st.stop()   # останавливаем выполнение, пока пользователь не вошёл

# --- ЛИЧНЫЙ КАБИНЕТ (после авторизации) ---
st.sidebar.write(f"Привет, {st.session_state.user_info.get('name', 'пользователь')}!")
if st.sidebar.button("Выйти"):
    # Очищаем состояние
    for key in ["authenticated", "token", "user_info", "messages_chat1", "messages_chat2"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- ДВА ЧАТА В ДВУХ КОЛОНКАХ ---
col1, col2 = st.columns(2)


# Чат 1
with col1:
    st.subheader("Чат 1")
    # Отображаем историю сообщений
    for msg in st.session_state.messages_chat1:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    # Поле ввода для первого чата
    if prompt1 := st.chat_input("Введите сообщение для чата 1", key="chat1_input"):
        send_message(CHAT1_URL, prompt1, st.session_state.messages_chat1)
        st.rerun()   # обновляем страницу, чтобы показать новые сообщения

# Чат 2
with col2:
    st.subheader("Чат 2")
    for msg in st.session_state.messages_chat2:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt2 := st.chat_input("Введите сообщение для чата 2", key="chat2_input"):
        send_message(CHAT2_URL, prompt2, st.session_state.messages_chat2)
        st.rerun()