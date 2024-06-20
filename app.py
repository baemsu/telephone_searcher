import requests
import pandas as pd
import streamlit as st
import re
import time
import os

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

if __name__ == "__main__":
    main()
