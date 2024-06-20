import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import re
import time
import os

# Function to fetch page
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

# Function to extract best result links
def extract_best_result_links(html, target_name, max_results=3):
    soup = BeautifulSoup(html, 'html.parser')
    results = soup.find_all('div', class_='titles')

    if not results:
        return []

    # Clean the target name
    target_name_clean = target_name.strip().replace(" ", "")
    extracted_links = []

    for result in results:
        title_tag = result.find('h4')
        if title_tag:
            title = title_tag.get_text(strip=True).replace(" ", "")
            link_tag = result.find('a', href=True)
            if title == target_name_clean and link_tag:
                extracted_links.append((link_tag['href'], title_tag.get_text(strip=True)))
                if len(extracted_links) >= max_results:
                    return extracted_links

    # If exact match not found, check for '(주)' prefix
    for result in results:
        title_tag = result.find('h4')
        if title_tag:
            title = title_tag.get_text(strip=True).replace(" ", "")
            link_tag = result.find('a', href=True)
            if title == f"(주){target_name_clean}" and link_tag:
                extracted_links.append((link_tag['href'], title_tag.get_text(strip=True)))
                if len(extracted_links) >= max_results:
                    return extracted_links

    return extracted_links

# Function to fetch article
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

# Function to extract table data
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

# Function to fetch and process data by phone number with retry mechanism
def fetch_and_process_data(phone_number, max_retries=5, initial_delay=2):
    url = f"https://map.naver.com/p/api/search/allSearch?query={phone_number}&type=all&searchCoord=126.85150490000274%3B37.553927499999716&boundary="

    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.6,en;q=0.4',
        'Cache-Control': 'no-cache',
        'Cookie': 'NNB=NPJOP2RQ4OAGK; NAC=AiscBMAJe939B; NACT=1; MM_PF=SEARCH; page_uid=iFaK2lqo1iCssmU/5+ossssst9V-397270; BUC=htSJvvHt8R3cQ7t_28Ox4DHSvcweJp-3iPnVEMLw0rQ=',
        'Pragma': 'no-cache',
        'Referer': f'https://map.naver.com/p/search/{phone_number}/place/1872692696?c=15.00,0,0,0,dh&placePath=%3Fentry%253Dbmp',
        'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }

    delay = initial_delay
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            try:
                data = response.json()
            except json.JSONDecodeError:
                st.error(f"JSON 디코딩에 실패했습니다: {response.text}")
                return [{
                    'searchedPhoneNumber': phone_number,
                    'name': '검색결과없음',
                    'tel': '검색결과없음',
                    'category': '검색결과없음',
                    'roadAddress': '검색결과없음'
                }]

            place_data = data.get('result', {}).get('place')
            
            if not place_data or not place_data.get('list'):
                return [{
                    'searchedPhoneNumber': phone_number,
                    'name': '검색결과없음',
                    'tel': '검색결과없음',
                    'category': '검색결과없음',
                    'roadAddress': '검색결과없음'
                }]

            place_list = place_data.get('list', [])

            extracted_data = []
            for place in place_list:
                name = place.get('name', '')
                tel = place.get('tel', '')
                category = ', '.join(place.get('category', []))
                road_address = place.get('roadAddress', '')
                extracted_data.append({
                    'searchedPhoneNumber': phone_number,
                    'name': name,
                    'tel': tel,
                    'category': category,
                    'roadAddress': road_address
                })

            return extracted_data
        else:
            print(f"요청 실패. 상태 코드: {response.status_code}. {attempt + 1}/{max_retries} 시도 후 {delay}초 대기 중...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

    st.error(f"{max_retries}번의 시도 후에도 요청이 실패했습니다.")
    return [{
        'searchedPhoneNumber': phone_number,
        'name': '검색결과없음',
        'tel': '검색결과없음',
        'category': '검색결과없음',
        'roadAddress': '검색결과없음'
    }]

# Function to clean name
def clean_name(name):
    name = re.sub(r'\d+', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = name.strip()
    return name

# Main function
def main():
    st.title("전화번호 검색 결과")

    input_method = st.radio("입력 방식을 선택하세요", ('직접 입력', '파일 업로드'))

    phone_numbers = []
    file_name = ""
    
    if input_method == '직접 입력':
        phone_number = st.text_input("검색할 전화번호를 입력하세요")
        if phone_number:
            phone_numbers.append(phone_number)
        file_name = st.text_input("저장할 파일명을 입력하세요")

    elif input_method == '파일 업로드':
        uploaded_file = st.file_uploader("전화번호 리스트가 있는 파일을 업로드하세요", type="txt")
        if uploaded_file is not None:
            phone_numbers = uploaded_file.read().decode('utf-8').splitlines()
            file_name = os.path.splitext(uploaded_file.name)[0]  # Extract the file name without extension

    if phone_numbers and file_name:
        all_extracted_data = []
        for phone_number in phone_numbers:
            extracted_data = fetch_and_process_data(phone_number)
            all_extracted_data.extend(extracted_data)

        if all_extracted_data:
            df = pd.DataFrame(all_extracted_data)
            st.dataframe(df)

            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="CSV 파일 다운로드", data=csv, file_name=f'{file_name}_extracted_data.csv', mime='text/csv')

            df['clean_name'] = df['name'].apply(clean_name)
            df['base_name'] = df['clean_name'].apply(lambda x: x.split()[0] if x else x)
            grouped = df.groupby('searchedPhoneNumber')['base_name'].agg(lambda x: x.value_counts().idxmax()).reset_index()
            grouped.columns = ['searchedPhoneNumber', 'name']

            st.write("정제된 데이터셋")
            st.dataframe(grouped)
            refined_csv = grouped.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="정제된 CSV 파일 다운로드", data=refined_csv, file_name=f'{file_name}_refined_data.csv', mime='text/csv')

            # Using the refined names to fetch business registration details
            business_data = []
            for _, row in grouped.iterrows():
                business_name = row['name']
                if business_name == "검색결과없음":
                    business_data.append({'SearchedPhoneNumber': row['searchedPhoneNumber'], 'name': '검색결과없음', 'h4텍스트': '', '사업자등록번호': '', '회사명(영문)': '', '업태': '', '종목': '', '주요제품': '', '전화번호': '', '팩스번호': '', '기업규모': '', '법인구분': '', '본사/지사': '', '법인형태': '', '설립일': '', '홈페이지': '', '대표자명': '', '법인등록번호': '', '회사주소': ''})
                else:
                    result = fetch_page(business_name)
                    if result:
                        best_links = extract_best_result_links(result, business_name, max_results=3)
                        for link, h4_text in best_links:
                            article_html = fetch_article(link)
                            if article_html:
                                extracted_data = extract_table_data(article_html)
                                if extracted_data:
                                    extracted_data['SearchedPhoneNumber'] = row['searchedPhoneNumber']
                                    extracted_data['name'] = business_name
                                    extracted_data['h4텍스트'] = h4_text
                                    business_data.append(extracted_data)
                        if not best_links:
                            business_data.append({'SearchedPhoneNumber': row['searchedPhoneNumber'], 'name': '검색결과없음', 'h4텍스트': '', '사업자등록번호': '', '회사명(영문)': '', '업태': '', '종목': '', '주요제품': '', '전화번호': '', '팩스번호': '', '기업규모': '', '법인구분': '', '본사/지사': '', '법인형태': '', '설립일': '', '홈페이지': '', '대표자명': '', '법인등록번호': '', '회사주소': ''})

            if business_data:
                business_df = pd.DataFrame(business_data)
                columns = ['SearchedPhoneNumber', 'name', 'h4텍스트', '사업자등록번호'] + [col for col in business_df.columns if col not in ['SearchedPhoneNumber', 'name', 'h4텍스트', '사업자등록번호']]
                business_df = business_df[columns]

                st.write("사업자 등록 정보 데이터셋")
                st.dataframe(business_df)
                business_csv = business_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(label="사업자 등록 정보 CSV 다운로드", data=business_csv, file_name=f'{file_name}_business_data.csv', mime='text/csv')
            else:
                st.info("사업자 등록 정보가 없습니다.")
        else:
            st.info("추출된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
