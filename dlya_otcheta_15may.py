import logging
import requests
import re
import urllib3
from urllib.parse import urlparse, parse_qs

# --- Настройка логирования ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("court_scrape.log", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}
cookies = {"assistFontSize": "1"}

def extract_table(html: str) -> str:
    match = re.search(
        r'(<table[^>]+id=["\']tablcont["\'][\s\S]*?</table>)',
        html, flags=re.IGNORECASE
    )
    return match.group(1) if match else ""

def scrape_one(module_url: str) -> None:
    # 1) GET исходной страницы для Referer и параметров
    logging.info(f"Получаем форму поиска: {module_url}")
    resp = requests.get(
        module_url, headers=headers, cookies=cookies,
        verify=False, timeout=10
    )
    resp.raise_for_status()

    # 2) Парсим URL
    parsed = urlparse(module_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    qp = parse_qs(parsed.query)
    form_params = {
        "name":    qp.get('name',   ['sud_delo'])[0],
        "name_op": qp.get('name_op',['sf'])[0],
        "delo_id": qp.get('delo_id',['1540006'])[0],
        "srv_num": qp.get('srv_num',['1'])[0]
    }

    # 3) Формируем параметры поиска
    search_params = {
        "name":                   form_params["name"],
        "name_op":                "r",
        "delo_id":                form_params["delo_id"],
        "srv_num":                form_params["srv_num"],
        "case_type":              "0",
        "new":                    "0",
        "delo_table":             "u1_case",
        "u1_case__RESULT_DATE1D": "01.01.2010",
        "u1_case__RESULT_DATE2D": "31.12.2023",
        "Submit":                 "Найти"
    }
    headers["Referer"] = module_url

    # 4) Отправляем поиск
    logging.info("Отправляем поисковый запрос...")
    resp2 = requests.get(
        base_url, params=search_params,
        headers=headers, cookies=cookies,
        verify=False, timeout=10
    )
    resp2.raise_for_status()

    # 5) Сохраняем таблицу
    table_html = extract_table(resp2.text)
    if table_html:
        fname = "search_result.html"
        with open(fname, "w", encoding="utf-8") as f:
            f.write(table_html)
        logging.info(f"Таблица сохранена в {fname}")
    else:
        logging.warning("Таблица не найдена в ответе")

def main():
    # URL суда здесь
    module_url = "https://xyz.com/your-query?delo_id=1540006&srv_num=1"
    scrape_one(module_url)

if __name__ == "__main__":
    main()