FROM node:18-alpine

WORKDIR /app

# 기본 빌드 도구만 설치
RUN apk add --no-cache \
    python3 \
    make \
    g++ \
    pkgconf

# 패키지 파일 복사
COPY api/report-service/package*.json ./

# package.json 수정하여 chart.js와 canvas 의존성 제거
RUN sed -i 's/"chart.js": ".*",//g' package.json && \
    sed -i 's/"chartjs-node-canvas": ".*",//g' package.json

# color-name 버전 문제 해결을 위해 먼저 설치
RUN npm install --no-save color-name@1.1.4

# 필수 패키지만 설치
RUN npm install --production morgan prom-client express winston cors helmet jsonwebtoken ioredis pg sequelize

# 공유 모듈 복사 (auth-service 방식으로 통일)
COPY api/shared /app/api/shared

# 공유 모듈의 의존성 설치
WORKDIR /app/api/shared/kafka-client
RUN npm install
WORKDIR /app

# 소스 코드 복사
COPY api/report-service .

# 헬스체크 및 시작 스크립트
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD wget -qO- http://localhost:${PORT:-3005}/health || exit 1

# 포트 설정
EXPOSE ${PORT}

# 시작 명령어
CMD ["node", "src/app.js"]