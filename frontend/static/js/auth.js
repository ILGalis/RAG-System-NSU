const API = {
    register: "/auth/register",
    login: "/auth/login"
};


async function readResponse(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}


function getErrorMessage(data, fallback) {
    if (data?.error?.message) {
        return data.error.message;
    }

    if (Array.isArray(data?.detail)) {
        return data.detail
            .map((item) => item.msg)
            .filter(Boolean)
            .join(". ");
    }

    return fallback;
}


async function handleLogin(form) {
    const errorElement = document.getElementById("form-error");
    const button = form.querySelector('button[type="submit"]');

    errorElement.textContent = "";

    const email = form.email.value.trim();
    const password = form.password.value;

    button.disabled = true;

    try {
        const response = await fetch(API.login, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await readResponse(response);

        if (!response.ok) {
            errorElement.textContent = getErrorMessage(
                data,
                "Не удалось войти в систему."
            );
            return;
        }

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("token_type", data.token_type);
        localStorage.setItem("user_id", String(data.user_id));

        window.location.href = "courses.html";
    } catch {
        errorElement.textContent =
            "Не удалось подключиться к серверу.";
    } finally {
        button.disabled = false;
    }
}


async function handleRegister(form) {
    const errorElement = document.getElementById("form-error");
    const noticeElement = document.getElementById("auth-notice");
    const button = form.querySelector('button[type="submit"]');

    errorElement.textContent = "";

    const email = form.email.value.trim();
    const password = form.password.value;

    /*
     * Имя и фамилия уже есть в интерфейсе.
     * Backend пока их не принимает.
     *
     * После изменения API сюда будут добавлены:
     *
     * first_name: form.first_name.value.trim(),
     * last_name: form.last_name.value.trim()
     */

    button.disabled = true;

    try {
        const response = await fetch(API.register, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        const data = await readResponse(response);

        if (!response.ok) {
            errorElement.textContent = getErrorMessage(
                data,
                "Не удалось зарегистрироваться."
            );
            return;
        }

        form.reset();

        noticeElement.textContent =
            data.message || "Регистрация завершена. Проверьте почту.";
    } catch {
        errorElement.textContent =
            "Не удалось подключиться к серверу.";
    } finally {
        button.disabled = false;
    }
}


document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.getElementById("login-form");
    const registerForm = document.getElementById("register-form");

    if (loginForm) {
        loginForm.addEventListener("submit", (event) => {
            event.preventDefault();
            handleLogin(loginForm);
        });
    }

    if (registerForm) {
        registerForm.addEventListener("submit", (event) => {
            event.preventDefault();
            handleRegister(registerForm);
        });
    }
});