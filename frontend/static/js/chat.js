const CHAT_API = {
    ask(spaceId) {
        return `/spaces/${encodeURIComponent(spaceId)}/ask`;
    }
};


let chatSending = false;


/* Данные страницы */

function getChatSpaceId() {
    const params =
        new URLSearchParams(
            window.location.search
        );

    return params.get(
        "space_id"
    );
}


function getChatAccessToken() {
    return localStorage.getItem(
        "access_token"
    );
}


function clearChatAuthData() {
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


/* Ответ API */

async function readChatResponse(
    response
) {
    try {
        return await response.json();
    } catch {
        return {};
    }
}


function getChatErrorMessage(
    response,
    data
) {
    if (response.status === 404) {
        return "Сервис ответов пока не подключён к backend.";
    }


    if (response.status === 429) {
        return "Сервис временно занят. Попробуйте отправить вопрос ещё раз.";
    }


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


    return "Не удалось получить ответ.";
}


/* Состояние */

function showChatError(message) {
    const error =
        document.getElementById(
            "chat-error"
        );


    if (error) {
        error.textContent =
            message;
    }
}


function clearChatError() {
    showChatError("");
}


function hideChatEmptyState() {
    const empty =
        document.getElementById(
            "chat-empty"
        );


    if (empty) {
        empty.hidden =
            true;
    }
}


function setChatLoading(loading) {
    const indicator =
        document.getElementById(
            "chat-loading"
        );


    chatSending =
        loading;


    if (indicator) {
        indicator.hidden =
            !loading;
    }


    updateChatSubmitState();


    if (loading) {
        scrollChatToBottom();
    }
}


function updateChatSubmitState() {
    const textarea =
        document.getElementById(
            "chat-question"
        );

    const button =
        document.getElementById(
            "chat-submit"
        );


    if (
        !textarea ||
        !button
    ) {
        return;
    }


    button.disabled =
        chatSending ||
        !textarea.value.trim();
}


/* Поле вопроса */

function resizeChatTextarea() {
    const textarea =
        document.getElementById(
            "chat-question"
        );


    if (!textarea) {
        return;
    }


    textarea.style.height =
        "auto";


    textarea.style.height =
        `${Math.min(
            textarea.scrollHeight,
            150
        )}px`;
}


/* Сообщения */

function scrollChatToBottom() {
    const messages =
        document.getElementById(
            "chat-messages"
        );


    if (!messages) {
        return;
    }


    messages.scrollTop =
        messages.scrollHeight;
}


function createUserMessage(
    question
) {
    const message =
        document.createElement(
            "article"
        );


    message.className =
        "chat-message chat-message-user";


    const body =
        document.createElement(
            "div"
        );


    body.className =
        "chat-message-body";


    body.textContent =
        question;


    message.append(
        body
    );


    return message;
}


function getSourcePages(
    source
) {
    if (
        !Array.isArray(
            source.page_numbers
        ) ||
        !source.page_numbers.length
    ) {
        return "";
    }


    const pages =
        source.page_numbers
            .filter(
                (page) =>
                    Number.isFinite(
                        Number(page)
                    )
            );


    if (!pages.length) {
        return "";
    }


    return `стр. ${pages.join(", ")}`;
}


function createSourceElement(
    source
) {
    const element =
        document.createElement(
            "article"
        );


    element.className =
        "chat-source";


    const header =
        document.createElement(
            "div"
        );


    header.className =
        "chat-source-header";


    const ref =
        document.createElement(
            "span"
        );


    ref.className =
        "chat-source-ref";


    ref.textContent =
        source.ref || "Источник";


    const name =
        document.createElement(
            "span"
        );


    name.className =
        "chat-source-name";


    name.textContent =
        source.source_name ||
        "Документ";


    header.append(
        ref,
        name
    );


    const pages =
        getSourcePages(
            source
        );


    if (pages) {
        const page =
            document.createElement(
                "span"
            );


        page.className =
            "chat-source-page";


        page.textContent =
            pages;


        header.append(
            page
        );
    }


    const quote =
        document.createElement(
            "p"
        );


    quote.className =
        "chat-source-quote";


    quote.textContent =
        source.quote || "";


    element.append(
        header,
        quote
    );


    return element;
}


function createAssistantMessage(
    data
) {
    const message =
        document.createElement(
            "article"
        );


    message.className =
        "chat-message chat-message-assistant";


    if (!data.found) {
        message.classList.add(
            "chat-message-not-found"
        );
    }


    const avatar =
        document.createElement(
            "div"
        );


    avatar.className =
        "chat-assistant-avatar";


    avatar.textContent =
        "AI";


    const body =
        document.createElement(
            "div"
        );


    body.className =
        "chat-message-body";


    const answer =
        document.createElement(
            "div"
        );


    answer.className =
        "chat-answer";


    answer.textContent =
        String(
            data.answer ||
            "В материалах этого пространства недостаточно информации для ответа."
        );


    body.append(
        answer
    );


    if (
        data.found &&
        Array.isArray(
            data.sources
        ) &&
        data.sources.length
    ) {
        const sources =
            document.createElement(
                "div"
            );


        sources.className =
            "chat-sources";


        const title =
            document.createElement(
                "p"
            );


        title.className =
            "chat-sources-title";


        title.textContent =
            "Источники";


        sources.append(
            title
        );


        data.sources.forEach(
            (source) => {
                sources.append(
                    createSourceElement(
                        source
                    )
                );
            }
        );


        body.append(
            sources
        );
    }


    message.append(
        avatar,
        body
    );


    return message;
}


function appendChatMessage(
    element
) {
    const messages =
        document.getElementById(
            "chat-messages"
        );

    const loading =
        document.getElementById(
            "chat-loading"
        );


    if (!messages) {
        return;
    }


    if (
        loading &&
        loading.parentElement ===
        messages
    ) {
        messages.insertBefore(
            element,
            loading
        );
    } else {
        messages.append(
            element
        );
    }


    scrollChatToBottom();
}


/* Отправка вопроса */

async function sendChatQuestion(
    question
) {
    const spaceId =
        getChatSpaceId();

    const token =
        getChatAccessToken();


    if (!spaceId) {
        showChatError(
            "Курс не выбран."
        );

        return;
    }


    if (!token) {
        window.location.href =
            "../login.html";

        return;
    }


    clearChatError();

    hideChatEmptyState();


    appendChatMessage(
        createUserMessage(
            question
        )
    );


    setChatLoading(
        true
    );


    try {
        const response =
            await fetch(
                CHAT_API.ask(
                    spaceId
                ),
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${token}`
                    },

                    body:
                        JSON.stringify({
                            question
                        })
                }
            );


        if (
            response.status ===
            401
        ) {
            clearChatAuthData();

            window.location.href =
                "../login.html";

            return;
        }


        const data =
            await readChatResponse(
                response
            );


        if (!response.ok) {
            showChatError(
                getChatErrorMessage(
                    response,
                    data
                )
            );

            return;
        }


        appendChatMessage(
            createAssistantMessage(
                data
            )
        );

    } catch {
        showChatError(
            "Не удалось подключиться к серверу."
        );

    } finally {
        setChatLoading(
            false
        );
    }
}


/* Инициализация */

function initChatPage() {
    const form =
        document.getElementById(
            "chat-form"
        );

    const textarea =
        document.getElementById(
            "chat-question"
        );


    if (
        !form ||
        !textarea
    ) {
        return;
    }


    textarea.addEventListener(
        "input",
        () => {
            resizeChatTextarea();

            updateChatSubmitState();

            clearChatError();
        }
    );


    textarea.addEventListener(
        "keydown",
        (event) => {
            if (
                event.key ===
                    "Enter" &&
                !event.shiftKey &&
                !event.isComposing
            ) {
                event.preventDefault();


                if (
                    !chatSending &&
                    textarea.value.trim()
                ) {
                    form.requestSubmit();
                }
            }
        }
    );


    form.addEventListener(
        "submit",
        (event) => {
            event.preventDefault();


            if (chatSending) {
                return;
            }


            const question =
                textarea.value
                    .trim();


            if (!question) {
                return;
            }


            textarea.value =
                "";


            resizeChatTextarea();

            updateChatSubmitState();


            sendChatQuestion(
                question
            );
        }
    );


    updateChatSubmitState();

    resizeChatTextarea();
}


document.addEventListener(
    "DOMContentLoaded",
    initChatPage
);