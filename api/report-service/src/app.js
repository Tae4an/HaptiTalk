// OpenTelemetry 트레이싱 초기화 (가장 먼저 로드되어야 함)
// 환경 변수로 비활성화 가능
if (process.env.ENABLE_TRACING !== 'false') {
  try {
    require('./utils/tracing');
  } catch (error) {
    console.warn('[WARNING] OpenTelemetry 초기화 실패:', error.message);
    console.warn('[WARNING] 트레이싱 없이 계속 진행합니다.');
  }
}

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const logger = require('./utils/logger');
const metrics = require('./utils/metrics');
const {errorHandler} = require('./middleware/errorHandler.middleware');
const routes = require('./routes');
const { v4: uuidv4 } = require('uuid');

// 앱 초기화
const app = express();
const port = process.env.PORT || 3005;

// 요청 ID 미들웨어 - 각 요청에 고유 ID 부여
app.use((req, res, next) => {
    req.id = req.headers['x-request-id'] || uuidv4();
    res.setHeader('X-Request-ID', req.id);
    next();
});

// 미들웨어 설정
app.use(helmet());
app.use(cors());

// 로깅 미들웨어 추가
app.use(logger.requestMiddleware);

// 메트릭 미들웨어 설정
metrics.setupMetricsMiddleware(app);

// Morgan 설정 변경 - OpenTelemetry와 호환되는 안전한 로깅
app.use(morgan((tokens, req, res) => {
    const logMessage = JSON.stringify({
        method: tokens.method(req, res),
        url: tokens.url(req, res),
        status: tokens.status(req, res),
        contentLength: tokens.res(req, res, 'content-length'),
        responseTime: tokens['response-time'](req, res),
        timestamp: new Date().toISOString(),
        requestId: req.id,
        userAgent: tokens['user-agent'](req, res)
    });
    
    // OpenTelemetry 컨텍스트와 충돌하지 않도록 직접 콘솔 출력
    console.log(logMessage);
    
    return null; // Morgan의 기본 스트림 사용 방지
}));

app.use(express.json());
app.use(express.urlencoded({extended: true}));

// 헬스체크 엔드포인트
app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

// API 라우트
app.use('/api/v1/reports', routes);

// 로깅 에러 미들웨어 추가
app.use(logger.errorMiddleware);

// 메트릭 에러 미들웨어 추가
app.use(metrics.errorMetricsMiddleware);

// 오류 처리 미들웨어
app.use(errorHandler);

// 서버 시작
app.listen(port, () => {
    logger.info(`Report service running on port ${port}`, { 
        port, 
        environment: process.env.NODE_ENV,
        node_version: process.version
    });
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    logger.error('Unhandled Rejection', { 
        reason: reason instanceof Error ? reason.message : reason,
        stack: reason instanceof Error ? reason.stack : undefined,
        promise
    });
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    logger.error('Uncaught Exception', { 
        error: error.message, 
        stack: error.stack
    });
    process.exit(1);
});

module.exports = app;