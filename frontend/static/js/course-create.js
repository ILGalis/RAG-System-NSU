function getAccessToken() {
    return localStorage.getItem(
        "access_token"
    );
}


function getCurrentUserId() {
    const value =
        Number(
            localStorage.getItem(
                "user_id"
            )
        );

    return Number.isFinite(value) &&
        value > 0
        ? value
        : null;
}


function clearAuthData() {
    localStorage.removeItem(
        "access_token"
    );

    localStorage.removeItem(
        "token_type"
    );

    localStorage.removeItem(
        "user_id"
    );

    localStorage.removeItem(
        "user_role"
    );

    localStorage.removeItem(
        "user_email"
    );

    localStorage.removeItem(
        "user_first_name"
    );

    localStorage.removeItem(
        "user_last_name"
    );
}


async function readResponse(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}


function getErrorMessage(
    data,
    fallback
) {
    if (data?.error?.message) {
        return data.error.message;
    }

    if (Array.isArray(data?.detail)) {
        return data.detail
            .map(
                (item) =>
                    item.msg
            )
            .filter(Boolean)
            .join(". ");
    }

    return fallback;
}


async function handleCreateCourse(
    form
) {
    const errorElement =
        document.getElementById(
            "course-create-error"
        );

    const button =
        form.querySelector(
            'button[type="submit"]'
        );

    const token =
        getAccessToken();

    const userId =
        getCurrentUserId();


    errorElement.textContent = "";


    if (!token || !userId) {
        clearAuthData();

        window.location.href =
            "login.html";

        return;
    }


    const name =
        form.name.value.trim();

    const accessMode =
        form.access_mode.value;


    if (!name) {
        errorElement.textContent =
            "Введите название курса.";

        return;
    }


    button.disabled = true;


    try {
        const response =
            await fetch(
                "/spaces",
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },
                    body:
                        JSON.stringify({
                            name,
                            owner_id:
                                userId,
                            access_mode:
                                accessMode
                        })
                }
            );


        if (
            response.status ===
            401
        ) {
            clearAuthData();

            window.location.href =
                "login.html";

            return;
        }


        const data =
            await readResponse(
                response
            );


        if (!response.ok) {
            errorElement.textContent =
                getErrorMessage(
                    data,
                    "Не удалось создать курс."
                );

            return;
        }


        window.location.href =
            `course/chat.html?space_id=${encodeURIComponent(data.id)}`;

    } catch {
        errorElement.textContent =
            "Не удалось подключиться к серверу.";
    } finally {
        button.disabled = false;
    }
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        const form =
            document.getElementById(
                "course-create-form"
            );


        if (!form) {
            return;
        }


        if (!getAccessToken()) {
            window.location.href =
                "login.html";

            return;
        }


        form.addEventListener(
            "submit",
            (event) => {
                event.preventDefault();

                handleCreateCourse(
                    form
                );
            }
        );
    }
);