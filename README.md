# HaptiTalk - 실시간 대화 코칭 시스템

> 실시간 대화 분석과 햅틱 피드백을 결합한 AI 서비스 기반 커뮤니케이션 코칭 시스템
<img width="1039" height="584" alt="image" src="https://github.com/user-attachments/assets/329919ee-8b35-4d75-931a-d3430f7dea73" />

## 프로젝트 개요

**HaptiTalk**은 발표, 면접 등 실제 대면 상황에서 **스마트워치를 통한 은밀한 햅틱 피드백**으로 즉각적인 대화 코칭을 제공하는 시스템입니다.
**HaptiTalk**은 기존 커뮤니케이션 코칭 도구의 한계를 뛰어넘는 실시간 솔루션을 제시합니다.

### 핵심 가치
- **실시간 대화 분석**: WhisperX 기반 고성능 STT 및 음성 분석
- **은밀한 햅틱(진동) 피드백**: 상대방 모르게 받는 자연스러운 실시간 코칭
- **세그먼트 기반 분석**: 기존 방식 대비 85% 향상된 말하기 속도 측정 정확도
- **시나리오별 맞춤화**: 발표/면접 상황별 특화된 분석 및 피드백

---

## 개발팀
개발 기간: **2025년 3월 4일 ~ 6월 12일** (총 14주)
| 역할 | 이름 | 전문 분야 | 연락처 |
|------|------|----------|--------|
| **팀장 & 풀스택** | 최태산 | 시스템 설계/통합, DevOps | xotks7524@gmail.com |
| **AI/ML** | 정연균 | 음성처리, 감정분석 | jungyk411@sunmoon.ac.kr |
| **프론트엔드** | 이은범 | Flutter, 모바일 개발 | bum17822@naver.com |

---

| 영상 종류 | 썸네일 및 링크 |
|:--:|:--:|
| 소개 영상 | [![소개 영상](https://github.com/user-attachments/assets/d0faa8a4-3ae1-4765-8206-34717aac0bef)](https://www.youtube.com/watch?v=s1fxJsoVDjs) |
| 시연 영상 | [![시연 영상](https://github.com/user-attachments/assets/bb6fe102-613a-4e65-b099-7186531c36d7)](https://www.youtube.com/watch?v=nllbIaujAKU) |


---

## 시스템 아키텍처
<img width="1411" height="682" alt="image" src="https://github.com/user-attachments/assets/ff463093-0990-4ed1-a6b3-ac951eb65b12" />


## AI 처리 파이프라인
<img width="1039" height="396" alt="image" src="https://github.com/user-attachments/assets/6d1de731-681d-438c-9b0a-21284b3c9bda" />

<img width="1423" height="245" alt="image" src="https://github.com/user-attachments/assets/c8a1aa65-8842-4cc6-a79b-86c56ab2e019" />

![image](https://github.com/user-attachments/assets/3bf49042-8658-41fb-b948-31c242a204fa)

<img width="1429" height="157" alt="image" src="https://github.com/user-attachments/assets/724fdec2-3e70-4dc1-9706-a97d56e5f368" />


- **STT Engine**: WhisperX v3.3.4 기반 실시간 음성 인식
- **Emotion Analysis**: Wav2Vec2-XLSR 모델로 7가지 감정 분류
- **Speaker Diarization**: pyannote.audio 3.1 다중 화자 식별
- **AI Report**: Google Gemini API 기반 맞춤형 분석 보고서

## ERD
<img width="1036" height="710" alt="image" src="https://github.com/user-attachments/assets/c91750d5-b5dd-4dbb-9d1c-0a4601cdacc6" />

## MongoDB Schema Diagram
<img width="1048" height="593" alt="image" src="https://github.com/user-attachments/assets/d37e2c0d-c697-4d40-96bd-35cfc9ce0066" />

---

## 주요 기능
<img width="1040" height="586" alt="image" src="https://github.com/user-attachments/assets/78a3c86d-451f-423e-84d2-8530316b7edc" />

<img width="1041" height="585" alt="image" src="https://github.com/user-attachments/assets/22c776c4-f1af-462e-be83-2b0cd70198f7" />

<img width="1037" height="585" alt="image" src="https://github.com/user-attachments/assets/21efecde-0f3b-4777-842b-0e5756f63a92" />

---

### 주요 화면 구성

| 로그인 화면 | 회원가입 화면 | 메인 화면 | 프로필 화면 |
|:---:|:---:|:---:|:---:|
| <img width="245" alt="image" src="https://github.com/user-attachments/assets/8c659218-9a73-4936-8eeb-9392ff6efe85" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/10fec808-9551-4dc7-9759-6e4b11d918c7" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/822816ff-fcd9-4e82-a0f8-21d0371ff779" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/a4592d77-5704-4dd3-99af-342683947534" /> |


| 새 세션 시작 화면 | 실시간 분석 화면 | 햅틱 패턴 연습 화면 | 설정 화면 |
|:---:|:---:|:---:|:---:|
| <img width="245" alt="image" src="https://github.com/user-attachments/assets/1d2a175a-7457-4dc4-8421-9799cfed65df" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/a5d7debf-d2e0-4dc3-8d3f-6017e2f14643" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/05375aa2-ed82-4a58-b260-c9bd3f041608" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/2728ff25-73df-40b1-99b3-8658b23cf1b1" /> |


| 분석 요약 화면 | 타임라인 화면 | 말하기 패턴 화면 | 대화 주제 화면 |
|:---:|:---:|:---:|:---:|
| <img width="245" alt="image" src="https://github.com/user-attachments/assets/f330e46d-d020-4df5-9507-efe572d21910" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/ac4f7ce4-5826-4697-9338-c9d276bab81d" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/8ee09f36-e0d2-4ae6-8bdb-321619a03da4" /> | <img width="245" alt="image" src="https://github.com/user-attachments/assets/3d0b8e02-55d4-4b41-9a67-83c85fcd41a9" /> |


#### Apple Watch 화면 
| 메인 화면 | 세션 화면 | 설정 화면 |
|:---:|:---:|:---:|
| <img width="200" alt="image" src="https://github.com/user-attachments/assets/a3a98071-23d7-425e-bef1-da1280fa74df" /> | <img width="200" alt="image" src="https://github.com/user-attachments/assets/6bbecd6c-5229-4982-a141-33bc3d4b2eec" /> | <img width="200" alt="image" src="https://github.com/user-attachments/assets/95d1e8c7-2150-44c4-9147-f40cd8159f7c" /> |


#### Apple Watch 햅틱 피드백 애니메이션
| 말하기 속도 조절 | 필러워드 감지 | 자신감 상승 | 자신감 하락 |
|:---:|:---:|:---:|:---:|
| <img width="200" alt="image" src="https://github.com/user-attachments/assets/4b439997-b831-4608-9340-e20275a2846b" /> | <img width="200" alt="image" src="https://github.com/user-attachments/assets/440b2ad6-f50c-40f9-bc37-dc6af64c9d4b" /> | <img width="200" alt="image" src="https://github.com/user-attachments/assets/c1158e26-7d03-4f01-9380-ce6f6fd76331" /> | <img width="200" alt="image" src="https://github.com/user-attachments/assets/2f94286c-ca2c-4a61-b000-303a5a96e811" /> |

---

## 기술 스택

### Frontend
```
Flutter 3.x          │ 크로스 플랫폼 모바일 앱
├── Provider         │ 상태 관리
├── WebSocket        │ 실시간 통신  
├── Watch Connectivity│ 스마트워치 연동
└── Material Design 3│ 현대적 UI/UX
```

### Backend Services
```
Node.js + Express    │ 마이크로서비스 프레임워크
├── auth-service     │ JWT 기반 인증 및 권한 관리
├── session-service  │ 세션 생명주기 관리
├── feedback-service │ 햅틱 피드백 생성 및 전송
├── user-service     │ 사용자 프로필 및 설정 관리
├── realtime-service │ WebSocket 실시간 통신
├── report-service   │ AI 보고서 생성 및 관리
└── notification-service │ 푸시 알림 및 이벤트 처리
```

### AI Services
```
Python + FastAPI     │ AI 마이크로서비스
├── STT Service      │ WhisperX v3.3.4 음성 인식
├── Emotion Analysis │ Wav2Vec2-XLSR 감정 분석
└── Speaker Diarization │ pyannote.audio 화자 분리
```

### Infrastructure
```
Docker + Compose     │ 컨테이너 오케스트레이션
├── Kong             │ API Gateway 및 인증
├── PostgreSQL       │ 사용자/세션 관계형 데이터
├── MongoDB          │ 비정형 분석 결과 저장
├── Redis            │ 캐싱 및 세션 관리
└── Kafka            │ 비동기 메시징 시스템
```

### Monitoring & DevOps
```
Observability Stack  │ 통합 관찰성 시스템
├── Prometheus       │ 메트릭 수집 및 저장
├── Grafana          │ 통합 관찰성 플랫폼 (메트릭/로그/트레이스)
├── ELK Stack        │ 로그 수집, 처리 및 검색
├── Jaeger           │ 분산 트레이싱 및 성능 분석
└── OpenTelemetry    │ 트레이스 수집 및 전처리
```

---

## 기술적 특징

### 세그먼트 기반 말하기 속도 분석
기존 전체 시간 기반 WPM 계산의 한계를 극복한 혁신적 알고리즘:

```python
# 기존 방식 (부정확)
traditional_wpm = total_words / total_time * 60  # pause 시간 포함

# HaptiTalk 세그먼트 방식 (85% 향상)
segment_wpm = (words_in_segment / segment_duration) * 60
average_wpm = sum(segment_wpms) / len(segments)  # 순수 발화 시간만 계산
```

### 6가지 말하기 패턴 자동 분류
- **staccato**: 끊어 말하기 패턴 감지
- **continuous**: 연속적 발화 패턴
- **very_sparse**: 매우 띄엄띄엄 말하기
- **steady**: 일정한 속도 유지
- **variable**: 속도 변화가 큰 패턴  
- **normal**: 일반적인 대화 패턴

### 시나리오별 특화 분석
| 시나리오 | VAD 임계값 | 침묵 허용 | 감정 가중치 | 분석 초점 |
|---------|-----------|----------|-----------|----------|
| **면접** | 0.7 | 1000ms | 중립(1.3x) | 자신감, 명확성 |
| **발표** | 0.75 | 800ms | 안정감 중심 | 전달력, 설득력 |

---

## 성능 지표

### 핵심 성능
- **STT 정확도**: 95% 이상 (한국어 기준)
- **감정 분석 정확도**: 87% (7가지 감정 분류)
- **평균 처리 지연**: 150ms 이하 (GPU 환경)
- **동시 세션 처리**: 4개 (Jetson Orin Nano 기준)
- **모바일 네트워크 지연**: 200ms 이하
- **배터리 최적화**: 1시간 연속 사용 시 15% 이하 소모

### 하드웨어 최적화
- **NVIDIA Jetson Orin Nano 8GB**: ARM64 아키텍처 네이티브 최적화
- **CUDA 12.6**: GPU 가속 처리로 95% 효율성 달성
- **메모리 사용량**: 전체 시스템 6GB 이하 유지

---
## 모니터링 시스템

### 통합 관찰성 플랫폼 (Grafana)
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/9e8aabcc-ffb8-4aff-89e8-bf1bd8e58e01" />
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/43575777-2d81-49aa-8abb-d5469f1896c5" />

- **기능**: 메트릭, 로그, 트레이스 통합 시각화 및 분석
- **통합 기능**: 트레이스→로그 연결, 메트릭→트레이스 드릴다운
- **모니터링 항목**: API 응답시간, 메모리 사용량, 처리 성공률, 에러율

### 메트릭 수집 (Prometheus)  
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/6adf560a-fbdd-4dd8-a097-c466e202a9a8" />
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/6f23aaa6-9002-443e-946f-0b7ba4d84c44" />

- **기능**: 시계열 메트릭 수집 및 저장
- **수집 대상**: 시스템 리소스, 애플리케이션 성능, 데이터베이스 상태
- **Exporters**: Node, PostgreSQL, Redis, MongoDB, Elasticsearch 메트릭

### 로그 관리 (ELK Stack)
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/8e4a30d6-a596-41f1-927a-c4a733d1fe02" />

- **기능**: 중앙화된 로그 수집, 처리 및 검색
- **구성**: Filebeat → Logstash → Elasticsearch → Kibana
- **활용**: 에러 추적, 사용자 행동 분석, 성능 병목 식별

### 분산 트레이싱 (Jaeger)
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/932db154-b322-4ad7-9e50-237f1df9df9b" />
<img width="1000" alt="image" src="https://github.com/user-attachments/assets/df644c80-ba65-4ac7-a914-743b7f8a9acf" />

- **기능**: 마이크로서비스 간 요청 추적 및 성능 분석
- **수집**: OpenTelemetry Collector를 통한 트레이스 데이터 수집
- **활용**: End-to-end 성능 분석, 병목 지점 탐지, 서비스 의존성 분석

---

## 프로젝트 성과

### 기술적 혁신
- 세계 최초 실시간 대화분석+햅틱피드백 결합 시스템
- 85% 향상된 세그먼트 기반 말하기 속도 측정 정확도
- 95% 달성한 한국어 STT 인식 정확도
- 150ms 이하 실시간 처리 지연시간

### 수상 및 특허
- **SW중심대학협의회 SW중심대학 우수작품경진대회 후원기업상** (2025)
- **선문대학교 SW중심대학 창업 아이디어 경진대회 최우수상** (2025)
- **선문대학교 SW중심대학 기업연계 프로젝트 우수팀 경진대회 대상** (2025)
- **한국디지털콘텐츠학회 하계종합학술대회 대학생 논문경진대회 대상** (2025)
- **제 8회 대학생 창의력 경진대회 우수상** (2025)
- **특허 출원(완)** 

---

## 연락처

### 프로젝트 문의
- **GitHub Issues**: 기술적 문의 및 버그 리포트
- **이메일**: xotks7524@gmail.com (프로젝트 총괄)
- **연구실**: 선문대학교 컴퓨터공학부

### 협업 제안
기업 협력, 연구 참여, 기술 이전 등의 제안은 최태산(xotks7524@gmail.com)에게 직접 연락주시기 바랍니다.

---

<div align="center">

**HaptiTalk** - *Revolutionizing Communication with AI and Haptic Technology*

*Made with ❤️ by Sunmoon University SW Development Team*

</div>
