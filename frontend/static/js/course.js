function getSpaceId() {
    const params =
        new URLSearchParams(
            window.location.search
        );

    return params.get(
        "space_id"
    );
}


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


async function readCourseResponse(
    response
) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}


function getCourseErrorMessage(
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


function getAccessLabel(
    accessMode
) {
    return accessMode ===
        "public"
        ? "Публичный курс"
        : "Приватный курс";
}


function updateCourseLinks(
    spaceId
) {
    const chatTab =
        document.getElementById(
            "chat-tab"
        );

    const materialsTab =
        document.getElementById(
            "materials-tab"
        );


    if (chatTab) {
        chatTab.href =
            `chat.html?space_id=${encodeURIComponent(spaceId)}`;
    }


    if (materialsTab) {
        materialsTab.href =
            `materials.html?space_id=${encodeURIComponent(spaceId)}`;
    }
}


function renderCourseInfo(course) {
    const title =
        document.getElementById(
            "course-title"
        );

    const access =
        document.getElementById(
            "course-access"
        );

    const owner =
        document.getElementById(
            "course-owner"
        );

    const currentUserId =
        getCurrentUserId();


    if (title) {
        title.textContent =
            course.name;
    }


    if (access) {
        access.textContent =
            getAccessLabel(
                course.access_mode
            );

        access.classList.toggle(
            "public",
            course.access_mode ===
                "public"
        );
    }


    if (owner) {
        const isOwner =
            course.owner_id ===
            currentUserId;

        owner.hidden =
            !isOwner;
    }


    document.title =
        `${course.name} — NSU RAG`;
}


async function loadCourse() {
    const spaceId =
        getSpaceId();

    const token =
        getAccessToken();

    const title =
        document.getElementById(
            "course-title"
        );

    const error =
        document.getElementById(
            "course-error"
        );


    if (!token) {
        window.location.href =
            "../login.html";

        return;
    }


    if (!spaceId) {
        if (title) {
            title.textContent =
                "Курс не выбран";
        }

        if (error) {
            error.textContent =
                "Откройте курс из списка курсов.";
        }

        return;
    }


    updateCourseLinks(
        spaceId
    );


    try {
        const response =
            await fetch(
                `/spaces/${encodeURIComponent(spaceId)}`,
                {
                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    }
                }
            );


        if (
            response.status ===
            401
        ) {
            clearAuthData();

            window.location.href =
                "../login.html";

            return;
        }


        const data =
            await readCourseResponse(
                response
            );


        if (!response.ok) {
            if (title) {
                title.textContent =
                    "Курс";
            }

            if (error) {
                error.textContent =
                    getCourseErrorMessage(
                        data,
                        "Не удалось открыть курс."
                    );
            }

            return;
        }


        if (error) {
            error.textContent = "";
        }


        renderCourseInfo(
            data
        );

    } catch {
        if (title) {
            title.textContent =
                "Курс";
        }

        if (error) {
            error.textContent =
                "Не удалось подключиться к серверу.";
        }
    }
}


document.addEventListener(
    "DOMContentLoaded",
    loadCourse
);