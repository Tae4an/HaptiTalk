const jwt = require('jsonwebtoken');
const httpStatus = require('http-status');
const logger = require('../utils/logger');
const axios = require('axios');

/**
 * 인증 미들웨어
 * JWT 토큰 검증 및 사용자 정보 확인
 */
const authMiddleware = {
    /**
     * JWT 토큰 검증 미들웨어
     * @param {Object} req - 요청 객체
     * @param {Object} res - 응답 객체
     * @param {Function} next - 다음 미들웨어 호출 함수
     */
    verifyToken: async (req, res, next) => {
        try {
            // 헤더에서 Authorization 토큰 가져오기
            const authHeader = req.headers.authorization;

            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                return res.status(httpStatus.UNAUTHORIZED).json({
                    success: false,
                    message: '인증 토큰이 필요합니다.'
                });
            }

            // Bearer 접두어 제거
            const token = authHeader.split(' ')[1];

            if (!token) {
                return res.status(httpStatus.UNAUTHORIZED).json({
                    success: false,
                    message: '유효하지 않은.인증 토큰 형식입니다.'
                });
            }

            // JWT 토큰 검증
            try {
                // JWT_SECRET 대신 JWT_ACCESS_SECRET 사용
                const decoded = jwt.verify(token, process.env.JWT_ACCESS_SECRET || 'your-secret-key');
                
                // 사용자 정보 설정
                req.user = {
                    ...decoded,
                    id: decoded.sub  // sub 필드를 id로 설정
                };

                // 토큰의 사용자 ID를 사용해 추가 검증 수행 (선택 사항)
                // 마이크로서비스 환경에서는 auth-service에 검증 요청을 보낼 수 있음
                // 임시로 비활성화 - JWT 토큰 자체 검증만 사용
                /*
                if (process.env.NODE_ENV === 'production') {
                    try {
                        const response = await axios.get(
                            `http://${process.env.AUTH_SERVICE_HOST || 'auth-service'}:${process.env.AUTH_SERVICE_PORT || '3000'}/api/v1/auth/token/status`,
                            {
                                headers: {
                                    Authorization: `Bearer ${token}`
                                }
                            }
                        );

                        if (!response.data.success) {
                            throw new Error('토큰 검증에 실패했습니다.');
                        }
                    } catch (error) {
                        logger.error('Token validation error:', error);
                        return res.status(httpStatus.UNAUTHORIZED).json({
                            success: false,
                            message: '인증 서비스에서 토큰 검증에 실패했습니다.'
                        });
                    }
                }
                */

                next();
            } catch (error) {
                logger.error('JWT verification error:', error);

                if (error.name === 'TokenExpiredError') {
                    return res.status(httpStatus.UNAUTHORIZED).json({
                        success: false,
                        message: '인증 토큰이 만료되었습니다.'
                    });
                }

                return res.status(httpStatus.UNAUTHORIZED).json({
                    success: false,
                    message: '유효하지 않은 인증 토큰입니다.'
                });
            }
        } catch (error) {
            logger.error('Authentication middleware error:', error);

            return res.status(httpStatus.INTERNAL_SERVER_ERROR).json({
                success: false,
                message: '인증 처리 중 오류가 발생했습니다.'
            });
        }
    },

    /**
     * 서비스 간 통신을 위한 토큰 검증 미들웨어
     * @param {Object} req - Express 요청 객체 
     * @param {Object} res - Express 응답 객체
     * @param {Function} next - Express 다음 미들웨어 함수
     */
    validateServiceToken: (req, res, next) => {
        try {
            const authHeader = req.headers.authorization;
            
            if (!authHeader || !authHeader.startsWith('Bearer ')) {
                return res.status(httpStatus.UNAUTHORIZED).json({
                    success: false,
                    message: '인증 토큰이 필요합니다'
                });
            }
            
            const token = authHeader.split(' ')[1];
            
            // 환경 변수에서 서비스 토큰 가져오기
            const serviceToken = process.env.INTER_SERVICE_TOKEN || 'default-service-token';
            
            // 간단한 토큰 비교 (실제 환경에서는 더 안전한 방식 사용 권장)
            if (token !== serviceToken) {
                return res.status(httpStatus.FORBIDDEN).json({
                    success: false,
                    message: '유효하지 않은 서비스 토큰입니다'
                });
            }
            
            // 서비스 요청임을 표시
            req.isServiceRequest = true;
            req.service = {
                name: 'realtime-service' // 기본값
            };
            
            next();
        } catch (error) {
            logger.error(`서비스 토큰 검증 오류: ${error.message}`);
            return res.status(httpStatus.INTERNAL_SERVER_ERROR).json({
                success: false,
                message: '인증 처리 중 오류가 발생했습니다'
            });
        }
    }
};

module.exports = authMiddleware;