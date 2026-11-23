import hashlib
import hmac
import bcrypt
import streamlit as st
from streamlit_local_storage import LocalStorage

st.set_page_config(page_title="Мое приложение", page_icon="🔐", layout="centered")

localS = LocalStorage()
SECRET_KEY = st.secrets["cookie"]["key"]
USERS = st.secrets["credentials"]["usernames"]


def make_token(username: str) -> str:
    sig = hmac.new(
        SECRET_KEY.encode(), username.encode(), hashlib.sha256
    ).hexdigest()
    return f"{username}:{sig}"


def verify_token(token: str) -> str | None:
    if not token or not isinstance(token, str) or ":" not in token:
        return None
    username, _ = token.split(":", 1)
    if username in USERS and hmac.compare_digest(token, make_token(username)):
        return username
    return None


def check_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# 1. Читаем все данные из localStorage (getAll надежнее срабатывает при старте в iOS)
stored_data = localS.getAll() or {}
saved_token = stored_data.get("pwa_auth_token")

# Проверяем, есть ли валидный токен в памяти телефона или в текущей сессии
verified_user = verify_token(saved_token) or st.session_state.get("auth_user")

# 2. Если пользователь НЕ авторизован — показываем форму входа
if not verified_user:
    with st.form("login_form"):
        st.subheader("Авторизация")
        username_input = st.text_input("Логин").strip()
        password_input = st.text_input("Пароль", type="password")

        if st.form_submit_button("Войти", use_container_width=True):
            user_data = USERS.get(username_input)
            if user_data and check_password(
                password_input, user_data["password"]
            ):
                # Запоминаем в сессии и ставим флаг, что нужно записать токен при рендере
                st.session_state["auth_user"] = username_input
                st.session_state["need_save_token"] = make_token(username_input)
                st.rerun()
            else:
                st.error("Неверный логин или пароль")
    st.stop()

# 3. Записываем токен в localStorage в основном потоке рендера (БЕЗ st.rerun после!)
if "need_save_token" in st.session_state:
    localS.setItem("pwa_auth_token", st.session_state.pop("need_save_token"))

# 4. --- ЗАЩИЩЕННАЯ ЧАСТЬ ПРИЛОЖЕНИЯ ---
user_info = USERS[verified_user]
full_name = (
    f"{user_info.get('first_name', '')} {user_info.get('last_name', '')}".strip()
    or verified_user
)

with st.sidebar:
    st.write(f"Пользователь: **{full_name}**")
    if st.button("Выйти из аккаунта", use_container_width=True):
        localS.deleteItem("pwa_auth_token")
        st.session_state["auth_user"] = None
        # Не делаем мгновенный rerun, чтобы deleteItem успел долететь до iPhone
        st.info("Выход выполнен. Обновите страницу.")
        st.stop()

st.title(f"Привет, {full_name}!")
st.success("Вы авторизованы.")
