# 🎯 SKAX Deal Board Agent

Claude claude-opus-4-7 기반의 AI 영업 지원 에이전트입니다.
회의록·통화 요약·음성 파일을 분석하여 MEDDIC 정보를 Salesforce 사업기회에 자동 반영합니다.

## 주요 기능

| 기능 | 설명 |
|------|------|
| 텍스트 분석 | 통화 요약, 미팅 기록, 이메일을 붙여넣기하면 MEDDIC 자동 추출 |
| 파일 첨부 | PDF/DOCX/TXT/JPG 회의록 업로드 후 분석 |
| 음성 업로드 | MP3/WAV/M4A 파일 → Whisper STT → MEDDIC 분석 |
| Deal Score | 영업성숙도(30) + 활동성(25) + MEDDIC(25) + 관계성(20) = 100점 |
| SF 반영 | MEDDIC 필드 + DealScore__c + Chatter 포스트 자동 업데이트 |

## 빠른 시작

### 1. 패키지 설치
```
cd C:\Users\07651\Desktop\dealBoardAgent
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```
copy .env.example .env
```
.env 파일을 열어 ANTHROPIC_API_KEY 입력

### 3. 실행
```
streamlit run app.py
```
브라우저에서 http://localhost:8501 접속

## 프로젝트 구조

```
dealBoardAgent/
├── app.py                      # Streamlit 메인 UI
├── agent/
│   └── deal_board_agent.py     # Claude API 에이전트 (MEDDIC 분석)
├── processors/
│   ├── file_processor.py       # PDF/DOCX/TXT/JPG 텍스트 추출
│   └── voice_processor.py      # 음성 → 텍스트 (Whisper)
├── salesforce/
│   └── sf_client.py            # SF 연동 (mock / live 모드)
├── models/
│   └── deal.py                 # 데이터 모델
├── requirements.txt
└── .env.example
```

## Salesforce 커스텀 필드

| SF 필드 | 설명 |
|---------|------|
| DealScore__c | 딜 스코어 (0-100) |
| MEDDIC_Metrics__c | 측정지표/ROI |
| MEDDIC_EB__c | 경제적 의사결정자 |
| MEDDIC_DC__c | 의사결정 기준 |
| MEDDIC_DP__c | 의사결정 프로세스 |
| MEDDIC_Paper__c | 계약 프로세스 |
| MEDDIC_Pain__c | 핵심 고충 |
| MEDDIC_Champion__c | 내부 지지자 |
| MEDDIC_Comp__c | 경쟁 현황 |
| AX_YN__c | AX 사업 여부 |
| SalesReviewStatus__c | 영업 리뷰 상태 |

## 모드 설명

- Mock 모드 (기본): Salesforce 연결 없이 로컬 샘플 데이터로 동작. 데모/개발에 사용.
- Live 모드: 실제 Salesforce API 연동. .env에 SF 계정 정보 필요.
