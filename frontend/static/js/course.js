function getSpaceId() {
    const params =
        new URLSearchParams(window.location.search);

    return params.get("space_id");
}


function getAccessToken() {
    return localStorage.getItem("access_token");
}


async function readCourseResponse(response) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}


function getCourseErrorMessage(data, fallback) {
    if (data?.error?.message) {
        return data.error.message;
    }

    return fallback;
}


function updateCourseLinks(spaceId) {
    const chatTab =
        document.getElementById("chat-tab");

    const materialsTab =
        document.getElementById("materials-tab");

    chatTab.href =
        `chat.html?space_id=${encodeURIComponent(spaceId)}`;

    materialsTab.href =
        `materials.html?space_id=${encodeURIComponent(spaceId)}`;
}


async function loadCourse() {
    const spaceId = getSpaceId();
    const token = getAccessToken();

    const title =
        document.getElementById("course-title");

    const error =
        document.getElementById("course-error");


    if (!token) {
        window.location.href = "../login.html";
        return;
    }


    if (!spaceId) {
        title.textContent = "Курс не выбран";

        error.textContent =
            "Откройте курс из списка курсов.";

        return;
    }


    updateCourseLinks(spaceId);


    try {
        const response = await fetch(
            `/spaces/${encodeURIComponent(spaceId)}`,
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );


        if (response.status === 401) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("token_type");
            localStorage.removeItem("user_id");

            window.location.href = "../login.html";
            return;
        }


        const data =
            await readCourseResponse(response);


        if (!response.ok) {
            error.textContent =
                getCourseErrorMessage(
                    data,
                    "Не удалось открыть курс."
                );

            title.textContent = "Курс";

            return;
        }


        title.textContent = data.name;

        document.title =
            `${data.name} — NSU RAG`;

    } catch {
        title.textContent = "Курс";

        error.textContent =
            "Не удалось подключиться к серверу.";
    }
}


document.addEventListener(
    "DOMContentLoaded",
    loadCourse
);