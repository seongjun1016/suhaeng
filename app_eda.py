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

        # 데이터셋 소개
        st.markdown("""
        **Population Trends 데이터셋**  
        - 파일: `population_trends.csv`  
        - 설명: 한국의 전국·광역시·도별 연도별 인구수, 출생자수, 사망자수를 포함한 시계열 데이터
        - 주요 컬럼:
          - `연도` (Year)
          - `지역` (Region)
          - `인구` (Population)
          - `출생아수(명)` (Births)
          - `사망자수(명)` (Deaths)
        """)

        # 앱 기능 안내
        with st.expander("🛠️ 앱 기능 안내"):
            st.markdown("""
            1. **기본 전처리 & 구조·통계**
               - CSV 업로드 후 결측치 처리, `info` 및 `describe` 확인
            2. **연도별 추이**
               - 전국 인구 변화 시각화 및 2035년 예측
            3. **지역별 분석**
               - 최근 5년 각 지역 인구 증감량 및 증감률 순위 차트
            4. **변화량 분석**
               - 연도별 인구 변화 상위 100개 케이스 테이블 표시
            5. **시각화**
               - 지역별 누적 영역 그래프
            """)

        st.markdown("Streamlit 앱 상단 메뉴에서 'EDA' 탭으로 이동하여, 분석을 시작하세요.")


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

        df = pd.read_csv(uploaded)
        tabs = st.tabs([
            "1. 기본 전처리 & 구조·통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # Tab 1
        with tabs[0]:
            st.header("🛠 기본 전처리 & 데이터 구조·기초 통계")
            mask_sejong = df['지역'] == '세종'
            df.loc[mask_sejong] = df.loc[mask_sejong].replace('-', 0)
            num_cols = ['인구', '출생아수(명)', '사망자수(명)']
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.subheader("데이터 구조 (`df.info()`)")
            st.text(buffer.getvalue())
            st.subheader("기초 통계량 (`df.describe()`)")
            st.dataframe(df.describe())

        # Tab 2
        with tabs[1]:
            st.header("Yearly Total Population Trends")
            df_national = df[df['지역'] == '전국'].copy().sort_values('연도')
            recent3 = df_national[['연도', '출생아수(명)', '사망자수(명)']].tail(3)
            avg_net_change = (recent3['출생아수(명)'] - recent3['사망자수(명)']).mean()
            last_year = int(df_national['연도'].max())
            last_pop = int(df_national.loc[df_national['연도'] == last_year, '인구'].iloc[0])
            future_years = list(range(last_year + 1, 2036))
            future_pops = [last_pop + avg_net_change * (yr - last_year) for yr in future_years]
            fig, ax = plt.subplots()
            ax.plot(df_national['연도'], df_national['인구'], 'o-', label='Actual')
            ax.plot(future_years, future_pops, 'x--', label='Forecast')
            ax.set_title("Population Trends by Year and Forecast")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

        # Tab 3
        with tabs[2]:
            st.header("Regional Population Change Ranking")
            eng_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi-do', '강원': 'Gangwon-do', '충북': 'Chungbuk',
                '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
                '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            df_reg = df[df['지역'] != '전국'].copy()
            years = sorted(df_reg['연도'].unique())
            if len(years) < 5:
                st.warning("Insufficient data for 5-year comparison.")
            else:
                start_year, end_year = years[-5], years[-1]
                df_sum = df_reg.groupby(['지역','연도'], as_index=False)['인구'].sum()
                pop_start = df_sum[df_sum['연도']==start_year].set_index('지역')['인구']
                pop_end   = df_sum[df_sum['연도']==end_year].set_index('지역')['인구']
                change      = pop_end - pop_start
                change_k    = change / 1000
                change_rate = (change / pop_start) * 100
                change_k    = change_k.rename(index=eng_map)
                change_rate = change_rate.rename(index=eng_map)
                order       = change_k.sort_values(ascending=False).index
                change_k    = change_k.loc[order]
                change_rate = change_rate.loc[order]
                fig1, ax1 = plt.subplots(figsize=(8,5))
                sns.barplot(x=change_k.values, y=change_k.index, ax=ax1, palette='tab20')
                ax1.set_title("Population Change (Last 5 Years)")
                ax1.set_xlabel("Change (thousands)")
                for i, v in enumerate(change_k.values):
                    xloc = v + (0.5 if v>=0 else -0.5)
                    ax1.text(xloc, i, f"{v:.1f}", va='center')
                fig1.tight_layout()
                st.pyplot(fig1)
                fig2, ax2 = plt.subplots(figsize=(8,5))
                sns.barplot(x=change_rate.values, y=change_rate.index, ax=ax2, palette='tab20')
                ax2.set_title("Population Change Rate (Last 5 Years)")
                ax2.set_xlabel("Change Rate (%)")
                for i, v in enumerate(change_rate.values):
                    xloc = v + (0.5 if v>=0 else -0.5)
                    ax2.text(xloc, i, f"{v:.1f}%", va='center')
                fig2.tight_layout()
                st.pyplot(fig2)
                st.markdown(
                    "> **설명:**\n"
                    "- 첫 번째 차트는 최근 5년간 인구 증감 규모(천 단위)를 내림차순으로 보여줍니다.\n"
                    "- 두 번째 차트는 같은 기간 대비 증감률(%)을 보여줍니다.\n"
                    "- 지역명은 영어로 표기했습니다."
                )

        # Tab 4
        with tabs[3]:
            st.header("📋 Top 100 Yearly Population Changes")
            df_reg2 = df[df['지역'] != '전국'] \
                .sort_values(['지역', '연도']) \
                .reset_index(drop=True)
            df_reg2['diff'] = df_reg2.groupby('지역')['인구'].diff()
            df_diff = df_reg2.dropna(subset=['diff']).copy()
            df_diff['abs_diff'] = df_diff['diff'].abs()
            top100 = df_diff.nlargest(100, 'abs_diff').copy()
            top100['인구'] = top100['인구'].apply(lambda x: f"{int(x):,}")
            top100['diff'] = top100['diff'].apply(lambda x: f"{int(x):,}")
            display_df = top100[['지역','연도','인구','diff']].rename(columns={
                '지역':'Region','연도':'Year','인구':'Population','diff':'Change'
            })
            def highlight_change(val):
                return 'background-color:#ffcccc' if isinstance(val,str) and val.startswith('-') else 'background-color:#cce5ff'
            styled = display_df.style.applymap(highlight_change, subset=['Change'])
            st.dataframe(styled, use_container_width=True)

        # Tab 5
        with tabs[4]:
            st.header("Population Trends by Region (Stacked Area Chart)")
            df_reg3 = df[df['지역']!='전국'].copy()
            df_reg3['Region'] = df_reg3['지역'].map(eng_map)
            df_reg3['Year'] = df_reg3['연도']
            pivot = (
                df_reg3
                .groupby(['Region','Year'], as_index=False)['인구']
                .sum()
                .pivot(index='Region', columns='Year', values='인구')
                .fillna(0)
            )
            fig3, ax3 = plt.subplots(figsize=(12,6))
            pivot.T.plot.area(ax=ax3, cmap='tab20')
            ax3.set_title("Population by Region and Year")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population")
            ax3.legend(title="Region", bbox_to_anchor=(1.02,1), loc='upper left')
            ax3.grid(True)
            st.pyplot(fig3)
            

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