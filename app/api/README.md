тут распишу про ручки чтобы чуть удобнее было ориентироваться.
/auth/register, /auth/verify-email, /auth/login	POST	все
/auth/me	GET	любой авторизованный
/spaces	POST (создать)	любой авторизованный
/spaces	GET (список)	любой авторизованный (свой + membership + public)
/spaces/{id}	GET	owner, member, или любой авторизованный если public
/spaces/{id}	PATCH / DELETE	только owner
/spaces/{id}/documents	POST (upload)	owner + member (не public-only)
/spaces/{id}/documents	GET	как /spaces/{id}
/spaces/{id}/documents/{doc_id}	DELETE	owner (по умолчанию)