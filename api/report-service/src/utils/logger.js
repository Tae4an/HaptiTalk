// 서비스 이름 설정
const SERVICE_NAME = process.env.SERVICE_NAME || 'report-service';

// 간단한 console 기반 로거 (winston ES Module 문제 회피)
const logger = {
    level: process.env.LOG_LEVEL || 'info',
    
    _log(level, message, meta = {}) {
        const timestamp = new Date().toISOString();
        const logObject = {
            timestamp,
            level,
            service: SERVICE_NAME,
            message,
            ...meta
        };
        
        const logString = JSON.stringify(logObject);
        
        if (level === 'error') {
            console.error(logString);
        } else if (level === 'warn') {
            console.warn(logString);
        } else {
            console.log(logString);
        }
    },
    
    info(message, meta) {
        this._log('info', message, meta);
    },
    
    warn(message, meta) {
        this._log('warn', message, meta);
    },
    
    error(message, meta) {
        this._log('error', message, meta);
    },
    
    debug(message, meta) {
        if (this.level === 'debug') {
            this._log('debug', message, meta);
        }
    }
};

// HTTP 요청 로깅 미들웨어
logger.requestMiddleware = (req, res, next) => {
    const start = Date.now();
    const requestId = req.headers['x-request-id'] || req.id;
    
    // 요청 정보 로깅
    logger.info(`Request received: ${req.method} ${req.originalUrl}`, {
        requestId,
        method: req.method,
        url: req.originalUrl,
        ip: req.ip,
        headers: req.headers,
        userId: req.user?.id
    });

    // 응답이 끝나면 결과 로깅
    res.on('finish', () => {
        const duration = Date.now() - start;
        const message = `Request completed: ${req.method} ${req.originalUrl} ${res.statusCode} ${duration}ms`;
        
        const logObject = {
            requestId,
            method: req.method,
            url: req.originalUrl,
            statusCode: res.statusCode,
            duration,
            ip: req.ip,
            userId: req.user?.id
        };

        if (res.statusCode >= 400) {
            logger.warn(message, logObject);
        } else {
            logger.info(message, logObject);
        }
    });

    next();
};

// 에러 핸들링 미들웨어
logger.errorMiddleware = (err, req, res, next) => {
    const requestId = req.headers['x-request-id'] || req.id;

    logger.error(`Error processing request: ${err.message}`, {
        requestId,
        method: req.method,
        url: req.originalUrl,
        statusCode: err.status || 500,
        error: err.message,
        stack: err.stack,
        userId: req.user?.id
    });

    next(err);
};

module.exports = logger;
