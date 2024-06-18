import requests
import json
import pandas as pd
import streamlit as st
import re

def fetch_and_process_data(phone_number):
    # 요청 URL
    url = f"https://map.naver.com/p/api/search/allSearch?query={phone_number}&type=all&searchCoord=126.85150490000274%3B37.553927499999716&boundary="

    # GET 요청 보내기
    response = requests.get(url)

    # 응답이 성공적인지 확인
    if response.status_code == 200:
        # JSON 데이터로 변환
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

        # place 데이터가 존재하는지 확인
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

        # 필요한 정보 추출
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
        st.error(f"요청 실패. 상태 코드: {response.status_code}")
        return [{
            'searchedPhoneNumber': phone_number,
            'name': '검색결과없음',
            'tel': '검색결과없음',
            'category': '검색결과없음',
            'roadAddress': '검색결과없음'
        }]

def clean_name(name):
    # 상호명에서 불필요한 숫자와 문자를 제거하여 정제
    name = re.sub(r'\d+', '', name)  # 숫자 제거
    name = re.sub(r'\(.*?\)', '', name)  # 괄호 내용 제거
    name = name.strip()  # 양쪽 공백 제거
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
        all_extracted_data = []
        for phone_number in phone_numbers:
            extracted_data = fetch_and_process_data(phone_number)
            all_extracted_data.extend(extracted_data)

        if all_extracted_data:
            df = pd.DataFrame(all_extracted_data)
            st.dataframe(df)

            # CSV 파일로 저장
            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="CSV 파일 다운로드", data=csv, file_name='extracted_data.csv', mime='text/csv')

            # 상호명을 정제하고 중복된 상호명을 찾는 과정
            df['clean_name'] = df['name'].apply(clean_name)
            # 'clean_name' 컬럼을 공백으로 분할하여 가장 많이 나타나는 단어를 선택
            df['base_name'] = df['clean_name'].apply(lambda x: x.split()[0] if x else x)
            grouped = df.groupby('searchedPhoneNumber')['base_name'].agg(lambda x: x.value_counts().idxmax()).reset_index()
            grouped.columns = ['searchedPhoneNumber', 'name']

            # 정제된 데이터셋 표시 및 다운로드
            st.write("정제된 데이터셋")
            st.dataframe(grouped)
            refined_csv = grouped.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(label="정제된 CSV 파일 다운로드", data=refined_csv, file_name='refined_data.csv', mime='text/csv')
        else:
            st.info("추출된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
