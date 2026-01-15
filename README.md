# 네이버 키워드 데이터 분석 대시보드 🧆

네이버 검색, 블로그, 쇼핑 데이터를 분석하는 Streamlit 대시보드입니다.

## 🚀 빠른 시작

### 1. 필수 요구사항

- Python 3.8+
- 네이버 개발자 API 계정

### 2. 네이버 API 발급받기

1. [네이버 개발자 센터](https://developers.naver.com/apps/#/register) 접속
2. **애플리케이션 등록** 클릭
3. **사용 API 선택**:
   - ✅ 검색
   - ✅ 데이터랩 (쇼핑인사이트)
4. 등록 후 **Client ID**와 **Client Secret** 복사

### 3. API 인증 정보 설정

#### 방법 1: .env 파일 (권장)

```bash
# .env.example을 복사하여 .env 파일 생성
cp .env.example .env

# .env 파일을 열어서 실제 값으로 수정
NAVER_CLIENT_ID=your_actual_client_id
NAVER_CLIENT_SECRET=your_actual_client_secret
```

#### 방법 2: 환경 변수

```bash
export NAVER_CLIENT_ID=your_actual_client_id
export NAVER_CLIENT_SECRET=your_actual_client_secret
```

#### 방법 3: Streamlit Cloud Secrets (배포 시)

`.streamlit/secrets.toml` 파일 생성:

```toml
NAVER_CLIENT_ID = "your_actual_client_id"
NAVER_CLIENT_SECRET = "your_actual_client_secret"
```

### 4. 패키지 설치

```bash
pip install -r requirements.txt
```

### 5. 실행

```bash
streamlit run app.py
```

## 📊 주요 기능

- **트렌드 분석**: 키워드별 검색 트렌드 시계열 분석
- **블로그 분석**: 네이버 블로그 게시물 통계 및 분석
- **쇼핑 분석**: 상품 가격대 분포 및 판매처 분석
- **통합 통계**: EDA 및 키워드별 종합 통계

## 🔧 문제 해결

### "수집된 데이터가 없습니다" 오류

1. **API 인증 정보 확인**
   - 사이드바에서 "API 연결 상태" 확인
   - ❌ 표시가 있다면 .env 파일 설정 필요

2. **네이버 개발자 센터 확인**
   - API 사용이 승인되었는지 확인
   - 일일 호출 한도를 초과하지 않았는지 확인

3. **진단 정보 확인**
   - 대시보드에서 에러 메시지 확인
   - HTTP 401/403: 인증 실패 → API 키 재확인
   - HTTP 429: 요청 한도 초과 → 잠시 후 재시도

## 📝 사용된 API

- [네이버 검색 API](https://developers.naver.com/docs/serviceapi/search/search.md)
- [네이버 데이터랩 API](https://developers.naver.com/docs/serviceapi/datalab/search/search.md)

## 🔒 보안 주의사항

- `.env` 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 `.env`가 포함되어 있는지 확인하세요
- Client ID와 Secret은 공개하지 마세요
