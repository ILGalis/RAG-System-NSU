const ALLOWED_DOCUMENT_EXTENSIONS = [
    "pdf",
    "docx",
    "txt"
];


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
    if (bytes < 1024) {
        return `${bytes} Б`;
    }


    if (
        bytes <
        1024 * 1024
    ) {
        return `${
            (
                bytes /
                1024
            ).toFixed(1)
        } КБ`;
    }


    return `${
        (
            bytes /
            (
                1024 *
                1024
            )
        ).toFixed(1)
    } МБ`;
}


function renderSelectedFile(
    file
) {
    const selectedFile =
        document.getElementById(
            "selected-file"
        );


    if (!selectedFile) {
        return;
    }


    if (!file) {
        selectedFile.hidden =
            true;

        selectedFile.textContent =
            "";

        return;
    }


    selectedFile.textContent =
        `${file.name} · ${formatFileSize(file.size)}`;

    selectedFile.hidden =
        false;
}


function validateDocument(
    file
) {
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


    return "";
}


document.addEventListener(
    "DOMContentLoaded",
    () => {
        const form =
            document.getElementById(
                "document-upload-form"
            );

        const input =
            document.getElementById(
                "document-file"
            );

        const error =
            document.getElementById(
                "upload-error"
            );


        if (
            !form ||
            !input ||
            !error
        ) {
            return;
        }


        input.addEventListener(
            "change",
            () => {
                error.textContent =
                    "";

                renderSelectedFile(
                    input.files[0] ??
                        null
                );
            }
        );


        form.addEventListener(
            "submit",
            (event) => {
                event.preventDefault();


                const file =
                    input.files[0] ??
                    null;


                const validationError =
                    validateDocument(
                        file
                    );


                if (
                    validationError
                ) {
                    error.textContent =
                        validationError;

                    return;
                }


                error.textContent =
                    "Загрузка документов пока недоступна: backend API документов ещё не реализован.";
            }
        );
    }
);