/**
 * Prometheus 메트릭 설정
 * user-service용 메트릭 모듈
 */

const client = require('prom-client');
const logger = require('./logger');

// 메트릭 레지스트리 생성
const collectDefaultMetrics = client.collectDefaultMetrics;
const Registry = client.Registry;
const register = new Registry();

// 기본 Node.js 메트릭 수집 (CPU, 메모리 등)
collectDefaultMetrics({ register });

// HTTP 요청 지속시간 측정 히스토그램
const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP 요청 처리 시간 (초)',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
});
register.registerMetric(httpRequestDurationMicroseconds);

// 요청 카운터 - API 엔드포인트별 호출 횟수
const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: '총 HTTP 요청 수',
  labelNames: ['method', 'route', 'status_code']
});
register.registerMetric(httpRequestsTotal);

// 활성 연결 수 게이지
const httpActiveConnections = new client.Gauge({
  name: 'http_active_connections',
  help: '현재 활성 HTTP 연결 수'
});
register.registerMetric(httpActiveConnections);

// API 오류 카운터
const apiErrorsTotal = new client.Counter({
  name: 'api_errors_total',
  help: 'API 처리 중 발생한 오류 수',
  labelNames: ['method', 'route', 'error_type']
});
register.registerMetric(apiErrorsTotal);

// 사용자 관련 메트릭
const userMetrics = {
  userCreationsTotal: new client.Counter({
    name: 'user_creations_total',
    help: '사용자 생성 총 수',
    labelNames: ['status'] // success, failed
  }),
  userUpdatesTotal: new client.Counter({
    name: 'user_updates_total',
    help: '사용자 정보 업데이트 총 수',
    labelNames: ['status', 'type'] // status: success, failed, type: profile, preferences, etc.
  }),
  userProfileViewsTotal: new client.Counter({
    name: 'user_profile_views_total',
    help: '사용자 프로필 조회 총 수',
    labelNames: ['status'] // success, failed
  }),
  totalUsersGauge: new client.Gauge({
    name: 'total_users_gauge',
    help: '전체 사용자 수'
  }),
  databaseQueryDuration: new client.Histogram({
    name: 'database_query_duration_seconds',
    help: '데이터베이스 쿼리 실행 시간 (초)',
    labelNames: ['operation', 'entity'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5]
  })
};

// 사용자 메트릭 등록
Object.values(userMetrics).forEach(metric => register.registerMetric(metric));

// Express.js 미들웨어 설정
function setupMetricsMiddleware(app) {
  // 메트릭 엔드포인트 설정
  app.get('/metrics', async function(req, res) {
    try {
      res.set('Content-Type', register.contentType);
      res.end(await register.metrics());
    } catch (error) {
      logger.error('메트릭 생성 중 오류 발생', { error: error.message });
      res.status(500).end();
    }
  });

  // 요청 측정 미들웨어
  app.use((req, res, next) => {
    // 활성 연결 증가
    httpActiveConnections.inc();
    
    // 요청 타이머 시작
    const end = httpRequestDurationMicroseconds.startTimer();
    
    // 응답 완료 이벤트 핸들러
    res.on('finish', () => {
      // 라벨 데이터 준비
      const route = req.route ? req.route.path : req.path;
      const method = req.method;
      const statusCode = res.statusCode;
      
      // 타이머 종료 및 히스토그램 업데이트
      end({ method, route, status_code: statusCode });
      
      // 요청 카운터 증가
      httpRequestsTotal.inc({ method, route, status_code: statusCode });
      
      // 활성 연결 감소
      httpActiveConnections.dec();
    });
    
    next();
  });
}

// 에러 처리 미들웨어
function errorMetricsMiddleware(err, req, res, next) {
  const route = req.route ? req.route.path : req.path;
  const method = req.method;
  const errorType = err.name || 'UnknownError';
  
  // 오류 카운터 증가
  apiErrorsTotal.inc({ method, route, error_type: errorType });
  
  next(err);
}

// DB 운영 시간 측정 유틸리티 함수
function measureDatabaseOperation(operation, entity, asyncFn) {
  const end = userMetrics.databaseQueryDuration.startTimer({ operation, entity });
  
  return asyncFn()
    .then(result => {
      end();
      return result;
    })
    .catch(err => {
      end();
      throw err;
    });
}

module.exports = {
  register,
  setupMetricsMiddleware,
  errorMetricsMiddleware,
  measureDatabaseOperation,
  metrics: {
    httpRequestDurationMicroseconds,
    httpRequestsTotal,
    httpActiveConnections,
    apiErrorsTotal,
    ...userMetrics
  }
}; 