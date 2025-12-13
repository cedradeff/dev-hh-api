import requests
import time
from dotenv import load_dotenv
from terminaltables import AsciiTable
import os

load_dotenv()
SJ_SECRET_KEY = os.environ["SJ_SECRET_KEY"]

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


def hh_request(language, page):
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": language,
        "professional_role": 96,
        "area": 1,
        "period": 30,
        "per_page": 100,
        "page": page
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def load_all_vacancies_hh(language):
    all_vacancies = []
    page = 0

    while True:

        data = hh_request(language, page)
        all_vacancies.extend(data["items"])

        if page >= data["pages"] - 1:
            break

        page += 1
        time.sleep(0.2)

    return all_vacancies


def sj_request(language, page, api_key):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": api_key}
    params = {
        "keyword": language,
        "town": 4,
        "count": 100,
        "page": page
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def load_all_vacancies_sj(language, api_key):
    all_vacancies = []
    page = 0
    while True:
        data = sj_request(language, page, api_key)
        all_vacancies.extend(data["objects"])
        if not data.get("more"):
            break
        page += 1
        time.sleep(0.2)
    return all_vacancies


def get_statistics(load_vacancies, predict_salary_func, api_key=None):
    statistics = {}
    for language in POPULAR_LANGS:
        if api_key:
            vacancies = load_vacancies(language, api_key)
        else:
            vacancies = load_vacancies(language)

        vacancies_found = len(vacancies)
        salaries = [predict_salary_func(v) for v in vacancies]
        salaries = [s for s in salaries if s is not None]

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
    return None


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get("salary")
    if salary is None or salary.get("currency") != "RUR":
        return None
    return predict_salary(salary.get("from"), salary.get("to"))


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy.get("payment_from")
    salary_to = vacancy.get("payment_to")
    currency = vacancy.get("currency")

    if currency is None or currency.lower() != "rub":
        return None

    if salary_from == 0 and salary_to == 0:
        return None

    return predict_salary(salary_from, salary_to)


def print_table(statistics, title):
    table_data = [["Язык программирования", "Вакансий найдено", "Вакансий обработано", "Средняя зарплата"]]
    for language, data in statistics.items():
        table_data.append([
            language.lower(),
            str(data["vacancies_found"]),
            str(data["vacancies_processed"]),
            str(data["average_salary"])
        ])
    table = AsciiTable(table_data, title)
    print(table.table)


def main():
    hh_stats = get_statistics(load_all_vacancies_hh, predict_rub_salary_hh)
    print_table(hh_stats, "HeadHunter Moscow--------")

    SJ_API_KEY = SJ_SECRET_KEY
    sj_stats = get_statistics(load_all_vacancies_sj, predict_rub_salary_sj, SJ_API_KEY)
    print_table(sj_stats, "SuperJob Moscow--------")


if __name__ == "__main__":
    main()
