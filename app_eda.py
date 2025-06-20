import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population Trends EDA")
        uploaded = st.file_uploader("population_trends.csv 파일 업로드", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        # 데이터 로드
        df = pd.read_csv(uploaded)

        # 탭 정의
        tabs = st.tabs([
            "1. 기본 전처리 & 구조·통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # --- Tab 1: 기본 전처리 & 데이터 구조/통계 ---
        with tabs[0]:
            st.header("🛠 기본 전처리 & 데이터 구조·기초 통계")

            # '세종'지역의 결측치 '-' → 0 치환
            mask_sejong = df['지역'] == '세종'
            df.loc[mask_sejong] = df.loc[mask_sejong].replace('-', 0)

            # 주요 열을 숫자형으로 변환
            num_cols = ['인구', '출생아수(명)', '사망자수(명)']
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

            # 데이터 구조 출력
            st.subheader("데이터 구조 (`df.info()`)")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())

            # 기초 통계량 출력
            st.subheader("기초 통계량 (`df.describe()`)")
            st.dataframe(df.describe())

        # --- Tab 2: 연도별 전체 인구 추이 & 2035년 예측 ---
        with tabs[1]:
            st.header("Yearly Total Population Trends")

            # 전국 필터링 및 정렬
            df_national = df[df['지역'] == '전국'].copy().sort_values('연도')

            # 최근 3년 평균 순증가분
            recent3 = df_national[['연도', '출생아수(명)', '사망자수(명)']].tail(3)
            avg_net_change = (recent3['출생아수(명)'] - recent3['사망자수(명)']).mean()

            # 2035년 예측치 생성
            last_year = int(df_national['연도'].max())
            last_pop = int(df_national.loc[df_national['연도'] == last_year, '인구'].iloc[0])
            future_years = list(range(last_year + 1, 2036))
            future_pops = [last_pop + avg_net_change * (yr - last_year) for yr in future_years]

            # 그래프 그리기
            fig, ax = plt.subplots()
            ax.plot(df_national['연도'], df_national['인구'], marker='o', linestyle='-', label='Actual')
            ax.plot(future_years, future_pops, marker='x', linestyle='--', label='Forecast (to 2035)')
            ax.set_title("Population Trends by Year and Forecast")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

        # --- Tab 3: 지역별 인구 변화량 순위 분석 ---
        with tabs[2]:
            st.header("Regional Population Change Ranking")

            # 한영 지역명 매핑
            eng_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기도': 'Gyeonggi-do', '강원도': 'Gangwon-do', '충청북도': 'Chungbuk',
                '충청남도': 'Chungnam', '전라북도': 'Jeonbuk', '전라남도': 'Jeonnam',
                '경상북도': 'Gyeongbuk', '경상남도': 'Gyeongnam', '제주특별자치도': 'Jeju'
            }

            # 전국 제외, 최근 5년 데이터
            df_reg = df[df['지역'] != '전국'].copy()
            years = sorted(df_reg['연도'].unique())
            last5 = years[-5:]
            df_last5 = df_reg[df_reg['연도'].isin(last5)]

            # 피벗 테이블
            pivot = df_last5.pivot(index='지역', columns='연도', values='인구').dropna()
            pivot.index = pivot.index.map(eng_map)

            # 절대 증감량
            change = pivot[last5[-1]] - pivot[last5[0]]
            change_sorted = change.sort_values(ascending=False)

            # 수평 막대그래프 (절대 증감량)
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            sns.barplot(x=change_sorted.values / 1000, y=change_sorted.index, ax=ax1)
            for i, v in enumerate(change_sorted.values / 1000):
                ax1.text(v, i, f"{v:.1f}", va='center')
            ax1.set_title("Population Change (Last 5 Years)")
            ax1.set_xlabel("Change (thousands)")
            fig1.tight_layout()
            st.pyplot(fig1)

            # 증감률
            rate = (change / pivot[last5[0]] * 100).loc[change_sorted.index]
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.barplot(x=rate.values, y=rate.index, ax=ax2)
            for i, v in enumerate(rate.values):
                ax2.text(v, i, f"{v:.1f}%", va='center')
            ax2.set_title("Population Change Rate (Last 5 Years)")
            ax2.set_xlabel("Change Rate (%)")
            fig2.tight_layout()
            st.pyplot(fig2)

            st.markdown(
                "> **해설:**\n"
                "- 첫 번째 그래프는 최근 5년간 각 지역별 인구 증감 규모를 천 단위로 보여줍니다.\n"
                "- 두 번째 그래프는 증감률(%)을 보여주어, 상대적 변화를 파악할 수 있습니다."
            )

        # --- Tab 4: Top 100 Yearly Population Changes ---
        with tabs[3]:
            st.header("📋 Top 100 Yearly Population Changes")

            df_reg = df[df['지역'] != '전국'] \
                .sort_values(['지역', '연도']) \
                .reset_index(drop=True)
            df_reg['diff'] = df_reg.groupby('지역')['인구'].diff()

            df_diff = df_reg.dropna(subset=['diff']).copy()
            df_diff['abs_diff'] = df_diff['diff'].abs()
            top100 = df_diff.nlargest(100, 'abs_diff').copy()

            # 포맷팅
            top100['인구'] = top100['인구'].apply(lambda x: f"{int(x):,}")
            top100['diff'] = top100['diff'].apply(lambda x: f"{int(x):,}")

            display_df = top100[['지역', '연도', '인구', 'diff']].rename(columns={
                '지역': 'Region', '연도': 'Year', '인구': 'Population', 'diff': 'Change'
            })

            def highlight_change(val):
                if isinstance(val, str) and val.startswith('-'):
                    return 'background-color: #ffcccc'
                else:
                    return 'background-color: #cce5ff'

            styled = display_df.style.applymap(highlight_change, subset=['Change'])
            st.dataframe(styled, use_container_width=True)

        # --- Tab 5: Stacked Area Chart of Population by Region & Year ---
        with tabs[4]:
            st.header("Population Trends by Region (Stacked Area Chart)")

            df_reg = df[df['지역'] != '전국'].copy()
            df_reg['Region'] = df_reg['지역'].map(eng_map)
            df_reg['Year'] = df_reg['연도']

            # 중복 제거 후 집계
            pivot = (
                df_reg
                .groupby(['Region', 'Year'], as_index=False)['인구']
                .sum()
                .pivot(index='Region', columns='Year', values='인구')
                .fillna(0)
            )

            fig, ax = plt.subplots(figsize=(12, 6))
            pivot.T.plot.area(ax=ax, cmap='tab20')
            ax.set_title("Population by Region and Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(title="Region", bbox_to_anchor=(1.02, 1), loc='upper left')
            ax.grid(True)

            st.pyplot(fig)

            
# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()