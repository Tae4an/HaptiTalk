const express = require('express');
const http = require('http');
const {Server} = require('socket.io');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const {createRedisClient} = require('./config/redis');
const authMiddleware = require('./middleware/auth.middleware');
const logger = require('./utils/logger');
const {setServiceAuthToken} = require('./config/api-client');
const ConnectionManager = require('./utils/connection-manager');
const SocketMonitor = require('./utils/socket-monitor');
const RedisPubSub = require('./utils/redis-pubsub');
const { v4: uuidv4 } = require('uuid');

// 기본 설정
const PORT = process.env.PORT || 3001;

// 서비스 간 통신을 위한 API 토큰
const INTER_SERVICE_TOKEN = process.env.INTER_SERVICE_TOKEN || 'default-service-token';

// Redis 클라이언트 초기화
const redisClient = createRedisClient();

// Express 앱 초기화
const app = express();
const server = http.createServer(app);

// 요청 ID 미들웨어 - 각 요청에 고유 ID 부여
app.use((req, res, next) => {
    req.id = req.headers['x-request-id'] || uuidv4();
    res.setHeader('X-Request-ID', req.id);
    next();
});

// Express 미들웨어
app.use(helmet());
app.use(cors());

// 로깅 미들웨어 추가
app.use(logger.requestMiddleware);

// Morgan 설정 변경 - JSON 형식 로그 출력
app.use(morgan((tokens, req, res) => {
    return JSON.stringify({
        method: tokens.method(req, res),
        url: tokens.url(req, res),
        status: tokens.status(req, res),
        contentLength: tokens.res(req, res, 'content-length'),
        responseTime: tokens['response-time'](req, res),
        timestamp: new Date().toISOString(),
        requestId: req.id,
        userAgent: tokens['user-agent'](req, res)
    });
}, { stream: { write: message => logger.http(message) } }));

app.use(express.json());

// 상태 확인 엔드포인트
app.get('/health', (req, res) => {
    res.status(200).send('OK');
});

// 버전 정보 엔드포인트
app.get('/api/v1/realtime/version', (req, res) => {
    res.json({
        service: 'realtime-service',
        version: '0.1.0',
        status: 'running'
    });
});

// Socket.io 초기화
const io = new Server(server, {
    cors: {
        origin: '*',
        methods: ['GET', 'POST']
    },
    path: '/socket.io/',
    // 성능 최적화 설정 추가
    pingTimeout: 30000,
    pingInterval: 10000,
    transports: ['websocket', 'polling'],
    // 폴링보다 웹소켓 선호
    allowUpgrades: true,
    // 메시지 압축
    perMessageDeflate: {
        threshold: 1024, // 1KB 이상 메시지에 압축 적용
    }
});

// 연결 관리자 및 모니터링 초기화
const connectionManager = new ConnectionManager(io, redisClient);
const socketMonitor = new SocketMonitor(io, redisClient);
const pubSub = new RedisPubSub(redisClient, io, {
    batchSize: 20,
    flushInterval: 50,
    retryAttempts: 3
});

// Socket.io 미들웨어 적용
io.use(async (socket, next) => {
    try {
        const token = socket.handshake.auth.token;
        if (!token) {
            return next(new Error('인증 토큰이 필요합니다'));
        }

        // 토큰 검증
        const user = await authMiddleware.verifySocketToken(token, redisClient);
        socket.user = user;
        
        // 연결 관리자에 연결 추가
        await connectionManager.addConnection(socket.id, user);
        
        // 소켓 연결 로깅
        logger.socketLogger.connect(socket.id, user.id);
        
        next();
    } catch (error) {
        logger.error(`소켓 인증 오류:`, {
            error: error.message,
            stack: error.stack
        });
        next(new Error('유효하지 않은 토큰입니다'));
    }
});

// 모니터링 엔드포인트
app.get('/api/v1/realtime/stats', authMiddleware.validateServiceToken, (req, res) => {
    const stats = socketMonitor.getMetrics();
    res.json({
        success: true,
        data: stats
    });
});

// 소켓 진단 엔드포인트
app.get('/api/v1/realtime/socket/:socketId', authMiddleware.validateServiceToken, async (req, res) => {
    const { socketId } = req.params;
    const socketInfo = await socketMonitor.diagnoseSocket(socketId);
    
    res.json({
        success: true,
        data: socketInfo
    });
});

// 에러 미들웨어 추가
app.use(logger.errorMiddleware);

// 이벤트 핸들러 등록
require('./events')(io, redisClient, pubSub);

// 연결 활동 업데이트 함수
const updateActivity = async (socket) => {
    try {
        await connectionManager.updateActivity(socket.id);
    } catch (error) {
        logger.error(`활동 업데이트 오류:`, {
            socketId: socket.id,
            userId: socket.user?.id,
            error: error.message,
            stack: error.stack
        });
    }
};

// 모든 소켓 이벤트에 활동 추적 추가
io.on('connection', (socket) => {
    const originalOnEvent = socket.onevent;
    socket.onevent = function(packet) {
        updateActivity(socket);
        return originalOnEvent.apply(this, arguments);
    };
    
    // 연결 종료 시 처리
    socket.on('disconnect', async (reason) => {
        try {
            await connectionManager.removeConnection(socket.id);
            logger.socketLogger.disconnect(socket.id, socket.user?.id, reason);
        } catch (error) {
            logger.error(`연결 제거 오류:`, {
                socketId: socket.id,
                userId: socket.user?.id,
                error: error.message,
                stack: error.stack
            });
        }
    });
});

// 서버 시작
const startServer = async () => {
    try {
        // Redis 연결 확인
        await redisClient.ping();
        logger.info('Redis 서버 연결 성공', {
            component: 'redis',
            status: 'connected'
        });

        // 서비스 간 통신을 위한 API 토큰 설정
        setServiceAuthToken(INTER_SERVICE_TOKEN);
        logger.info('서비스 간 통신을 위한 인증 토큰이 설정되었습니다', {
            component: 'auth',
            status: 'configured'
        });
        
        // 연결 관리자 초기화
        connectionManager.initialize();
        
        // 소켓 모니터링 시작
        socketMonitor.start();
        
        // Redis PubSub 초기화
        await pubSub.start();
        
        // 피드백 및 분석 채널 구독
        pubSub.subscribe('feedback:channel:*', (channel, message) => {
            const sessionId = channel.split(':')[2];
            io.to(`session:${sessionId}`).emit('feedback', message);
        });
        
        pubSub.subscribe('analysis:events:*', (channel, message) => {
            const sessionId = channel.split(':')[2];
            io.to(`session:${sessionId}`).emit('analysis_update', message);
        });

        // 서버 시작
        server.listen(PORT, () => {
            logger.info(`실시간 서비스가 포트 ${PORT}에서 실행 중입니다`, { 
                port: PORT, 
                environment: process.env.NODE_ENV,
                node_version: process.version
            });
        });
    } catch (error) {
        logger.error(`서버 시작 실패:`, {
            error: error.message,
            stack: error.stack,
            component: 'startup'
        });
        process.exit(1);
    }
};

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

// 종료 시 정리 작업
const gracefulShutdown = async () => {
    logger.info('서버 종료 중...', {
        component: 'lifecycle',
        action: 'shutdown'
    });

    // 소켓 모니터링 중지
    socketMonitor.stop();
    
    // 연결 관리자 정리
    connectionManager.cleanup();
    
    // PubSub 정리
    await pubSub.stop();

    // Socket.io 연결 종료
    io.close(() => {
        logger.info('모든 WebSocket 연결이 종료되었습니다', {
            component: 'websocket',
            status: 'closed'
        });
    });

    // Redis 연결 종료
    await redisClient.quit();
    logger.info('Redis 연결이 종료되었습니다', {
        component: 'redis',
        status: 'closed'
    });

    // HTTP 서버 종료
    server.close(() => {
        logger.info('HTTP 서버가 종료되었습니다', {
            component: 'http',
            status: 'closed'
        });
        process.exit(0);
    });

    // 5초 후 강제 종료
    setTimeout(() => {
        logger.error('서버 강제 종료', {
            component: 'lifecycle',
            action: 'forced_shutdown'
        });
        process.exit(1);
    }, 5000);
};

// 종료 시그널 처리
process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// 서버 시작
startServer();

module.exports = {app, server, io, connectionManager, socketMonitor, pubSub};