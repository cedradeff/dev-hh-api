import requests
import time
from dotenv import load_dotenv
from terminaltables import AsciiTable
import os


POPULAR_LANGS = [
    "Python",
    "Java",
    "JavaScript",
    "C++",
    "C#",
    "Go",
    "PHP",
    "TypeScript",
    "Kotlin",
    "Swift"
]

# HeadHunter params
HH_PROFESSIONAL_ROLE = 96   # роль "Разработчик"
HH_AREA_MOSCOW = 1          # Москва
HH_PERIOD_DAYS = 30         # вакансии за последние 30 дней
HH_PER_PAGE = 100           # вакансий на странице

# SuperJob params
SJ_TOWN_MOSCOW = 4          # Москва
SJ_PER_PAGE = 100           # вакансий на странице


def request_hh(language, page):
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": language,
        "professional_role": HH_PROFESSIONAL_ROLE,
        "area": HH_AREA_MOSCOW,
        "period": HH_PERIOD_DAYS,
        "per_page": HH_PER_PAGE,
        "page": page
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def load_all_vacancies_hh(language):
    all_vacancies = []
    page = 0

    while True:

        hh_response = request_hh(language, page)
        all_vacancies.extend(hh_response["items"])

        if page >= hh_response["pages"] - 1:
            break

        page += 1
        time.sleep(0.2)

    return all_vacancies, hh_response["found"]


def request_sj(language, page, api_key):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": api_key}
    params = {
        "keyword": language,
        "town": SJ_TOWN_MOSCOW,
        "count": SJ_PER_PAGE,
        "page": page
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def load_all_vacancies_sj(language, api_key):
    all_vacancies = []
    page = 0
    while True:
        sj_response = request_sj(language, page, api_key)
        all_vacancies.extend(sj_response["objects"])
        if not sj_response.get("more"):
            break
        page += 1
        time.sleep(0.2)
    return all_vacancies, sj_response["total"]


def get_statistics(load_vacancies, predict_salary_func):
    statistics = {}

    for language in POPULAR_LANGS:
        vacancies, vacancies_found = load_vacancies(language)

        salaries = []
        for vacancy in vacancies:
            salary = predict_salary_func(vacancy)
            if salary:
                salaries.append(salary)

        vacancies_processed = len(salaries)
        average_salary = sum(salaries) // vacancies_processed if vacancies_processed else 0

        statistics[language] = {
            "vacancies_found": vacancies_found,
            "vacancies_processed": vacancies_processed,
            "average_salary": average_salary
        }
    return statistics


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return int((salary_from + salary_to) / 2)
    if salary_from:
        return int(salary_from * 1.2)
    if salary_to:
        return int(salary_to * 0.8)
    return 0


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get("salary")
    if salary is None or salary.get("currency") != "RUR":
        return 0
    return predict_salary(salary.get("from"), salary.get("to"))


def predict_rub_salary_sj(vacancy):
    if vacancy.get("currency", "").lower() != "rub":
        return 0

    salary_from = vacancy.get("payment_from", 0)
    salary_to = vacancy.get("payment_to", 0)

    return predict_salary(salary_from, salary_to)


def print_table(statistics, title):
    table_data = [["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]]
    for language, language_stats in statistics.items():
        table_data.append([
            language.lower(),
            str(language_stats["vacancies_found"]),
            str(language_stats["vacancies_processed"]),
            str(language_stats["average_salary"])
        ])
    table = AsciiTable(table_data, title)
    print(table.table)


def main():

    load_dotenv()
    SJ_SECRET_KEY = os.environ["SJ_SECRET_KEY"]

    hh_stats = get_statistics(load_all_vacancies_hh, predict_rub_salary_hh)
    print_table(hh_stats, "HeadHunter Moscow--------")

    SJ_API_KEY = SJ_SECRET_KEY
    sj_stats = get_statistics(
        lambda lang: load_all_vacancies_sj(lang, SJ_API_KEY),
        predict_rub_salary_sj
    )
    print_table(sj_stats, "SuperJob Moscow--------")


if __name__ == "__main__":
    main()
