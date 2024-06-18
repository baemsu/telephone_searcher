import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import pandas as pd
import difflib

def fetch_page(query):
    base_url = "https://bizno.net/?area=&query="
    encoded_query = quote(query)
    full_url = base_url + encoded_query

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Upgrade-Insecure-Requests': '1',
        'Referer': full_url,
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1'
    }

    response = requests.get(full_url, headers=headers)

    if response.status_code == 200:
        print("페이지 요청 성공")
        return response.text
    else:
        print(f"페이지 요청 실패. 상태 코드: {response.status_code}")
        return None

def extract_first_result_link(html, target_name):
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('div', class_='single-post')

    if not results:
        return None

    best_match = None
    highest_similarity = 0.0

    for result in results:
        title_tag = result.find('div', class_='titles')
        if title_tag:
            title = title_tag.get_text(strip=True)
            similarity = difflib.SequenceMatcher(None, title, target_name).ratio()
            if similarity > highest_similarity:
                highest_similarity = similarity
                link_tag = result.find('a', href=True)
                if link_tag:
                    best_match = link_tag['href']

    return best_match

def fetch_article(link):
    base_url = "https://bizno.net"
    full_url = base_url + link

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Upgrade-Insecure-Requests': '1',
        'Referer': full_url,
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }

    response = requests.get(full_url, headers=headers)

    if response.status_code == 200:
        print("기사 페이지 요청 성공")
        return response.text
    else:
        print(f"기사 페이지 요청 실패. 상태 코드: {response.status_code}")
        return None

def extract_table_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='table_guide01')
    
    if not table:
        print("테이블을 찾을 수 없습니다.")
        return None

    data = {}
    for row in table.find_all('tr'):
        cols = row.find_all(['th', 'td'])
        if len(cols) == 2:
            header = cols[0].text.strip()
            value = cols[1].text.strip()
            data[header] = value

    columns = ["회사명(영문)", "업태", "종목", "주요제품", "전화번호", "팩스번호", "기업규모", "법인구분", "본사/지사", "법인형태", "설립일", "홈페이지", "대표자명", "사업자등록번호", "법인등록번호", "회사주소"]
    extracted_data = {col: data.get(col, '') for col in columns}
    
    return extracted_data

def main():
    query = input("검색어를 입력하세요: ")
    result = fetch_page(query)
    if result:
        with open("result.html", "w", encoding="utf-8") as file:
            file.write(result)
        print("결과가 result.html 파일에 저장되었습니다.")
        
        first_link = extract_first_result_link(result, query)
        if first_link:
            print(f"첫 번째 링크: {first_link}")
            article_html = fetch_article(first_link)
            if article_html:
                with open("article.html", "w", encoding="utf-8") as file:
                    file.write(article_html)
                print("기사 내용이 article.html 파일에 저장되었습니다.")
                
                extracted_data = extract_table_data(article_html)
                if extracted_data:
                    df = pd.DataFrame([extracted_data])
                    df.to_csv("extracted_data.csv", index=False, encoding='utf-8-sig')
                    print("추출된 데이터가 extracted_data.csv 파일에 저장되었습니다.")
                else:
                    print("추출된 데이터가 없습니다.")
        else:
            print("첫 번째 링크를 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
