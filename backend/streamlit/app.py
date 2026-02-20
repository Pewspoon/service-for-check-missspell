import streamlit as st
import requests
import os
import time
import pandas as pd

API_BASE_URL = os.getenv("API_BASE_URL", "http://app:8080")

# ---------- Функции для работы с API ----------
def register_user(username, email, full_name, password):
    url = f"{API_BASE_URL}/api/auth/register"
    payload = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "role": "user",
        "password": password
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 201:
            return response.json(), None
        else:
            error_detail = response.json().get("detail", "Неизвестная ошибка")
            return None, f"Ошибка {response.status_code}: {error_detail}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def login_user(username, password):
    url = f"{API_BASE_URL}/api/auth/login"
    data = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            error_detail = response.json().get("detail", "Неверные учетные данные")
            return None, f"Ошибка {response.status_code}: {error_detail}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def get_current_user(token):
    url = f"{API_BASE_URL}/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def get_balance(token):
    url = f"{API_BASE_URL}/api/balance/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def replenish_balance(token, amount):
    url = f"{API_BASE_URL}/api/balance/replenish"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"amount": amount}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def get_history(token):
    url = f"{API_BASE_URL}/api/history/me"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def send_predict_request(token, text, model_id=1):
    url = f"{API_BASE_URL}/api/predict/predict"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "text": text,
        "model_id": model_id
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        return None, f"Ошибка соединения: {e}"

def get_prediction_result(token, task_id):
    url = f"{API_BASE_URL}/api/predict/result/{task_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, None  # 404 или другая ошибка – просто возвращаем None
    except Exception as e:
        return None, None

# ---------- Страница входа/регистрации ----------
def show_auth_page():
    st.set_page_config(page_title="Авторизация", page_icon="🔐")
    st.title("🔐 Добро пожаловать")

    tab1, tab2 = st.tabs(["Вход", "Регистрация"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Имя пользователя")
            password = st.text_input("Пароль", type="password")
            submitted = st.form_submit_button("Войти")
            if submitted:
                if not username or not password:
                    st.warning("Заполните все поля")
                else:
                    with st.spinner("Вход..."):
                        token_data, error = login_user(username, password)
                        if token_data:
                            st.session_state.token = token_data["access_token"]
                            st.success("Успешный вход!")
                            st.rerun()
                        else:
                            st.error(error)

    with tab2:
        with st.form("register_form"):
            username = st.text_input("Имя пользователя *")
            email = st.text_input("Email *")
            full_name = st.text_input("Полное имя")
            password = st.text_input("Пароль *", type="password")
            password2 = st.text_input("Подтверждение *", type="password")
            submitted = st.form_submit_button("Зарегистрироваться")
            if submitted:
                if not username or not email or not password:
                    st.warning("Заполните обязательные поля")
                elif password != password2:
                    st.warning("Пароли не совпадают")
                else:
                    with st.spinner("Регистрация..."):
                        data, error = register_user(username, email, full_name, password)
                        if data:
                            st.success("Регистрация успешна! Теперь войдите.")
                        else:
                            st.error(error)

# ---------- Основная страница (после входа) ----------
def show_main_page():
    st.set_page_config(page_title="Личный кабинет", page_icon="💬", layout="wide")
    
    if "token" not in st.session_state:
        st.session_state.token = None
    
    token = st.session_state.token
    if not token:
        show_auth_page()
        return

    # Загружаем данные пользователя
    with st.spinner("Загрузка профиля..."):
        user_data, user_error = get_current_user(token)
        if user_error:
            st.error(f"Ошибка загрузки пользователя: {user_error}")
            if "401" in user_error:
                st.session_state.token = None
                st.rerun()
            return

        # Загружаем баланс
        balance_data, balance_error = get_balance(token)
        
        # Если баланс не найден (404), создаём его через пополнение
        if balance_error and "404" in balance_error:
            st.info("Баланс не найден. Создаём начальный баланс...")
            new_balance, rep_error = replenish_balance(token, 1)
            if new_balance:
                balance_data = new_balance
                st.success("Баланс успешно создан!")
            else:
                st.error(f"Не удалось создать баланс: {rep_error}")
                balance_data = {"amount": 0}
        elif balance_error:
            st.error(f"Ошибка загрузки баланса: {balance_error}")
            balance_data = {"amount": 0}

    # Боковая панель
    with st.sidebar:
        st.header(f"👋 Привет, {user_data.get('full_name', user_data['username'])}!")
        st.metric("Баланс", f"{balance_data.get('amount', 0)} ₽")
        
        with st.expander("Пополнить баланс"):
            amount = st.number_input("Сумма", min_value=1, value=100, step=10)
            if st.button("Пополнить"):
                with st.spinner("Пополнение..."):
                    new_balance, error = replenish_balance(token, amount)
                    if new_balance:
                        st.success("Баланс пополнен!")
                        st.rerun()
                    else:
                        st.error(error)
        
        if st.button("🚪 Выйти"):
            st.session_state.token = None
            st.rerun()

    # Основной контент: чат и история
    st.title("💬 Чат с ML-моделью")

    # Инициализация состояний
    if "current_task_id" not in st.session_state:
        st.session_state.current_task_id = None
    if "current_result" not in st.session_state:
        st.session_state.current_result = None
    if "waiting_for_result" not in st.session_state:
        st.session_state.waiting_for_result = False

    # Форма отправки запроса
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Введите текст для анализа", height=100)
        submitted = st.form_submit_button("Отправить")
        if submitted and user_input:
            with st.spinner("Отправка запроса..."):
                result, error = send_predict_request(token, user_input)
                if result:
                    # Ожидаем, что в ответе есть поле "task_id" (из MLPredictionResponse)
                    # В текущей реализации бэкенд возвращает result с сообщением, но не task_id.
                    # Проверим структуру: в ml.py return MLPredictionResponse(result=f"Task {task_id} queued...", model_name=...)
                    # Значит, task_id нужно извлечь из строки. Это неудобно. Лучше исправить бэкенд, но пока сделаем костыль.
                    # Предположим, что result["result"] содержит "Task <uuid> queued..."
                    import re
                    match = re.search(r'Task ([a-f0-9-]+) queued', result.get("result", ""))
                    if match:
                        st.session_state.current_task_id = match.group(1)
                        st.session_state.waiting_for_result = True
                        st.session_state.current_result = None
                        st.rerun()
                    else:
                        st.error("Не удалось получить идентификатор задачи")
                else:
                    st.error(error)

    # Обработка ожидания результата
    if st.session_state.waiting_for_result and st.session_state.current_task_id:
        task_id = st.session_state.current_task_id
        # Создаём placeholder для динамического обновления
        status_placeholder = st.empty()
        
        max_attempts = 10
        for attempt in range(max_attempts):
            with status_placeholder.container():
                st.info(f"⏳ Задача в очереди. ID: `{task_id}` (попытка {attempt+1}/{max_attempts})")
            
            result_data, _ = get_prediction_result(token, task_id)
            if result_data and result_data.get("status") == "completed":
                st.session_state.current_result = result_data
                st.session_state.waiting_for_result = False
                st.rerun()
                break
            
            time.sleep(1)
        
        # Если после всех попыток результат не получен
        if st.session_state.waiting_for_result:
            with status_placeholder.container():
                st.warning(f"⏳ Задача `{task_id}` ещё обрабатывается. Проверьте историю позже.")
            st.session_state.waiting_for_result = False

    # Отображение результата, если он есть
    if st.session_state.current_result:
        st.success("Результат получен:")
        st.write(st.session_state.current_result.get("result", "Нет данных"))
        if st.button("Очистить результат"):
            st.session_state.current_result = None
            st.rerun()

    # История запросов
    st.subheader("📜 История запросов")
    history_data, history_error = get_history(token)
    if history_error:
        st.error(f"Ошибка загрузки истории: {history_error}")
    elif history_data:
        df = pd.DataFrame(history_data)
        if not df.empty:
            # Переименование колонок
            rename_map = {
                "input_text": "Запрос",
                "result": "Ответ",
                "cost": "Стоимость",
                "created_at": "Дата"
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
            # Оставляем только нужные колонки
            keep_cols = ["Дата", "Запрос", "Ответ", "Стоимость"]
            df = df[[c for c in keep_cols if c in df.columns]]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("История пуста")
    else:
        st.info("История пуста")

# ---------- Точка входа ----------
if __name__ == "__main__":
    if "token" not in st.session_state or not st.session_state.token:
        show_auth_page()
    else:
        show_main_page()