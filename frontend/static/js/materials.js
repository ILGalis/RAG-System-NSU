const DOCUMENT_API = {
    list(spaceId) {
        return `/spaces/${encodeURIComponent(spaceId)}/documents`;
    },

    upload(spaceId) {
        return `/spaces/${encodeURIComponent(spaceId)}/documents`;
    }
};


const ALLOWED_DOCUMENT_EXTENSIONS = [
    "pdf",
    "docx",
    "txt"
];


const MAX_DOCUMENT_SIZE =
    20 * 1024 * 1024;


let selectedDocument = null;


/* Данные страницы */

function getMaterialsSpaceId() {
    const params =
        new URLSearchParams(
            window.location.search
        );

    return params.get(
        "space_id"
    );
}


function getMaterialsAccessToken() {
    return localStorage.getItem(
        "access_token"
    );
}


function getMaterialsCurrentUserId() {
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


/* Авторизация */

function clearMaterialsAuthData() {
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


function redirectMaterialsToLogin() {
    window.location.href =
        "../login.html";
}


/* Ответ API */

async function readMaterialsResponse(
    response
) {
    if (response.status === 204) {
        return {};
    }


    try {
        return await response.json();
    } catch {
        return {};
    }
}


function getMaterialsErrorMessage(
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


/* Файлы */

function getFileExtension(
    fileName
) {
    const parts =
        fileName
            .toLowerCase()
            .split(".");


    return parts.length > 1
        ? parts.pop()
        : "";
}


function formatFileSize(bytes) {
    const value =
        Number(bytes);


    if (
        !Number.isFinite(value) ||
        value < 0
    ) {
        return "";
    }


    if (value < 1024) {
        return `${value} Б`;
    }


    if (
        value <
        1024 * 1024
    ) {
        return `${
            (
                value /
                1024
            ).toFixed(1)
        } КБ`;
    }


    return `${
        (
            value /
            (
                1024 *
                1024
            )
        ).toFixed(1)
    } МБ`;
}


function validateDocument(file) {
    if (!file) {
        return "Выберите документ для загрузки.";
    }


    const extension =
        getFileExtension(
            file.name
        );


    if (
        !ALLOWED_DOCUMENT_EXTENSIONS
            .includes(
                extension
            )
    ) {
        return "Поддерживаются только файлы PDF, DOCX и TXT.";
    }


    if (
        file.size >
        MAX_DOCUMENT_SIZE
    ) {
        return "Максимальный размер файла — 20 МБ.";
    }


    if (file.size === 0) {
        return "Файл пустой.";
    }


    return "";
}


/* Ошибка загрузки */

function showUploadError(message) {
    const error =
        document.getElementById(
            "upload-error"
        );


    if (error) {
        error.textContent =
            message;
    }
}


function clearUploadError() {
    showUploadError("");
}


/* Выбранный файл */

function renderSelectedDocument() {
    const container =
        document.getElementById(
            "selected-file"
        );

    const name =
        document.getElementById(
            "selected-file-name"
        );

    const size =
        document.getElementById(
            "selected-file-size"
        );

    const uploadButton =
        document.getElementById(
            "document-upload-button"
        );


    if (
        !container ||
        !name ||
        !size
    ) {
        return;
    }


    if (!selectedDocument) {
        container.hidden =
            true;

        name.textContent =
            "";

        size.textContent =
            "";


        if (uploadButton) {
            uploadButton.disabled =
                true;
        }


        return;
    }


    name.textContent =
        selectedDocument.name;


    size.textContent =
        formatFileSize(
            selectedDocument.size
        );


    container.hidden =
        false;


    if (uploadButton) {
        uploadButton.disabled =
            false;
    }
}


function setSelectedDocument(file) {
    clearUploadError();


    const validationError =
        validateDocument(file);


    if (validationError) {
        selectedDocument =
            null;


        renderSelectedDocument();


        showUploadError(
            validationError
        );


        return;
    }


    selectedDocument =
        file;


    renderSelectedDocument();
}


function clearSelectedDocument() {
    const input =
        document.getElementById(
            "document-file"
        );


    selectedDocument =
        null;


    if (input) {
        input.value = "";
    }


    renderSelectedDocument();

    clearUploadError();
}


/* Состояние загрузки */

function setUploadLoading(
    loading
) {
    const button =
        document.getElementById(
            "document-upload-button"
        );


    if (!button) {
        return;
    }


    button.disabled =
        loading ||
        !selectedDocument;


    button.textContent =
        loading
            ? "Загрузка..."
            : "Загрузить документ";
}


/* Данные документов */

function getDocumentsFromResponse(
    data
) {
    if (Array.isArray(data)) {
        return data;
    }


    if (
        Array.isArray(
            data?.documents
        )
    ) {
        return data.documents;
    }


    if (
        Array.isArray(
            data?.items
        )
    ) {
        return data.items;
    }


    if (
        Array.isArray(
            data?.results
        )
    ) {
        return data.results;
    }


    return [];
}


function getDocumentName(
    documentItem
) {
    return (
        documentItem.source_name ||
        documentItem.filename ||
        documentItem.file_name ||
        documentItem.original_name ||
        documentItem.name ||
        "Документ"
    );
}


function getDocumentSize(
    documentItem
) {
    return (
        documentItem.file_size ??
        documentItem.size_bytes ??
        documentItem.size ??
        null
    );
}


function getDocumentStatus(
    documentItem
) {
    return (
        documentItem.status ||
        documentItem.processing_status ||
        ""
    );
}


function getDocumentStatusLabel(
    status
) {
    switch (
        String(status)
            .toLowerCase()
    ) {
        case "ready":
        case "completed":
        case "indexed":
            return "Готов";

        case "processing":
            return "Обработка";

        case "pending":
            return "В очереди";

        case "failed":
        case "error":
            return "Ошибка";

        default:
            return status || "";
    }
}


/* Карточка документа */

function createDocumentCard(
    documentItem
) {
    const card =
        document.createElement(
            "article"
        );


    card.className =
        "material-item";


    const icon =
        document.createElement(
            "div"
        );


    icon.className =
        "material-item-icon";


    icon.innerHTML = `
        <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
        >
            <path
                d="M14 2H6C4.9 2 4 2.9 4 4V20C4 21.1 4.9 22 6 22H18C19.1 22 20 21.1 20 20V8L14 2Z"
            ></path>

            <path
                d="M14 2V8H20"
            ></path>
        </svg>
    `;


    const body =
        document.createElement(
            "div"
        );


    body.className =
        "material-item-body";


    const name =
        document.createElement(
            "strong"
        );


    name.className =
        "material-item-name";


    name.textContent =
        getDocumentName(
            documentItem
        );


    const meta =
        document.createElement(
            "div"
        );


    meta.className =
        "material-item-meta";


    const sizeValue =
        getDocumentSize(
            documentItem
        );


    if (sizeValue !== null) {
        const size =
            document.createElement(
                "span"
            );


        size.textContent =
            formatFileSize(
                sizeValue
            );


        meta.append(
            size
        );
    }


    const statusValue =
        getDocumentStatus(
            documentItem
        );


    if (statusValue) {
        const status =
            document.createElement(
                "span"
            );


        status.className =
            "material-status";


        status.dataset.status =
            String(
                statusValue
            ).toLowerCase();


        status.textContent =
            getDocumentStatusLabel(
                statusValue
            );


        meta.append(
            status
        );
    }


    body.append(
        name,
        meta
    );


    card.append(
        icon,
        body
    );


    return card;
}


/* Состояния списка */

function showMaterialsState(
    state,
    message = ""
) {
    const loading =
        document.getElementById(
            "materials-loading"
        );

    const empty =
        document.getElementById(
            "materials-empty"
        );

    const unavailable =
        document.getElementById(
            "materials-unavailable"
        );

    const error =
        document.getElementById(
            "materials-error"
        );

    const list =
        document.getElementById(
            "materials-list"
        );


    if (loading) {
        loading.hidden =
            state !==
            "loading";
    }


    if (empty) {
        empty.hidden =
            state !==
            "empty";
    }


    if (unavailable) {
        unavailable.hidden =
            true;
    }


    if (error) {
        error.hidden =
            state !==
            "error";


        error.textContent =
            state === "error"
                ? message
                : "";
    }


    if (list) {
        list.hidden =
            state !==
            "list";
    }
}


function renderDocuments(
    documents
) {
    const list =
        document.getElementById(
            "materials-list"
        );


    if (!list) {
        return;
    }


    list.replaceChildren();


    if (!documents.length) {
        showMaterialsState(
            "empty"
        );

        return;
    }


    documents.forEach(
        (documentItem) => {
            list.append(
                createDocumentCard(
                    documentItem
                )
            );
        }
    );


    showMaterialsState(
        "list"
    );
}


/* Загрузка списка */

async function loadDocuments() {
    const spaceId =
        getMaterialsSpaceId();

    const token =
        getMaterialsAccessToken();


    if (!spaceId) {
        showMaterialsState(
            "error",
            "Курс не выбран."
        );

        return;
    }


    if (!token) {
        redirectMaterialsToLogin();

        return;
    }


    showMaterialsState(
        "loading"
    );


    try {
        const response =
            await fetch(
                DOCUMENT_API.list(
                    spaceId
                ),
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
            clearMaterialsAuthData();

            redirectMaterialsToLogin();

            return;
        }


        const data =
            await readMaterialsResponse(
                response
            );


        if (!response.ok) {
            showMaterialsState(
                "error",
                getMaterialsErrorMessage(
                    data,
                    "Не удалось загрузить материалы курса."
                )
            );

            return;
        }


        renderDocuments(
            getDocumentsFromResponse(
                data
            )
        );

    } catch {
        showMaterialsState(
            "error",
            "Не удалось подключиться к серверу."
        );
    }
}


/* Загрузка документа */

async function uploadDocument() {
    const spaceId =
        getMaterialsSpaceId();

    const token =
        getMaterialsAccessToken();


    clearUploadError();


    if (!spaceId) {
        showUploadError(
            "Курс не выбран."
        );

        return;
    }


    if (!token) {
        redirectMaterialsToLogin();

        return;
    }


    const validationError =
        validateDocument(
            selectedDocument
        );


    if (validationError) {
        showUploadError(
            validationError
        );

        return;
    }


    const formData =
        new FormData();


    formData.append(
        "file",
        selectedDocument
    );


    setUploadLoading(
        true
    );


    try {
        const response =
            await fetch(
                DOCUMENT_API.upload(
                    spaceId
                ),
                {
                    method:
                        "POST",

                    headers: {
                        "Authorization":
                            `Bearer ${token}`
                    },

                    body:
                        formData
                }
            );


        if (
            response.status ===
            401
        ) {
            clearMaterialsAuthData();

            redirectMaterialsToLogin();

            return;
        }


        const data =
            await readMaterialsResponse(
                response
            );


        if (!response.ok) {
            showUploadError(
                getMaterialsErrorMessage(
                    data,
                    "Не удалось загрузить документ."
                )
            );

            return;
        }


        clearSelectedDocument();


        await loadDocuments();

    } catch {
        showUploadError(
            "Не удалось подключиться к серверу."
        );

    } finally {
        setUploadLoading(
            false
        );
    }
}


/* Права владельца */

function configureUploadAccess(
    course
) {
    const uploadCard =
        document.getElementById(
            "materials-upload-card"
        );

    const currentUserId =
        getMaterialsCurrentUserId();


    if (!uploadCard) {
        return;
    }


    uploadCard.hidden =
        course.owner_id !==
        currentUserId;
}


/* Инициализация */

function initMaterialsPage() {
    const form =
        document.getElementById(
            "document-upload-form"
        );

    const input =
        document.getElementById(
            "document-file"
        );

    const dropZone =
        document.getElementById(
            "file-drop-zone"
        );

    const removeButton =
        document.getElementById(
            "remove-selected-file"
        );


    if (
        !form ||
        !input ||
        !dropZone
    ) {
        return;
    }


    renderSelectedDocument();


    input.addEventListener(
        "change",
        () => {
            setSelectedDocument(
                input.files[0] ??
                null
            );
        }
    );


    dropZone.addEventListener(
        "dragover",
        (event) => {
            event.preventDefault();


            dropZone.classList.add(
                "drag-active"
            );
        }
    );


    dropZone.addEventListener(
        "dragleave",
        () => {
            dropZone.classList.remove(
                "drag-active"
            );
        }
    );


    dropZone.addEventListener(
        "drop",
        (event) => {
            event.preventDefault();


            dropZone.classList.remove(
                "drag-active"
            );


            const file =
                event.dataTransfer
                    ?.files?.[0] ??
                null;


            setSelectedDocument(
                file
            );
        }
    );


    if (removeButton) {
        removeButton.addEventListener(
            "click",
            clearSelectedDocument
        );
    }


    form.addEventListener(
        "submit",
        (event) => {
            event.preventDefault();


            uploadDocument();
        }
    );


    loadDocuments();
}


document.addEventListener(
    "course:loaded",
    (event) => {
        configureUploadAccess(
            event.detail
        );
    }
);


document.addEventListener(
    "DOMContentLoaded",
    initMaterialsPage
);