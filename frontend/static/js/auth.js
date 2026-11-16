const API = {
    register: "/auth/register",
    verifyEmail: "/auth/verify-email",
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
        if (data.error.code === "invalid_token") {
            return "Код подтверждения недействителен или истёк.";
        }

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


function saveAuthenticatedUser(data) {
    localStorage.setItem(
        "access_token",
        data.access_token
    );

    localStorage.setItem(
        "token_type",
        data.token_type
    );

    localStorage.setItem(
        "user_id",
        String(data.user.id)
    );

    localStorage.setItem(
        "user_role",
        data.user.role
    );

    localStorage.setItem(
        "user_email",
        data.user.email
    );

    localStorage.setItem(
        "user_first_name",
        data.user.first_name
    );

    localStorage.setItem(
        "user_last_name",
        data.user.last_name
    );
}


async function loginUser(email, password) {
    const response = await fetch(
        API.login,
        {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/json"
            },
            body: JSON.stringify({
                email,
                password
            })
        }
    );

    const data =
        await readResponse(response);

    if (!response.ok) {
        throw new Error(
            getErrorMessage(
                data,
                "Не удалось автоматически войти в систему."
            )
        );
    }

    saveAuthenticatedUser(data);
}


async function handleLogin(form) {
    const errorElement =
        document.getElementById(
            "form-error"
        );

    const button =
        form.querySelector(
            'button[type="submit"]'
        );

    errorElement.textContent = "";

    const email =
        form.email.value.trim();

    const password =
        form.password.value;

    button.disabled = true;

    try {
        await loginUser(
            email,
            password
        );

        window.location.href =
            "courses.html";

    } catch (error) {
        errorElement.textContent =
            error.message;

    } finally {
        button.disabled = false;
    }
}


async function handleRegister(form) {
    const errorElement =
        document.getElementById(
            "form-error"
        );

    const button =
        form.querySelector(
            'button[type="submit"]'
        );

    errorElement.textContent = "";

    const firstName =
        form.first_name.value.trim();

    const lastName =
        form.last_name.value.trim();

    const email =
        form.email.value.trim();

    const password =
        form.password.value;

    button.disabled = true;

    try {
        const response =
            await fetch(
                API.register,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        email,
                        password,
                        first_name: firstName,
                        last_name: lastName
                    })
                }
            );

        const data =
            await readResponse(response);

        if (!response.ok) {
            errorElement.textContent =
                getErrorMessage(
                    data,
                    "Не удалось зарегистрироваться."
                );

            return;
        }


        /*
         * Временно сохраняем данные только
         * до подтверждения почты.
         *
         * После успешной верификации они
         * будут удалены.
         */
        sessionStorage.setItem(
            "pending_email",
            email
        );

        sessionStorage.setItem(
            "pending_password",
            password
        );


        window.location.href =
            "verify-email.html";

    } catch {
        errorElement.textContent =
            "Не удалось подключиться к серверу.";

    } finally {
        button.disabled = false;
    }
}


async function handleVerifyEmail(form) {
    const errorElement =
        document.getElementById(
            "form-error"
        );

    const button =
        form.querySelector(
            'button[type="submit"]'
        );

    errorElement.textContent = "";

    const token =
        form.token.value.trim();

    button.disabled = true;

    try {
        const response =
            await fetch(
                API.verifyEmail,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        token
                    })
                }
            );

        const data =
            await readResponse(response);

        if (!response.ok) {
            errorElement.textContent =
                getErrorMessage(
                    data,
                    "Не удалось подтвердить почту."
                );

            return;
        }


        const email =
            sessionStorage.getItem(
                "pending_email"
            );

        const password =
            sessionStorage.getItem(
                "pending_password"
            );


        if (!email || !password) {
            window.location.href =
                "login.html";

            return;
        }


        await loginUser(
            email,
            password
        );


        sessionStorage.removeItem(
            "pending_email"
        );

        sessionStorage.removeItem(
            "pending_password"
        );


        window.location.href =
            "courses.html";

    } catch (error) {
        errorElement.textContent =
            error.message ||
            "Не удалось подключиться к серверу.";

    } finally {
        button.disabled = false;
    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        const loginForm =
            document.getElementById(
                "login-form"
            );

        const registerForm =
            document.getElementById(
                "register-form"
            );

        const verifyForm =
            document.getElementById(
                "verify-form"
            );


        if (loginForm) {
            loginForm.addEventListener(
                "submit",
                (event) => {
                    event.preventDefault();

                    handleLogin(
                        loginForm
                    );
                }
            );
        }


        if (registerForm) {
            registerForm.addEventListener(
                "submit",
                (event) => {
                    event.preventDefault();

                    handleRegister(
                        registerForm
                    );
                }
            );
        }


        if (verifyForm) {
            verifyForm.addEventListener(
                "submit",
                (event) => {
                    event.preventDefault();

                    handleVerifyEmail(
                        verifyForm
                    );
                }
            );
        }
    }
);