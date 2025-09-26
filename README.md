# JSON Annotation Validator

두 JSON/JSONL 파일을 비교하여 변경사항을 분석하는 웹 애플리케이션입니다.

## 기능

- **파일 업로드**: 두 개의 JSON/JSONL 파일을 웹 인터페이스를 통해 업로드
- **상세 분석**: 텍스트, 메타데이터, 어노테이션의 모든 변경사항 분석
- **시각적 보고서**: 웹 페이지에서 변경사항을 직관적으로 확인
- **보고서 다운로드**: 분석 결과를 JSON 형식으로 다운로드
- **실시간 통계**: 변경 유형별 통계 및 요약 정보 제공

## 분석 항목

### 1. 텍스트 변경사항
- 텍스트 길이 차이
- 라인별 추가/삭제
- 문자 단위 변경사항 및 위치 정보

### 2. 메타데이터 변경사항
- 필드 추가/삭제/수정
- 값 변경 추적
- 무시할 필드 설정 (예: provenance)

### 3. Subject 변경사항
- Subject 수량 변화
- Subject ID별 변경사항
- Description 변경
- PII 어노테이션 변경

### 4. PII 어노테이션 분석
- 태그별 추가/삭제/수정
- 필드별 변경사항 (keyword, certainty, hardness)
- 특정 패턴 감지 (예: Turkey → Türkiye, 나이 형식 변경)

## 설치 및 실행

### 방법 1: Docker 사용 (권장)

#### 1. Docker 설치 확인
```bash
docker --version
docker-compose --version
```

#### 2. 애플리케이션 실행
```bash
# 자동 실행 스크립트 사용
./run.sh

# 또는 수동 실행
docker-compose up -d
```

#### 3. Nginx와 함께 실행 (선택사항)
```bash
docker-compose --profile nginx up -d
```

#### 4. 웹 브라우저에서 접속
- 직접 접속: http://localhost:55007
- Nginx 프록시: http://localhost:55007

### 방법 2: 로컬 실행

#### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

#### 2. 애플리케이션 실행
```bash
python app.py
```

#### 3. 웹 브라우저에서 접속
```
http://localhost:55007
```

## 프로젝트 구조

```
annotation_validator/
├── app/                    # Flask 애플리케이션
│   ├── __init__.py        # 앱 팩토리
│   ├── routes.py          # 라우트 정의
│   ├── templates/         # HTML 템플릿
│   │   ├── base.html
│   │   ├── index.html
│   │   └── report.html
│   └── static/            # 정적 파일
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── core/                  # 핵심 분석 로직
│   └── analyzer.py        # JSON 분석 클래스
├── uploads/               # 업로드된 파일 저장
├── reports/               # 생성된 보고서 저장
├── app.py                 # 메인 애플리케이션
├── requirements.txt       # Python 의존성
├── Dockerfile            # Docker 이미지 정의
├── docker-compose.yml    # Docker Compose 설정
├── nginx.conf            # Nginx 설정
├── .dockerignore         # Docker 빌드 제외 파일
├── run.sh               # 자동 실행 스크립트
└── README.md            # 프로젝트 문서
```

## 사용법

### 1. 파일 업로드
- 웹 페이지에서 "원본 파일"과 "내보낸 파일"을 선택
- JSON 또는 JSONL 형식의 파일만 지원
- 최대 파일 크기: 16MB

### 2. 분석 실행
- "분석 시작" 버튼 클릭
- 분석이 완료되면 결과 요약이 표시됨

### 3. 결과 확인
- **상세 보고서 보기**: 웹 페이지에서 변경사항 상세 확인
- **보고서 다운로드**: JSON 형식으로 분석 결과 다운로드

## API 엔드포인트

### POST /upload
파일 업로드 및 분석 실행
- **요청**: multipart/form-data
  - `original_file`: 원본 파일
  - `exported_file`: 내보낸 파일
- **응답**: JSON
  ```json
  {
    "success": true,
    "session_id": "uuid",
    "report_filename": "report_uuid.json",
    "summary": {
      "total_records": 100,
      "records_with_changes": 5,
      "text_changes": 2,
      "description_changes": 3
    }
  }
  ```

### GET /report/<session_id>
분석 보고서 웹 페이지 표시

### GET /download/<session_id>
분석 보고서 JSON 파일 다운로드

### GET /api/report/<session_id>
분석 보고서 JSON 데이터 반환

## 설정

### 무시할 필드 설정
`core/analyzer.py`의 `ignored_fields` 리스트에서 무시할 메타데이터 필드를 설정할 수 있습니다.

```python
self.ignored_fields = ["provenance", "timestamp"]
```

### 파일 크기 제한
`app/__init__.py`에서 최대 업로드 파일 크기를 설정할 수 있습니다.

```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

## 기술 스택

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **분석**: Python difflib, JSON 처리
- **UI**: Font Awesome 아이콘, 반응형 디자인

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요.

## Docker 명령어

### 기본 명령어
```bash
# 컨테이너 빌드 및 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 컨테이너 중지
docker-compose down

# 컨테이너 재시작
docker-compose restart

# 이미지 재빌드
docker-compose build --no-cache
```

### Nginx와 함께 실행
```bash
# Nginx 프록시 포함 실행
docker-compose --profile nginx up -d

# Nginx만 중지
docker-compose stop nginx
```

### 개발 모드
```bash
# 개발 모드로 실행 (디버그 활성화)
FLASK_DEBUG=1 docker-compose up
```

## 변경 이력

- v1.0.0: 초기 버전 - 기본 파일 비교 기능
- v1.1.0: 웹 인터페이스 추가
- v1.2.0: 상세 텍스트 분석 및 시각화 개선
- v1.3.0: Docker 컨테이너 지원 추가
- v1.3.1: 포트 55007로 변경
