import hashlib
import hmac
import time
import bcrypt
import streamlit as st
from streamlit_local_storage import LocalStorage

st.set_page_config(page_title="Мое приложение", page_icon="🔐", layout="centered")

localS = LocalStorage()
SECRET_KEY = st.secrets["cookie"]["key"]
USERS = st.secrets["credentials"]["usernames"]


def make_token(username: str) -> str:
    """Создает криптографическую подпись (HMAC) для логина, чтобы токен нельзя было подделать."""
    sig = hmac.new(
        SECRET_KEY.encode(), username.encode(), hashlib.sha256
    ).hexdigest()
    return f"{username}:{sig}"


def verify_token(token: str) -> str | None:
    """Проверяет токен из localStorage и возвращает логин, если подпись верна."""
    if not token or ":" not in token:
        return None
    username, _ = token.split(":", 1)
    if username in USERS and hmac.compare_digest(token, make_token(username)):
        return username
    return None


def check_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль по bcrypt-хешу из st.secrets."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# 1. Инициализация состояния
if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None

# 2. Пытаемся прочитать токен из localStorage iPhone
if st.session_state["auth_user"] is None:
    saved_token = localS.getItem("pwa_auth_token")
    verified_user = verify_token(saved_token)

    if verified_user:
        st.session_state["auth_user"] = verified_user
        st.rerun()
    elif "ls_sync_done" not in st.session_state:
        # Даем JS-компоненту localStorage полсекунды на ответ при холодном старте PWA
        st.session_state["ls_sync_done"] = True
        with st.spinner("Проверка сессии..."):
            time.sleep(0.5)
        st.rerun()

# 3. Если пользователь не авторизован — показываем форму входа
if st.session_state["auth_user"] is None:
    with st.form("login_form"):
        st.subheader("Авторизация")
        username_input = st.text_input("Логин").strip()
        password_input = st.text_input("Пароль", type="password")

        if st.form_submit_button("Войти", use_container_width=True):
            user_data = USERS.get(username_input)
            if user_data and check_password(
                password_input, user_data["password"]
            ):
                token = make_token(username_input)
                # Записываем токен в память браузера
                localS.setItem("pwa_auth_token", token)
                st.session_state["auth_user"] = username_input
                # Небольшая пауза, чтобы JS успел записать localStorage до перезагрузки
                time.sleep(0.3)
                st.rerun()
            else:
                st.error("Неверный логин или пароль")
    st.stop()

# 4. --- ЗАЩИЩЕННАЯ ЧАСТЬ ПРИЛОЖЕНИЯ ---
current_user = st.session_state["auth_user"]
user_info = USERS[current_user]
full_name = (
    f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
    or current_user
)

with st.sidebar:
    st.write(f"Пользователь: **{full_name}**")
    if st.button("Выйти из аккаунта", use_container_width=True):
        localS.deleteItem("pwa_auth_token")
        st.session_state["auth_user"] = None
        time.sleep(0.3)
        st.rerun()

st.title(f"Привет, {full_name}!")
st.success("Сессия сохранена в localStorage устройства.")
