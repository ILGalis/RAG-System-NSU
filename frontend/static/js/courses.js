const MOCK_USER_ID = 1;

const MOCK_COURSES = [
    {
        id: 1,
        name: "Математический анализ",
        owner_id: 1,
        access_mode: "public",
        relation: "owned"
    },
    {
        id: 2,
        name: "Алгоритмы и структуры данных",
        owner_id: 1,
        access_mode: "private",
        relation: "owned"
    },
    {
        id: 3,
        name: "Основы машинного обучения",
        owner_id: 2,
        access_mode: "public",
        relation: "joined"
    },
    {
        id: 4,
        name: "Базы данных",
        owner_id: 3,
        access_mode: "private",
        relation: "joined"
    },
    {
        id: 5,
        name: "Линейная алгебра",
        owner_id: 4,
        access_mode: "public",
        relation: null
    },
    {
        id: 6,
        name: "Компьютерные сети",
        owner_id: 5,
        access_mode: "public",
        relation: null
    }
];


let allCourses = [];


/* Тестовый режим */

function getCurrentUserId() {
    return MOCK_USER_ID;
}


async function loadCourses() {
    return MOCK_COURSES;
}


/* Backend режим

function getCurrentUserId() {
    const value =
        Number(localStorage.getItem("user_id"));

    return Number.isFinite(value)
        ? value
        : null;
}


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


async function loadCourses() {
    const token =
        localStorage.getItem("access_token");

    if (!token) {
        window.location.href = "login.html";

        return [];
    }

    const response = await fetch("/spaces", {
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (response.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("token_type");
        localStorage.removeItem("user_id");

        window.location.href = "login.html";

        return [];
    }

    const data =
        await readResponse(response);

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

*/


function getAccessLabel(course) {
    return course.access_mode === "public"
        ? "Публичный курс"
        : "Приватный курс";
}


function createCourseCard(
    course,
    currentUserId
) {
    const card =
        document.createElement("a");

    card.className = "course-card";

    card.href =
        `course/chat.html?space_id=${encodeURIComponent(course.id)}`;


    const header =
        document.createElement("div");

    header.className =
        "course-card-header";


    const title =
        document.createElement("h2");

    title.textContent =
        course.name;


    header.append(title);


    const meta =
        document.createElement("div");

    meta.className =
        "course-card-meta";


    const access =
        document.createElement("span");

    access.className =
        "course-access";

    if (course.access_mode === "public") {
        access.classList.add("public");
    }

    access.textContent =
        getAccessLabel(course);

    meta.append(access);


    if (course.owner_id === currentUserId) {
        const owner =
            document.createElement("span");

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

    courses.forEach((course) => {
        container.append(
            createCourseCard(
                course,
                currentUserId
            )
        );
    });
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
        .then((courses) => {
            allCourses = courses;

            renderCourseList(
                grid,
                allCourses,
                currentUserId
            );

            empty.hidden =
                allCourses.length !== 0;
        })
        .catch((error) => {
            showPageError(
                error.message
            );
        });


    searchInput.addEventListener(
        "input",
        () => {
            const query =
                searchInput
                    .value
                    .trim()
                    .toLowerCase();

            const filtered =
                allCourses.filter(
                    (course) =>
                        course.name
                            .toLowerCase()
                            .includes(query)
                );

            renderCourseList(
                grid,
                filtered,
                currentUserId
            );

            empty.hidden =
                filtered.length !== 0;
        }
    );
}


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
        .then((courses) => {

            const ownedCourses =
                courses.filter(
                    (course) =>
                        course.relation === "owned"
                );


            const joinedCourses =
                courses.filter(
                    (course) =>
                        course.relation === "joined"
                );


            /* Backend режим

            const ownedCourses =
                courses.filter(
                    (course) =>
                        course.owner_id === currentUserId
                );


            const joinedCourses =
                courses.filter(
                    (course) =>
                        course.owner_id !== currentUserId &&
                        course.access_mode === "private"
                );

            */


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


            ownedCount.textContent =
                String(
                    ownedCourses.length
                );

            joinedCount.textContent =
                String(
                    joinedCourses.length
                );


            ownedEmpty.hidden =
                ownedCourses.length !== 0;

            joinedEmpty.hidden =
                joinedCourses.length !== 0;
        })
        .catch((error) => {
            showPageError(
                error.message
            );
        });


    const tabs =
        document.querySelectorAll(
            ".my-courses-tab"
        );

    const contents =
        document.querySelectorAll(
            ".my-courses-content"
        );


    tabs.forEach((tab) => {
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


                document
                    .getElementById(
                        tab.dataset.tab
                    )
                    .classList.add(
                        "active"
                    );
            }
        );
    });
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        initCoursesPage();
        initMyCoursesPage();
    }
);