from typing import Literal
#MVP : список преподавателей захардкожен :)
#TODO: стоит заглушка-файл teachers.txt который лежит в backend/core(в нем вписано три почты)
#TODO: заменить на реальный источник (список преподавателей из деканата/БД/файла) - наверное нет

TEACHER_EMAILS: set[str] = {
    "m.tkachenko@g.nsu.ru",
    "v.bobrovnikov@g.nsu.ru",
    "i.gorin@alumni.nsu.ru"
}


def resolve_role(email: str) -> Literal["teacher", "student"]:
    return "teacher" if email.strip().lower() in TEACHER_EMAILS else "student"