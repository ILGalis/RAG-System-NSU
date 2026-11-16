let allCourses = [];


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


function redirectToLogin() {
    window.location.href =
        "login.html";
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
        document.createElement("a");

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


    header.append(title);


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
        getAccessLabel(course);

    meta.append(access);


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

        meta.append(owner);
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


/* Все курсы */

function initCoursesPage() {
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

    const currentUserId =
        getCurrentUserId();


    loadCourses()
        .then(
            (courses) => {

                /*
                 * В разделе "Все курсы"
                 * отображаются только
                 * публичные курсы.
                 */
                allCourses =
                    courses.filter(
                        (course) =>
                            course.access_mode ===
                            "public"
                    );


                renderCourseList(
                    grid,
                    allCourses,
                    currentUserId
                );


                if (empty) {
                    empty.hidden =
                        allCourses.length !==
                        0;
                }
            }
        )
        .catch(
            (error) => {
                showPageError(
                    error.message
                );

                if (empty) {
                    empty.hidden =
                        true;
                }
            }
        );


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
                    currentUserId
                );


                if (empty) {
                    empty.hidden =
                        filtered.length !==
                        0;
                }
            }
        );
    }
}


/* Мои курсы */

function initMyCoursesPage() {
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

    const currentUserId =
        getCurrentUserId();


    loadCourses()
        .then(
            (courses) => {

                /*
                 * Все курсы, которыми
                 * пользователь владеет.
                 */
                const ownedCourses =
                    courses.filter(
                        (course) =>
                            course.owner_id ===
                            currentUserId
                    );


                /*
                 * Все курсы, в которых
                 * пользователь состоит.
                 *
                 * Владелец курса тоже
                 * считается участником,
                 * поэтому его собственные
                 * курсы отображаются и здесь.
                 *
                 * Для чужих курсов backend
                 * должен возвращать is_member.
                 */
                const joinedCourses =
                    courses.filter(
                        (course) =>
                            course.owner_id ===
                                currentUserId ||
                            course.is_member ===
                                true
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
            }
        )
        .catch(
            (error) => {
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
        );


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
                        (item) =>
                            item.classList.remove(
                                "active"
                            )
                    );


                    contents.forEach(
                        (content) =>
                            content.classList.remove(
                                "active"
                            )
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


document.addEventListener(
    "DOMContentLoaded",
    () => {
        initCoursesPage();
        initMyCoursesPage();
    }
);