let allCourses = [];


/* Авторизация */

function getAccessToken() {
    return localStorage.getItem(
        "access_token"
    );
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


function redirectToLogin() {
    window.location.href =
        "login.html";
}


/* Ответы API */

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

    if (
        typeof data?.detail ===
        "string"
    ) {
        return data.detail;
    }

    if (
        Array.isArray(
            data?.detail
        )
    ) {
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


/* Текущий пользователь */

async function loadCurrentUser() {
    const token =
        getAccessToken();

    if (!token) {
        redirectToLogin();

        return null;
    }


    const response =
        await fetch(
            "/auth/me",
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );


    if (response.status === 401) {
        clearAuthData();

        redirectToLogin();

        return null;
    }


    const data =
        await readResponse(
            response
        );


    if (!response.ok) {
        throw new Error(
            getErrorMessage(
                data,
                "Не удалось получить данные пользователя."
            )
        );
    }


    localStorage.setItem(
        "user_id",
        String(data.id)
    );

    localStorage.setItem(
        "user_role",
        data.role ?? ""
    );

    localStorage.setItem(
        "user_email",
        data.email ?? ""
    );

    localStorage.setItem(
        "user_first_name",
        data.first_name ?? ""
    );

    localStorage.setItem(
        "user_last_name",
        data.last_name ?? ""
    );


    return data;
}


/* Курсы */

async function loadCourses() {
    const token =
        getAccessToken();

    if (!token) {
        redirectToLogin();

        return [];
    }


    const response =
        await fetch(
            "/spaces",
            {
                headers: {
                    "Authorization":
                        `Bearer ${token}`
                }
            }
        );


    if (response.status === 401) {
        clearAuthData();

        redirectToLogin();

        return [];
    }


    const data =
        await readResponse(
            response
        );


    if (!response.ok) {
        throw new Error(
            getErrorMessage(
                data,
                "Не удалось загрузить список курсов."
            )
        );
    }


    return Array.isArray(data)
        ? data
        : [];
}


/* Карточка курса */

function getAccessLabel(course) {
    return course.access_mode ===
        "public"
        ? "Публичный курс"
        : "Приватный курс";
}


function createCourseCard(
    course,
    currentUserId
) {
    const card =
        document.createElement(
            "a"
        );

    card.className =
        "course-card";

    card.href =
        `course/chat.html?space_id=${encodeURIComponent(course.id)}`;


    const header =
        document.createElement(
            "div"
        );

    header.className =
        "course-card-header";


    const title =
        document.createElement(
            "h2"
        );

    title.textContent =
        course.name;


    header.append(
        title
    );


    const meta =
        document.createElement(
            "div"
        );

    meta.className =
        "course-card-meta";


    const access =
        document.createElement(
            "span"
        );

    access.className =
        "course-access";


    if (
        course.access_mode ===
        "public"
    ) {
        access.classList.add(
            "public"
        );
    }


    access.textContent =
        getAccessLabel(
            course
        );


    meta.append(
        access
    );


    if (
        course.owner_id ===
        currentUserId
    ) {
        const owner =
            document.createElement(
                "span"
            );

        owner.className =
            "course-owner-badge";

        owner.textContent =
            "Вы владелец";

        meta.append(
            owner
        );
    }


    card.append(
        header,
        meta
    );


    return card;
}


function renderCourseList(
    container,
    courses,
    currentUserId
) {
    container.replaceChildren();


    courses.forEach(
        (course) => {
            container.append(
                createCourseCard(
                    course,
                    currentUserId
                )
            );
        }
    );
}


/* Ошибки */

function showPageError(message) {
    const errorElement =
        document.getElementById(
            "courses-error"
        );


    if (errorElement) {
        errorElement.textContent =
            message;
    }
}


function clearPageError() {
    showPageError("");
}


/* Все курсы */

async function initCoursesPage() {
    const grid =
        document.getElementById(
            "courses-grid"
        );


    if (!grid) {
        return;
    }


    const searchInput =
        document.getElementById(
            "course-search"
        );


    const empty =
        document.getElementById(
            "courses-empty"
        );


    clearPageError();


    try {
        const [
            currentUser,
            courses
        ] =
            await Promise.all([
                loadCurrentUser(),
                loadCourses()
            ]);


        if (!currentUser) {
            return;
        }


        allCourses =
            courses.filter(
                (course) =>
                    course.access_mode ===
                    "public"
            );


        renderCourseList(
            grid,
            allCourses,
            currentUser.id
        );


        if (empty) {
            empty.hidden =
                allCourses.length !==
                0;
        }


        if (searchInput) {
            searchInput.addEventListener(
                "input",
                () => {
                    const query =
                        searchInput.value
                            .trim()
                            .toLowerCase();


                    const filtered =
                        allCourses.filter(
                            (course) =>
                                course.name
                                    .toLowerCase()
                                    .includes(
                                        query
                                    )
                        );


                    renderCourseList(
                        grid,
                        filtered,
                        currentUser.id
                    );


                    if (empty) {
                        empty.hidden =
                            filtered.length !==
                            0;
                    }
                }
            );
        }

    } catch (error) {
        console.error(
            "Ошибка загрузки курсов:",
            error
        );


        showPageError(
            error.message
        );


        if (empty) {
            empty.hidden =
                true;
        }
    }
}


/* Мои курсы */

function isJoinedCourse(
    course,
    currentUserId
) {
    if (
        course.owner_id ===
        currentUserId
    ) {
        return true;
    }


    if (
        typeof course.is_member ===
        "boolean"
    ) {
        return course.is_member;
    }


    return (
        course.access_mode ===
        "private"
    );
}


async function initMyCoursesPage() {
    const ownedGrid =
        document.getElementById(
            "owned-grid"
        );


    if (!ownedGrid) {
        return;
    }


    const joinedGrid =
        document.getElementById(
            "joined-grid"
        );


    const ownedEmpty =
        document.getElementById(
            "owned-empty"
        );


    const joinedEmpty =
        document.getElementById(
            "joined-empty"
        );


    const ownedCount =
        document.getElementById(
            "owned-count"
        );


    const joinedCount =
        document.getElementById(
            "joined-count"
        );


    clearPageError();


    try {
        const [
            currentUser,
            courses
        ] =
            await Promise.all([
                loadCurrentUser(),
                loadCourses()
            ]);


        if (!currentUser) {
            return;
        }


        const currentUserId =
            currentUser.id;


        const ownedCourses =
            courses.filter(
                (course) =>
                    course.owner_id ===
                    currentUserId
            );


        const joinedCourses =
            courses.filter(
                (course) =>
                    isJoinedCourse(
                        course,
                        currentUserId
                    )
            );


        renderCourseList(
            ownedGrid,
            ownedCourses,
            currentUserId
        );


        renderCourseList(
            joinedGrid,
            joinedCourses,
            currentUserId
        );


        if (ownedCount) {
            ownedCount.textContent =
                String(
                    ownedCourses.length
                );
        }


        if (joinedCount) {
            joinedCount.textContent =
                String(
                    joinedCourses.length
                );
        }


        if (ownedEmpty) {
            ownedEmpty.hidden =
                ownedCourses.length !==
                0;
        }


        if (joinedEmpty) {
            joinedEmpty.hidden =
                joinedCourses.length !==
                0;
        }

    } catch (error) {
        console.error(
            "Ошибка загрузки моих курсов:",
            error
        );


        showPageError(
            error.message
        );


        if (ownedEmpty) {
            ownedEmpty.hidden =
                true;
        }


        if (joinedEmpty) {
            joinedEmpty.hidden =
                true;
        }
    }


    const tabs =
        document.querySelectorAll(
            ".my-courses-tab"
        );


    const contents =
        document.querySelectorAll(
            ".my-courses-content"
        );


    tabs.forEach(
        (tab) => {
            tab.addEventListener(
                "click",
                () => {
                    tabs.forEach(
                        (item) => {
                            item.classList.remove(
                                "active"
                            );
                        }
                    );


                    contents.forEach(
                        (content) => {
                            content.classList.remove(
                                "active"
                            );
                        }
                    );


                    tab.classList.add(
                        "active"
                    );


                    const target =
                        document.getElementById(
                            tab.dataset.tab
                        );


                    if (target) {
                        target.classList.add(
                            "active"
                        );
                    }
                }
            );
        }
    );
}


/* Отладка */

window.initCoursesPage =
    initCoursesPage;

window.initMyCoursesPage =
    initMyCoursesPage;

window.loadCourses =
    loadCourses;


/* Запуск */

document.addEventListener(
    "DOMContentLoaded",
    () => {
        initCoursesPage();
        initMyCoursesPage();
    }
);