import requests
from bs4 import BeautifulSoup
import logging
import time
import re

logger = logging.getLogger(**name**)

HEADERS = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 “
“(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36”,
“Accept-Language”: “ru-RU,ru;q=0.9”,
“Accept”: “text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8”,
}

BASE_URL = “https://krisha.kz”

def build_url(params: dict) -> str:
“”“Строим URL для поиска на krisha.kz”””
deal_type = params.get(‘deal_type’, ‘rent’)
city = params.get(‘city’, ‘astana’)

```
if deal_type == 'rent':
    path = f"/arenda/kvartiry/{city}/"
else:
    path = f"/prodazha/kvartiry/{city}/"

query_parts = []

rooms = params.get('rooms')
if rooms and rooms != 'any':
    if rooms == '5':
        query_parts.append("das[live.rooms][]=5&das[live.rooms][]=6&das[live.rooms][]=7")
    else:
        query_parts.append(f"das[live.rooms][]={rooms}")

price_min = params.get('price_min')
price_max = params.get('price_max')
if price_min:
    query_parts.append(f"das[price][from]={price_min}")
if price_max:
    query_parts.append(f"das[price][to]={price_max}")

area_min = params.get('area_min')
area_max = params.get('area_max')
if area_min:
    query_parts.append(f"das[live.square][from]={area_min}")
if area_max:
    query_parts.append(f"das[live.square][to]={area_max}")

district = params.get('district')
if district:
    query_parts.append(f"q={requests.utils.quote(district)}")

complex_name = params.get('complex')
if complex_name:
    if not district:
        query_parts.append(f"q={requests.utils.quote(complex_name)}")
    else:
        query_parts[0] = f"q={requests.utils.quote(district + ' ' + complex_name)}"

url = BASE_URL + path
if query_parts:
    url += "?" + "&".join(query_parts)

logger.info(f"Поиск по URL: {url}")
return url
```

def parse_listing(card) -> dict | None:
“”“Парсит одну карточку объявления”””
try:
# Ссылка и ID
link_tag = card.find(‘a’, class_=‘a-card__title’)
if not link_tag:
link_tag = card.find(‘a’, href=re.compile(r’/a/show/’))

```
    if not link_tag:
        return None
    
    url = BASE_URL + link_tag.get('href', '')
    title = link_tag.get_text(strip=True)

    # Цена
    price_tag = card.find('strong', class_='a-card__price')
    if not price_tag:
        price_tag = card.find(class_=re.compile(r'price'))
    price = price_tag.get_text(strip=True) if price_tag else 'Цена не указана'

    # Адрес
    address_tag = card.find('div', class_='a-card__subtitle')
    if not address_tag:
        address_tag = card.find(class_=re.compile(r'subtitle|address'))
    address = address_tag.get_text(strip=True) if address_tag else 'Адрес не указан'

    # Параметры (комнаты, площадь, этаж)
    params_tag = card.find('div', class_='a-card__params')
    rooms = ''
    area = ''
    floor = ''
    
    if params_tag:
        params_text = params_tag.get_text(strip=True)
        # Комнаты
        rooms_match = re.search(r'(\d+)-комн', params_text)
        if rooms_match:
            rooms = f"{rooms_match.group(1)}-комн."
        # Площадь
        area_match = re.search(r'([\d.,]+)\s*м²', params_text)
        if area_match:
            area = f"{area_match.group(1)} м²"
        # Этаж
        floor_match = re.search(r'(\d+)/(\d+)\s*эт', params_text)
        if floor_match:
            floor = f"{floor_match.group(1)}/{floor_match.group(2)} эт."

    # Описание
    desc_tag = card.find('div', class_='a-card__description')
    description = desc_tag.get_text(strip=True) if desc_tag else ''

    return {
        'url': url,
        'title': title,
        'price': price,
        'address': address,
        'rooms': rooms or title,
        'area': area,
        'floor': floor,
        'description': description,
    }
except Exception as e:
    logger.error(f"Ошибка парсинга карточки: {e}")
    return None
```

def search_krisha(params: dict, top_n: int = 5) -> list:
“”“Основная функция поиска на Krisha.kz”””
url = build_url(params)

```
try:
    time.sleep(1)  # Задержка чтобы не банили
    response = requests.get(url, headers=HEADERS, timeout=15)
    response.raise_for_status()
except requests.RequestException as e:
    logger.error(f"Ошибка запроса к krisha.kz: {e}")
    return []

soup = BeautifulSoup(response.text, 'html.parser')

# Ищем карточки объявлений
cards = soup.find_all('div', class_='a-card')
if not cards:
    cards = soup.find_all('article', class_=re.compile(r'card'))
if not cards:
    cards = soup.find_all('div', attrs={'data-id': True})

logger.info(f"Найдено карточек: {len(cards)}")

results = []
for card in cards[:20]:  # Берём первые 20 для анализа
    listing = parse_listing(card)
    if listing:
        results.append(listing)

# Фильтруем по ЖК если указан (дополнительная фильтрация)
complex_name = params.get('complex')
if complex_name and results:
    filtered = [r for r in results 
                if complex_name.lower() in r['address'].lower() 
                or complex_name.lower() in r['title'].lower()
                or complex_name.lower() in r['description'].lower()]
    if filtered:
        results = filtered

# Сортируем по цене (от меньшей к большей) если это аренда
# Для продажи тоже по цене
def price_sort_key(r):
    price_str = r['price']
    nums = re.findall(r'\d+', price_str.replace(' ', ''))
    if nums:
        return int(''.join(nums[:2]))  # Берём первые цифры
    return 999_999_999

results.sort(key=price_sort_key)

return results[:top_n]
```
