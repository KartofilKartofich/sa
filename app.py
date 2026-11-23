import streamlit as st
import streamlit_authenticator as stauth

# Настройка страницы (хорошо смотрится в iOS PWA)
st.set_page_config(
    page_title="Мое приложение",
    page_icon="🔐",
    layout="centered",
)


# Рекурсивное преобразование st.secrets в обычный изменяемый dict
def secrets_to_dict(obj):
    if isinstance(obj, dict):
        return {k: secrets_to_dict(v) for k, v in obj.items()}
    return obj


config = secrets_to_dict(st.secrets.to_dict())

# Инициализация аутентификатора
authenticator = stauth.Authenticate(
    credentials=config["credentials"],
    cookie_name=config["cookie"]["name"],
    cookie_key=config["cookie"]["key"],
    cookie_expiry_days=config["cookie"]["expiry_days"],
)

# Отрисовка формы входа на русском языке
try:
    authenticator.login(
        location="main",
        fields={
            "Form name": "Авторизация",
            "Username": "Логин",
            "Password": "Пароль",
            "Login": "Войти",
        },
    )
except Exception as e:
    st.error(f"Ошибка авторизации: {e}")

# Проверка статуса входа
auth_status = st.session_state.get("authentication_status")

if auth_status:
    # --- ЗАЩИЩЕННАЯ ЧАСТЬ ПРИЛОЖЕНИЯ ---
    with st.sidebar:
        st.write(f"Пользователь: **{st.session_state.get('name')}**")
        authenticator.logout(button_name="Выйти из аккаунта")

    st.title("Добро пожаловать!")
    st.success("Сессия активна. Cookie сохранена в браузере.")
    st.write(
        "Попробуйте полностью закрыть PWA-приложение на iPhone и открыть его снова через пару минут."
    )

elif auth_status is False:
    st.error("Неверный логин или пароль")

elif auth_status is None:
    st.info("Введите логин и пароль для доступа к приложению")
