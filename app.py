import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드 (로컬 환경 대응)
load_dotenv()

# 컬러 팔레트 정의
PRIMARY_BROWN = "#3B2A22"  # Dubai Chocolate Brown
SECONDARY_GREEN = "#6E8F3D" # Pistachio Green
BACKGROUND_CREAM = "#F4EFEA" # Cream Beige
WHITE = "#FFFFFF"
TERTIARY_GOLD = "#C89B5C"   # Caramel Gold

# 페이지 설정
st.set_page_config(page_title="네이버 키워드 데이터 분석 대시보드", layout="wide")

st.markdown(f"""
<style>
    /* 메인 배경색 */
    .stApp {{
        background-color: {BACKGROUND_CREAM};
    }}
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {{
        background-color: {PRIMARY_BROWN};
        color: {BACKGROUND_CREAM};
    }}
    [data-testid="stSidebar"] .stMarkdown h1, 
    [data-testid="stSidebar"] .stMarkdown h2, 
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] label {{
        color: {BACKGROUND_CREAM} !important;
    }}
    
    /* 메트릭 카드 스타일 */
    .stMetric {{
        background-color: {WHITE};
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid {SECONDARY_GREEN};
    }}
    
    /* 헤더 텍스트 색상 */
    h1, h2, h3 {{
        color: {PRIMARY_BROWN} !important;
    }}
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: {WHITE};
        border-radius: 5px 5px 0px 0px;
        color: {PRIMARY_BROWN};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {SECONDARY_GREEN} !important;
        color: {WHITE} !important;
    }}
</style>
""", unsafe_allow_html=True)

# API 자격 증명 로드 함수
def get_naver_credentials():
    # 1. Streamlit Secrets (배포용) 확인
    if "NAVER_CLIENT_ID" in st.secrets:
        return st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"]
    
    # 2. 환경 변수/dotenv (로컬용) 확인
    client_id = os.getenv("NAVER_CLIENT_ID")
    client_secret = os.getenv("NAVER_CLIENT_SECRET")
    
    return client_id, client_secret

CLIENT_ID, CLIENT_SECRET = get_naver_credentials()

def get_headers():
    return {
        "X-Naver-Client-Id": CLIENT_ID,
        "X-Naver-Client-Secret": CLIENT_SECRET,
        "Content-Type": "application/json"
    }

# --- 데이터 수집 함수 ---

@st.cache_data(show_spinner="쇼핑 트렌드 데이터를 불러오는 중...")
def fetch_datalab_trend(keywords, start_date="2025-01-01", end_date=datetime.now().strftime("%Y-%m-%d")):
    if not CLIENT_ID or not CLIENT_SECRET: return pd.DataFrame()
    
    url = "https://openapi.naver.com/v1/datalab/search"
    data = {
        "startDate": start_date,
        "endDate": end_date,
        "timeUnit": "date",
        "keywordGroups": [{"groupName": kw, "keywords": [kw]} for kw in keywords]
    }
    
    try:
        response = requests.post(url, headers=get_headers(), data=json.dumps(data))
        if response.status_code == 200:
            res_json = response.json()
            results = []
            for group in res_json['results']:
                group_name = group['title']
                for entry in group['data']:
                    results.append({"period": entry['period'], "ratio": entry['ratio'], "keyword": group_name})
            return pd.DataFrame(results)
        else:
            st.warning(f"⚠️ 트렌드 데이터 수집 실패: HTTP {response.status_code} - {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ 트렌드 API 연결 오류: {str(e)}")
    except Exception as e:
        st.error(f"❌ 트렌드 데이터 처리 오류: {str(e)}")
    return pd.DataFrame()

@st.cache_data(show_spinner="검색 결과 데이터를 수집하는 중...")
def fetch_search_results(api_type, keywords, max_count=1000):
    if not CLIENT_ID or not CLIENT_SECRET: return pd.DataFrame(), {}
    
    base_url = f"https://openapi.naver.com/v1/search/{api_type}.json"
    all_results = []
    total_counts = {}
    
    for kw in keywords:
        total_counts[kw] = 0 # 초기화
        for start in range(1, max_count, 100):
            params = {"query": kw, "display": 100, "start": start, "sort": "sim"}
            try:
                response = requests.get(base_url, headers=get_headers(), params=params)
                if response.status_code == 200:
                    data = response.json()
                    if start == 1:
                        total_counts[kw] = data.get('total', 0)

                    items = data.get('items', [])
                    if not items: break
                    for item in items:
                        item['keyword'] = kw
                        all_results.append(item)
                    time.sleep(0.1)
                else:
                    if start == 1:  # 첫 요청 실패시에만 에러 표시
                        st.warning(f"⚠️ '{kw}' {api_type} 검색 실패: HTTP {response.status_code}")
                    break
            except requests.exceptions.RequestException as e:
                if start == 1:  # 첫 요청 실패시에만 에러 표시
                    st.error(f"❌ '{kw}' {api_type} API 연결 오류: {str(e)}")
                break
            except Exception as e:
                if start == 1:  # 첫 요청 실패시에만 에러 표시
                    st.error(f"❌ '{kw}' {api_type} 데이터 처리 오류: {str(e)}")
                break
    return pd.DataFrame(all_results), total_counts

# --- 메인 UI 구성 ---

st.markdown("<h1 style='text-align: center;'>네이버 키워드 데이터 분석 대시보드 🧆</h1>", unsafe_allow_html=True)

if not CLIENT_ID or not CLIENT_SECRET:
    st.error("⚠️ 네이버 API 인증 정보(Client ID 또는 Secret)가 설정되지 않았습니다. 사이드바의 안내 또는 가이드 문서를 확인해 주세요.")
    st.info("로컬: .env 파일 / 배포: Streamlit Cloud Secrets 설정 필요")

# 사이드바 구성
st.sidebar.title("🔍 분석 옵션")
input_keywords = st.sidebar.text_input(
    "분석할 키워드를 입력하세요 (쉼표로 구분)",
    value="카다이프, 피스타치오, 마시멜로우"
)
selected_keywords = [k.strip() for k in input_keywords.split(",") if k.strip()]

run_analysis = st.sidebar.button("⚡ 실시간 분석 실행", type="primary")

# 키워드별 고정 컬러 맵 생성 (일관성 유지)
color_palette = [PRIMARY_BROWN, SECONDARY_GREEN, TERTIARY_GOLD]
keyword_color_map = {kw: color_palette[i % len(color_palette)] for i, kw in enumerate(selected_keywords)}

# 데이터 변수 초기화 (초기 로딩 시 NameError 방지)
filtered_trend = pd.DataFrame()
filtered_blog = pd.DataFrame()
filtered_shop = pd.DataFrame()

# 데이터 로드 로직
if run_analysis or 'data_loaded' in st.session_state:
    st.session_state.data_loaded = True
    
    with st.status("데이터를 실시간으로 수집하고 있습니다...", expanded=True) as status:
        st.write("1. 쇼핑 트렌드 수집 중...")
        df_trend = fetch_datalab_trend(selected_keywords)
        
        st.write("2. 블로그 검색 결과 수집 중 (최대 1,000건)...")
        df_blog, blog_total_counts = fetch_search_results("blog", selected_keywords)
        st.session_state['blog_total_counts'] = blog_total_counts # 총 개수 저장
        
        st.write("3. 쇼핑 검색 결과 수집 중 (최대 1,000건)...")
        df_shop, shop_total_counts = fetch_search_results("shop", selected_keywords)
        
        # 데이터 수집 결과 확인
        has_data = not (df_trend.empty and df_blog.empty and df_shop.empty)
        if has_data:
            status.update(label="✅ 데이터 수집 완료!", state="complete", expanded=False)
        else:
            status.update(label="⚠️ 데이터 수집 실패", state="error", expanded=True)

    if df_trend.empty and df_blog.empty and df_shop.empty:
        st.error("❌ 수집된 데이터가 없습니다. 위의 에러 메시지를 확인하고 API 설정을 점검해 주세요.")
        st.info("💡 확인사항:\n- API Client ID와 Secret이 올바르게 설정되었는지\n- 네이버 개발자 센터에서 해당 API가 활성화되었는지\n- 키워드 입력이 정확한지")
        st.stop()
    
    st.info(f"수집 기준일: {datetime.now().strftime('%Y-%m-%d')} | 분석 키워드: {', '.join(selected_keywords)}")

    # 데이터 필터링 (멀티셀렉트 대신 입력값 유지)
    filtered_trend = df_trend
    filtered_blog = df_blog
    filtered_shop = df_shop

# --- 페이지 본문 제어 ---
if not st.session_state.get('data_loaded', False):
    # 랜딩 페이지 UI
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write("")  # 간격 조절
        img_path = os.path.join(os.path.dirname(__file__), "_cookie.png")
        if os.path.exists(img_path):
            # 이미지 크기 조절을 위한 중첩 컬럼 (이미지 사이즈 축소)
            sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1])
            with sub_c2:
                st.image(img_path, use_container_width=True, caption="Naver Keywords 🍫🥑")
        
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; background-color: {WHITE}; border-radius: 15px; border: 2px solid {SECONDARY_GREEN};">
            <h3 style="color: {PRIMARY_BROWN}; margin-bottom: 10px;">👋 환영합니다!</h3>
            <p style="color: {PRIMARY_BROWN}; font-size: 1.1em;">
                분석을 시작하려면 왼쪽 <b>사이드바</b>에서 키워드를 입력하고<br>
                <span style="color: {SECONDARY_GREEN}; font-weight: bold;">'실시간 분석 실행'</span> 버튼을 눌러주세요.
            </p>
        </div>
        """, unsafe_allow_html=True)
    st.stop()  # 분석 전에는 아래 탭 구성을 숨김

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📉 트렌드 비교", "✍️ 블로그 분석", "🛒 쇼핑 분석", "📊 통합 통계"])

# --- Tab 1: 트렌드 비교 ---
with tab1:
    st.header("1. 검색어 트렌드 시계열 분석")
    
    if not filtered_trend.empty:
        # 그래프 1: 시계열 라인 차트
        fig1 = px.line(filtered_trend, x='period', y='ratio', color='keyword',
                       title="2025년 키워드별 검색 트렌드 (상대적 비중)",
                       labels={'ratio': '검색 비중', 'period': '날짜'},
                       template="plotly_white",
                       color_discrete_map=keyword_color_map)
        fig1.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color=PRIMARY_BROWN
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # 표 1: 일자별 트렌드 요약표
        st.subheader("일자별 트렌드 데이터 요약")
        st.dataframe(filtered_trend.sort_values(by=['period', 'keyword'], ascending=[False, True]).head(20), use_container_width=True)
    else:
        st.write("트렌드 데이터가 없습니다.")

# --- Tab 2: 블로그 분석 ---
with tab2:
    st.header("2. 네이버 블로그 검색 현황")
    
    if not filtered_blog.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # 그래프 2: 키워드별 블로그 포스트 수 (전체 검색 결과 기준)
            # 수집된 데이터(최대 1000개)가 아닌 API Total Count 사용
            if 'blog_total_counts' in st.session_state:
                total_counts_data = [
                    {'keyword': k, 'count': st.session_state['blog_total_counts'].get(k, 0)} 
                    for k in filtered_blog['keyword'].unique()
                ]
                blog_counts = pd.DataFrame(total_counts_data)
            else:
                blog_counts = filtered_blog['keyword'].value_counts().reset_index()
                blog_counts.columns = ['keyword', 'count']

            fig2 = px.bar(blog_counts, x='keyword', y='count', color='keyword',
                          title="키워드별 전체 블로그 포스트 수 (Total Count)",
                          text='count', # 막대 위에 숫자 표시
                          template="plotly_white",
                          color_discrete_map=keyword_color_map)
            fig2.update_traces(texttemplate='%{text:,}', textposition='outside') # 천단위 콤마
            fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=PRIMARY_BROWN)
            st.plotly_chart(fig2, use_container_width=True)
            
        with col2:
            # 데이터 타입 변환 및 2025년 이후 필터링
            if 'postdate' in filtered_blog.columns:
                filtered_blog['postdate_dt'] = pd.to_datetime(filtered_blog['postdate'], format='%Y%m%d', errors='coerce')
                # 2025년 1월 1일 이후 데이터만 필터링
                df_blog_filtered = filtered_blog[filtered_blog['postdate_dt'] >= '2025-01-01'].copy()
                
                if not df_blog_filtered.empty:
                    # 월별로 그룹화 (YYYY-MM 형식)
                    df_blog_filtered['month'] = df_blog_filtered['postdate_dt'].dt.strftime('%Y-%m')
                    blog_time = df_blog_filtered.groupby(['month', 'keyword']).size().reset_index(name='count')
                    blog_time = blog_time.sort_values('month')
                    
                    fig3 = px.bar(blog_time, x='month', y='count', color='keyword', barmode='group',
                                  title="2025년 월별 블로그 게시물 빈도",
                                  labels={'month': '게시월', 'count': '게시물 수'},
                                  template="plotly_white",
                                  color_discrete_map=keyword_color_map)
                    fig3.update_layout(
                        xaxis={'type': 'category', 'categoryorder': 'category ascending'},
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)', 
                        font_color=PRIMARY_BROWN
                    )
                    st.plotly_chart(fig3, use_container_width=True)
                else:
                    st.info("📅 2025년 1월 이후의 게시물 데이터가 없습니다.")

        # 표 2: 관련도순 블로그 리스트
        st.subheader("주요 블로그 게시물 정보")
        display_blog = filtered_blog[['title', 'bloggername', 'postdate', 'link']].copy()
        # HTML 태그 제거 및 링크 처리 생략 (간소화)
        st.dataframe(display_blog.head(500), use_container_width=True)
    else:
        st.write("블로그 데이터가 없습니다.")

# --- Tab 3: 쇼핑 분석 ---
with tab3:
    st.header("3. 네이버 쇼핑 상품 데이터 분석")
    
    if not filtered_shop.empty:
        # 데이터 전처리: 가격 숫자로 변환
        filtered_shop['lprice'] = pd.to_numeric(filtered_shop['lprice'], errors='coerce')
        
        col1, col2 = st.columns(2)
        
        # 이상치 제거 옵션
        with col1:
            use_iqr = st.checkbox("이상치(Outlier) 제거하고 보기", value=True, help="IQR 방식으로 비정상적으로 높거나 낮은 가격 데이터를 제외하여 그래프 가독성을 높입니다.")

        # 데이터 필터링 로직
        plot_data = filtered_shop.copy()
        if use_iqr:
            # 그룹별 IQR 계산 및 필터링
            def filter_outliers(group):
                Q1 = group['lprice'].quantile(0.25)
                Q3 = group['lprice'].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                return group[(group['lprice'] >= lower) & (group['lprice'] <= upper)]
            
            plot_data = plot_data.groupby('keyword', group_keys=False).apply(filter_outliers)

        with col1:
            # 그래프 4: 키워드별 가격 분포 박스 플롯
            fig4 = px.box(plot_data, x='keyword', y='lprice', color='keyword',
                          title="키워드별 상품 가격대 분포 (Box Plot)",
                          labels={'lprice': '최저가 (원)'},
                          template="plotly_white",
                          color_discrete_map=keyword_color_map)
            fig4.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color=PRIMARY_BROWN)
            st.plotly_chart(fig4, use_container_width=True)
            
        with col2:
            # 그래프 5: 주요 몰 분포 (Top 10)
            mall_counts = filtered_shop['mallName'].value_counts().head(10).reset_index()
            mall_counts.columns = ['mallName', 'count']
            fig5 = px.pie(mall_counts, values='count', names='mallName',
                          title="주요 판매처(Mall) 점유율 (Top 10)",
                          hole=0.4,
                          color_discrete_sequence=px.colors.sequential.YlOrBr) # Brown 계열 연속 색상 사용
            fig5.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color=PRIMARY_BROWN)
            st.plotly_chart(fig5, use_container_width=True)

        # 표 3: 상위 쇼핑 상품 리스트
        st.subheader("검색된 주요 쇼핑 상품")
        st.dataframe(filtered_shop[['title', 'lprice', 'mallName', 'category1', 'link']].head(500), use_container_width=True)
    else:
        st.write("쇼핑 데이터가 없습니다.")

# --- Tab 4: 통합 통계 ---
with tab4:
    st.header("4. 데이터 기초 EDA 및 통합 통계")
    
    if not filtered_trend.empty:
        # 표 4: 트렌드 기초 통계 요약
        st.subheader("키워드별 트렌드 기초 통계")
        desc_trend = filtered_trend.groupby('keyword')['ratio'].describe().reset_index()
        st.table(desc_trend)
        
        # 표 5: 가격 분석 요약 (쇼핑)
        if not filtered_shop.empty:
            st.subheader("키워드별 가격 분석 요약")
            desc_price = filtered_shop.groupby('keyword')['lprice'].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
            st.table(desc_price)
            
            # 그래프 6: 추가 그래프 (예: 히트맵 또는 산점도 - 생략 가능하나 조건 충족을 위해)
    
    st.success("대시보드 분석이 완료되었습니다.")
