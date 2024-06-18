import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re
from sentence_transformers import SentenceTransformer

# 문장 임베딩 모델 로드
model = SentenceTransformer('all-MiniLM-L6-v2')

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
        st.success("페이지 요청 성공")
        return response.text
    else:
        st.error(f"페이지 요청 실패. 상태 코드: {response.status_code}")
        return None

def extract_best_result_link(html, target_name):
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('div', class_='single-post')

    if not results:
        return None
    
    # 문장 임베딩 생성
    target_embedding = model.encode([target_name])[0]
    
    best_match = None
    highest_similarity = -1.0
    
    for result in results:
        title_tag = result.find('div', class_='titles')
        if title_tag:
            title = title_tag.get_text(strip=True)
            title_embedding = model.encode([title])[0]
            similarity = float(title_embedding.dot(target_embedding) / (title_embedding.norm() * target_embedding.norm()))
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
        st.success("기사 페이지 요청 성공")
        return response.text
    else:
        st.error(f"기사 페이지 요청 실패. 상태 코드: {response.status_code}")
        return None


def extract_table_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table', class_='table_guide01')
    
    if not table:
        st.error("테이블을 찾을 수 없습니다.")
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


def fetch_and_process_data(phone_numbers):
    processed_data = []
    for phone_number in phone_numbers:
        url = f"https://map.naver.com/p/api/search/allSearch?query={phone_number}&type=all&searchCoord=126.85150490000274%3B37.553927499999716&boundary="
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            place_data = data.get('result', {}).get('place', {}).get('list', [])
            for place in place_data:
                name = place.get('name', '')
                road_address = place.get('roadAddress', '')
                extracted_data = {
                    'name': name,
                    'roadAddress': road_address
                }
                processed_data.append(extracted_data)

    return processed_data


def clean_name(name):
    name = re.sub(r'\d+', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = name.strip()
    return name

def main():
    st.title("전화번호 검색 결과")

    input_method = st.radio("입력 방식을 선택하세요", ('직접 입력', '파일 업로드'))

    phone_numbers = []
    
    if input_method == '직접 입력':
        phone_number = st.text_input("검색할 전화번호를 입력하세요")
        if phone_number:
            phone_numbers.append(phone_number)

    elif input_method == '파일 업로드':
        uploaded_file = st.file_uploader("전화번호 리스트가 있는 파일을 업로드하세요", type="txt")

    if uploaded_file is not None:
        phone_numbers = uploaded_file.read().decode('utf-8').splitlines()
    
    if phone_numbers:
        processed_data = fetch_and_process_data(phone_numbers)
    
        if processed_data:
            df = pd.DataFrame(processed_data)
            st.dataframe(df)

            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="CSV 파일 다운로드", data=csv, file_name='extracted_data.csv', mime='text/csv')
    
            df['clean_name'] = df['name'].apply(clean_name)
            df['base_name'] = df['clean_name'].apply(lambda x: x.split()[0] if x else x)
            grouped = df.groupby('roadAddress')['base_name'].agg(lambda x: x.value_counts().idxmax()).reset_index()
            grouped.columns = ['roadAddress', 'name']

            st.write("정제된 데이터셋")
            st.dataframe(grouped)
            refined_csv = grouped.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="정제된 CSV 파일 다운로드", data=refined_csv, file_name='refined_data.csv', mime='text/csv')

        # Using the refined names to fetch business registration details
            business_data = []
            for _, row in grouped.iterrows():
                business_name = row['name']
                if business_name == "검색결과없음":
                    business_data.append({'name': '검색결과없음', '사업자등록번호': '', '회사명(영문)': '', '업태': '', '종목': '', '주요제품': '', '전화번호': '', '팩스번호': '', '기업규모': '', '법인구분': '', '본사/지사': '', '법인형태': '', '설립일': '', '홈페이지': '', '대표자명': '', '법인등록번호': '', '회사주소': ''})
                else:
                    result = fetch_page(business_name)
                    if result:
                        best_link = extract_best_result_link(result, business_name)
                        if best_link:
                            article_html = fetch_article(best_link)
                            if article_html:
                                extracted_data = extract_table_data(article_html)
                                if extracted_data:
                                    extracted_data['name'] = business_name
                                    business_data.append(extracted_data)

            if business_data:
                business_df = pd.DataFrame(business_data)
                columns = ['name', '사업자등록번호'] + [col for col in business_df.columns if col not in ['name', '사업자등록번호']]
                business_df = business_df[columns]

                st.write("사업자 등록 정보 데이터셋")
                st.dataframe(business_df)
                business_csv = business_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(label="사업자 등록 정보 CSV 다운로드", data=business_csv, file_name='business_data.csv', mime='text/csv')
            else:
                st.info("사업자 등록 정보가 없습니다.")
        else:
            st.info("추출된 데이터가 없습니다.")

    if __name__ == "__main__":
        main()
