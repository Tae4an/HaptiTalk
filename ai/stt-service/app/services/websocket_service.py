import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Awaitable
import numpy as np
import whisperx
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import httpx

from app.core.logging import logger
from app.core.config import settings
from app.services.stt_service import stt_processor

# WhisperX 3.3.4에서는 whisperx.audio 모듈이 제거되었으므로 직접 상수 정의

async def call_emotion_analysis(audio_bytes: bytes, scenario: str, language: str) -> Optional[Dict[str, Any]]:
    """
    감정분석 서비스 호출
    
    Args:
        audio_bytes: 오디오 바이너리 데이터
        scenario: 시나리오 (dating, interview, presentation)
        language: 언어 코드
        
    Returns:
        감정분석 결과 또는 None (실패 시)
    """
    try:
        emotion_service_url = "http://210.119.33.7:8621/api/v1/emotion/analyze_bytes"
        
        params = {
            "scenario": scenario,
            "language": language,
            "apply_scenario_weights": True,
            "top_k": 6  # 모든 감정 반환 (6개 모든 감정 라벨)
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:  # 타임아웃 30초로 증가
            response = await client.post(
                emotion_service_url,
                content=audio_bytes,
                params=params,
                headers={"Content-Type": "application/octet-stream"}
            )
            
            if response.status_code == 200:
                emotion_result = response.json()
                logger.debug(f"감정분석 완료 - 주 감정: {emotion_result['primary_emotion']['emotion_kr']} ({emotion_result['primary_emotion']['probability']:.3f})")
                return emotion_result
            else:
                logger.warning(f"감정분석 서비스 오류: HTTP {response.status_code}")
                return None
                
    except httpx.TimeoutException:
        logger.warning("감정분석 서비스 호출 시간 초과")
        return None
    except httpx.ConnectError:
        logger.warning("감정분석 서비스에 연결할 수 없습니다 (포트 8001)")
        return None
    except Exception as e:
        logger.warning(f"감정분석 서비스 호출 중 오류: {str(e)}")
        return None


def calculate_segment_based_metrics(
    segments_list: list,
    audio_duration: float,
    scenario: str = "presentation",
    language: str = "ko"
) -> Dict[str, Any]:
    """
    세그먼트별 말하기 속도 및 관련 메트릭 계산
    
    Returns:
        - segment_wpm_list: 각 세그먼트의 WPM
        - average_segment_wpm: 세그먼트 WPM의 평균
        - median_segment_wpm: 세그먼트 WPM의 중앙값
        - pause_metrics: pause 관련 메트릭
        - speech_pattern: 말하기 패턴 분석
    """
    if not segments_list or audio_duration <= 0:
        return {
            "segment_wpm_list": [],
            "average_segment_wpm": 0,
            "median_segment_wpm": 0,
            "wpm_active": 0,
            "wpm_total": 0,
            "speech_density": 0,
            "pause_metrics": {},
            "speech_pattern": "no_data",
            "speed_category": "no_data"
        }
    
    # 1. 세그먼트별 WPM 계산
    segment_metrics = []
    total_word_count = 0
    total_speech_duration = 0
    pause_durations = []
    
    for i, segment in enumerate(segments_list):
        if hasattr(segment, 'start') and hasattr(segment, 'end'):
            segment_duration = segment.end - segment.start
            
            # 단어 수 계산
            word_count = 0
            if hasattr(segment, 'words') and segment.words:
                word_count = len(segment.words)
            elif hasattr(segment, 'text'):
                # words가 없는 경우 텍스트 기반 추정
                word_count = len(segment.text.split())
            
            total_word_count += word_count
            total_speech_duration += segment_duration
            
            # 세그먼트 WPM 계산
            segment_wpm = (word_count / segment_duration * 60) if segment_duration > 0 else 0
            
            segment_metrics.append({
                "index": i,
                "text": segment.text if hasattr(segment, 'text') else "",
                "start": segment.start,
                "end": segment.end,
                "duration": segment_duration,
                "word_count": word_count,
                "wpm": segment_wpm,
                "spm": count_syllables(segment.text, language) / segment_duration * 60 if segment_duration > 0 else 0
            })
            
            # Pause 계산 (다음 세그먼트와의 간격)
            if i < len(segments_list) - 1:
                next_segment = segments_list[i + 1]
                if hasattr(next_segment, 'start'):
                    pause = next_segment.start - segment.end
                    if pause > 0:
                        pause_durations.append(pause)
    
    # 2. 세그먼트 WPM 통계
    segment_wpm_list = [m["wpm"] for m in segment_metrics if m["wpm"] > 0]
    
    if segment_wpm_list:
        average_segment_wpm = sum(segment_wpm_list) / len(segment_wpm_list)
        median_segment_wpm = sorted(segment_wpm_list)[len(segment_wpm_list) // 2]
        wpm_std = (sum((w - average_segment_wpm) ** 2 for w in segment_wpm_list) / len(segment_wpm_list)) ** 0.5
        wpm_cv = wpm_std / average_segment_wpm if average_segment_wpm > 0 else 0
    else:
        average_segment_wpm = median_segment_wpm = wpm_std = wpm_cv = 0
    
    # 3. 기존 메트릭 호환성 (wpm_active, wpm_total)
    wpm_active = (total_word_count / total_speech_duration * 60) if total_speech_duration > 0 else 0
    wpm_total = (total_word_count / audio_duration * 60) if audio_duration > 0 else 0
    
    # 4. 발화 밀도
    speech_density = total_speech_duration / audio_duration if audio_duration > 0 else 0
    
    # 5. Pause 분석
    if pause_durations:
        pause_metrics = {
            "count": len(pause_durations),
            "total_duration": sum(pause_durations),
            "average_duration": sum(pause_durations) / len(pause_durations),
            "max_duration": max(pause_durations),
            "min_duration": min(pause_durations),
            "pause_ratio": sum(pause_durations) / audio_duration,
            # 기존 호환성
            "avg_duration": sum(pause_durations) / len(pause_durations)
        }
        
        # Pause 패턴 분류
        avg_pause = pause_metrics["average_duration"]
        if avg_pause < 0.5:
            pause_pattern = "very_short"
        elif avg_pause < 1.0:
            pause_pattern = "short"
        elif avg_pause < 2.0:
            pause_pattern = "normal"
        elif avg_pause < 3.0:
            pause_pattern = "long"
        else:
            pause_pattern = "very_long"
    else:
        pause_metrics = {
            "count": 0,
            "total_duration": 0,
            "average_duration": 0,
            "max_duration": 0,
            "min_duration": 0,
            "pause_ratio": 0,
            # 기존 호환성
            "avg_duration": 0
        }
        pause_pattern = "no_pause"
    
    # 6. 말하기 패턴 분석
    speech_pattern = analyze_speech_pattern(
        speech_density,
        pause_pattern,
        wpm_cv,
        average_segment_wpm,
        pause_metrics.get("pause_ratio", 0)
    )
    
    # 7. 속도 카테고리 결정 (세그먼트 평균 기준)
    thresholds = settings.SCENARIO_SPEED_THRESHOLDS.get(scenario, {}).get(
        language, 
        settings.SCENARIO_SPEED_THRESHOLDS["presentation"]["ko"]
    )
    
    # 평가 기준 선택
    if speech_pattern in ["staccato", "very_sparse"]:
        # 끊어 말하기 패턴일 경우 중앙값 사용
        evaluation_wpm = median_segment_wpm
    else:
        # 일반적인 경우 평균 사용
        evaluation_wpm = average_segment_wpm
    
    # 속도 카테고리
    if evaluation_wpm < thresholds["very_slow"]:
        speed_category = "very_slow"
    elif evaluation_wpm < thresholds["slow"]:
        speed_category = "slow"
    elif evaluation_wpm < thresholds["normal"]:
        speed_category = "normal"
    elif evaluation_wpm < thresholds["fast"]:
        speed_category = "fast"
    else:
        speed_category = "very_fast"
    
    return {
        # 세그먼트 정보
        "segment_metrics": segment_metrics,
        "segment_wpm_list": segment_wpm_list,
        "average_segment_wpm": round(average_segment_wpm, 2),
        "median_segment_wpm": round(median_segment_wpm, 2),
        "wpm_std": round(wpm_std, 2),
        "wpm_cv": round(wpm_cv, 3),
        # 기존 호환성 메트릭
        "wpm_active": round(wpm_active, 2),
        "wpm_total": round(wpm_total, 2),
        "evaluation_wpm": round(evaluation_wpm, 2),
        "word_count": total_word_count,
        "speech_duration": round(total_speech_duration, 2),
        "total_duration": round(audio_duration, 2),
        "speech_density": round(speech_density, 3),
        # Pause 메트릭
        "pause_metrics": pause_metrics,
        "pause_pattern": pause_pattern,
        # 패턴 및 평가
        "speech_pattern": speech_pattern,
        "speed_category": speed_category
    }


def analyze_speech_pattern(
    speech_density: float,
    pause_pattern: str,
    wpm_cv: float,
    average_wpm: float,
    pause_ratio: float
) -> str:
    """말하기 패턴 분석"""
    
    # 1. 매우 긴 pause가 많은 경우
    if pause_ratio > 0.5:
        return "very_sparse"  # 매우 띄엄띄엄
    
    # 2. 짧은 문장 + 긴 pause 패턴
    if pause_pattern in ["long", "very_long"] and speech_density < 0.6:
        return "staccato"  # 끊어 말하기
    
    # 3. 연속적인 발화
    if speech_density > 0.8 and pause_pattern in ["very_short", "short", "no_pause"]:
        return "continuous"  # 연속적
    
    # 4. 일정한 속도의 발화
    if wpm_cv < 0.2:
        return "steady"  # 일정한 속도
    
    # 5. 변화가 큰 발화
    if wpm_cv > 0.4:
        return "variable"  # 속도 변화 큼
    
    # 6. 기본
    return "normal"  # 일반적


# 기존 호환성을 위한 별칭 (구 함수명 유지)
def calculate_speech_metrics(
    segments_list: list,
    audio_duration: float,
    scenario: str = "presentation",
    language: str = "ko"
) -> Dict[str, Any]:
    """기존 호환성을 위한 래퍼 함수"""
    result = calculate_segment_based_metrics(segments_list, audio_duration, scenario, language)
    
    # 기존 형식으로 변환
    return {
        "wpm_active": result["wpm_active"],
        "wpm_total": result["wpm_total"],
        "evaluation_wpm": result["evaluation_wpm"],
        "word_count": result["word_count"],
        "speech_duration": result["speech_duration"],
        "total_duration": result["total_duration"],
        "speech_density": result["speech_density"],
        "pause_pattern": result["pause_metrics"],
        "speed_category": result["speed_category"],
        # 새로운 메트릭 추가
        "segment_metrics": result["segment_metrics"],
        "average_segment_wpm": result["average_segment_wpm"],
        "median_segment_wpm": result["median_segment_wpm"],
        "speech_pattern": result["speech_pattern"]
    }


def count_syllables(text: str, language: str) -> int:
    """언어별 음절 수 계산"""
    if language == "ko":
        # 한글 음절 수 (공백 제외)
        return len([char for char in text if '가' <= char <= '힣'])
    elif language == "ja":
        # 일본어: 히라가나, 가타카나, 한자
        return len([char for char in text if (
            '\u3040' <= char <= '\u309F' or  # 히라가나
            '\u30A0' <= char <= '\u30FF' or  # 가타카나
            '\u4E00' <= char <= '\u9FAF'     # 한자
        )])
    elif language == "zh":
        # 중국어: 한자
        return len([char for char in text if '\u4E00' <= char <= '\u9FAF'])
    else:
        # 영어 등: 대략적인 음절 수 (모음 기준)
        vowels = "aeiouAEIOU"
        return sum(1 for char in text if char in vowels)


def calculate_speech_variability(segments_list: list) -> Dict[str, float]:
    """세그먼트 간 속도 변동성 계산"""
    if not segments_list or len(segments_list) < 2:
        return {"cv": 0, "std": 0, "mean": 0}
    
    segment_speeds = []
    for segment in segments_list:
        if hasattr(segment, 'words') and segment.words and hasattr(segment, 'start') and hasattr(segment, 'end'):
            duration = segment.end - segment.start
            if duration > 0:
                wpm = len(segment.words) / duration * 60
                segment_speeds.append(wpm)
    
    if not segment_speeds:
        return {"cv": 0, "std": 0, "mean": 0}
    
    mean_speed = sum(segment_speeds) / len(segment_speeds)
    variance = sum((s - mean_speed) ** 2 for s in segment_speeds) / len(segment_speeds)
    std_speed = variance ** 0.5
    cv = std_speed / mean_speed if mean_speed > 0 else 0
    
    return {
        "cv": round(cv, 3),           # 변동계수
        "std": round(std_speed, 2),    # 표준편차
        "mean": round(mean_speed, 2)   # 평균
    }


class ConnectionManager:
    """
    WebSocket 연결 관리 클래스
    """
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket) -> str:
        """
        새 WebSocket 연결 수립
        
        Args:
            websocket: WebSocket 인스턴스
            
        Returns:
            생성된 연결 ID
        """
        # 고유 연결 ID 생성
        connection_id = str(uuid.uuid4())
        
        # 연결 수락
        await websocket.accept()
        
        # 활성 연결에 추가
        self.active_connections[connection_id] = websocket
        
        logger.info(f"WebSocket 연결 수립: {connection_id}")
        return connection_id
    
    def disconnect(self, connection_id: str) -> None:
        """
        WebSocket 연결 종료
        
        Args:
            connection_id: 연결 ID
        """
        if connection_id in self.active_connections:
            logger.info(f"WebSocket 연결 종료: {connection_id}")
            del self.active_connections[connection_id]
    
    async def send_text(self, connection_id: str, message: str) -> None:
        """
        텍스트 메시지 전송
        
        Args:
            connection_id: 연결 ID
            message: 전송할 텍스트 메시지
        """
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message)
                else:
                    logger.warning(f"연결이 닫힌 상태입니다: {connection_id}")
                    self.disconnect(connection_id)
            except Exception as e:
                logger.error(f"메시지 전송 실패: {connection_id} - {str(e)}")
                self.disconnect(connection_id)
    
    async def send_json(self, connection_id: str, data: Dict[str, Any]) -> None:
        """
        JSON 메시지 전송
        
        Args:
            connection_id: 연결 ID
            data: 전송할 JSON 데이터
        """
        if connection_id in self.active_connections:
            try:
                await self.send_text(connection_id, json.dumps(data))
            except Exception as e:
                logger.error(f"JSON 메시지 전송 실패: {connection_id} - {str(e)}")
                self.disconnect(connection_id)


class STTWebSocketManager:
    """
    STT 웹소켓 관리 클래스
    """
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        
    async def _initialize_session(self, connection_id: str, language: str, scenario: str = "presentation") -> None:
        """
        WebSocket 세션 초기화
        
        Args:
            connection_id: 연결 ID
            language: 인식 언어
            scenario: 시나리오 타입 (dating, interview, presentation)
        """
        logger.info(f"WebSocket 세션 초기화 시작: {connection_id}, 언어: {language}, 시나리오: {scenario}")
        self.sessions[connection_id] = {
            "buffer": bytearray(),
            "last_chunk_time": time.time(),
            "is_processing": False,
            "language": language,
            "scenario": scenario,
            "segment_count": 0,
            "last_transcription": "",
            "is_first_segment": True,
            "is_recording": False  # 초기에는 False로 설정
        }
        logger.info(f"WebSocket 세션 초기화 완료: {connection_id}, 초기 녹음 상태: {self.sessions[connection_id]['is_recording']}")
    
    async def _load_model_if_needed(self, connection_id: str) -> bool:
        """
        필요한 경우 STT 모델 로드
        
        Args:
            connection_id: 연결 ID
            
        Returns:
            모델 로드 성공 여부
        """
        if stt_processor.model is None:
            logger.info("WhisperX 모델 로딩 시작...")
            try:
                await stt_processor.load_model()
                logger.info("WhisperX 모델 로딩 완료")
                return True
            except Exception as e:
                await self.connection_manager.send_json(connection_id, {
                    "type": "error",
                    "message": f"모델 로딩 실패: {str(e)}"
                })
                return False
        else:
            logger.info("WhisperX 모델이 이미 로드되어 있습니다.")
            return True
    
    async def _handle_text_message(self, connection_id: str, text_data: str) -> bool:
        """
        텍스트 메시지 처리
        
        Args:
            connection_id: 연결 ID
            text_data: 수신된 텍스트 데이터
            
        Returns:
            계속 처리해야 하는지 여부
        """
        if connection_id not in self.sessions:
            return False
            
        try:
            # 언어 변경 명령 처리 (예: "language:en")
            if text_data.startswith("language:"):
                new_language = text_data.split(":", 1)[1]
                old_language = self.sessions[connection_id]["language"]
                self.sessions[connection_id]["language"] = new_language
                self.sessions[connection_id]["is_first_segment"] = True
                
                logger.info(f"언어 변경: {connection_id} - {old_language} -> {new_language}")
                
                await self.connection_manager.send_json(connection_id, {
                    "type": "language_changed",
                    "language": new_language,
                    "message": f"인식 언어가 변경되었습니다: {new_language}"
                })
                return True
                
            # JSON 명령 처리
            try:
                data = json.loads(text_data)
                
                if "command" in data:
                    command = data["command"]
                    
                    # 녹음 시작 명령
                    if command == "start_recording":
                        logger.info(f"녹음 시작 요청 수신: {connection_id}")
                        session = self.sessions[connection_id]
                        old_state = session.get("is_recording", False)
                        session["is_recording"] = True
                        
                        logger.info(f"녹음 상태 변경: {connection_id}, {old_state} -> {session['is_recording']}")
                        
                        await self.connection_manager.send_json(connection_id, {
                            "type": "recording_started",
                            "message": "녹음이 시작되었습니다."
                        })
                        return True
                    
                    # 녹음 중지 명령
                    elif command == "stop_recording":
                        logger.info(f"녹음 중지 요청 수신: {connection_id}")
                        session = self.sessions[connection_id]
                        old_state = session.get("is_recording", False)
                        
                        # 버퍼에 남은 데이터 최종 처리 (녹음 상태 변경 전에)
                        if len(session["buffer"]) > 0:
                            logger.info(f"녹음 중지 시 남은 버퍼 데이터 처리: {connection_id}, 버퍼 크기: {len(session['buffer'])} bytes")
                            await self._process_audio_buffer(connection_id, is_final=True)
                        else:
                            logger.info(f"녹음 중지 시 처리할 버퍼 데이터 없음: {connection_id}")
                        
                        session["is_recording"] = False
                        logger.info(f"녹음 상태 변경: {connection_id}, {old_state} -> {session['is_recording']}")
                        
                        await self.connection_manager.send_json(connection_id, {
                            "type": "recording_stopped",
                            "message": "녹음이 중지되었습니다."
                        })
                        return True
                    
                    # 최종 처리 명령
                    elif command == "process_final":
                        logger.info(f"최종 처리 요청 수신: {connection_id}")
                        await self._process_audio_buffer(connection_id, is_final=True)
                        logger.info(f"최종 처리 완료: {connection_id}")
                        
                        await self.connection_manager.send_json(connection_id, {
                            "type": "processing_complete",
                            "message": "오디오 처리가 완료되었습니다."
                        })
                        return True
                    
                    # 언어 설정 명령
                    elif command == "set_language" and "language" in data:
                        new_language = data["language"]
                        old_language = self.sessions[connection_id]["language"]
                        self.sessions[connection_id]["language"] = new_language
                        self.sessions[connection_id]["is_first_segment"] = True
                        
                        logger.info(f"언어 변경: {connection_id} - {old_language} -> {new_language}")
                        
                        await self.connection_manager.send_json(connection_id, {
                            "type": "language_changed",
                            "language": new_language,
                            "message": f"인식 언어가 변경되었습니다: {new_language}"
                        })
                        return True
                    
                    # 버퍼 초기화 명령
                    elif command == "reset":
                        session = self.sessions[connection_id]
                        session["buffer"] = bytearray()
                        session["segment_count"] = 0
                        session["last_transcription"] = ""
                        session["is_first_segment"] = True
                        
                        logger.info(f"버퍼 초기화: {connection_id}")
                        
                        await self.connection_manager.send_json(connection_id, {
                            "type": "reset_complete",
                            "message": "버퍼가 초기화되었습니다."
                        })
                        return True
                
            except json.JSONDecodeError:
                # 유효하지 않은 JSON 형식
                logger.warning(f"잘못된 JSON 형식: {connection_id} - {text_data}")
        except Exception as e:
            logger.error(f"텍스트 메시지 처리 오류: {connection_id} - {str(e)}")
            await self.connection_manager.send_json(connection_id, {
                "type": "error",
                "message": f"메시지 처리 오류: {str(e)}"
            })
        
        return True
    
    async def _handle_binary_message(self, connection_id: str, binary_data: bytes) -> bool:
        """
        바이너리 메시지 처리
        
        Args:
            connection_id: 연결 ID
            binary_data: 수신된 바이너리 데이터
            
        Returns:
            계속 처리해야 하는지 여부
        """
        if connection_id not in self.sessions:
            logger.warning(f"알 수 없는 연결 ID로 바이너리 데이터 수신: {connection_id}")
            return False
            
        session = self.sessions[connection_id]
        
        # 바이너리 데이터 수신 로그 (항상 기록)
        logger.info(f"바이너리 데이터 수신: {connection_id}, 크기: {len(binary_data)} bytes")
        
        # 녹음 상태가 아니면 오디오 데이터 무시하지만 로그는 남김
        if not session.get("is_recording", False):
            logger.warning(f"녹음 상태가 아니므로 오디오 데이터 무시: {connection_id}, 현재 녹음 상태: {session.get('is_recording', 'None')}")
            # 자동으로 녹음 상태를 True로 설정 (웹 클라이언트 호환성)
            logger.info(f"자동으로 녹음 상태를 활성화: {connection_id}")
            session["is_recording"] = True
        
        # 데이터 버퍼에 추가
        session["buffer"].extend(binary_data)
        session["last_chunk_time"] = time.time()
        
        logger.info(f"오디오 데이터 버퍼에 추가: {connection_id}, 추가된 크기: {len(binary_data)} bytes, 현재 버퍼 크기: {len(session['buffer'])} bytes")
        
        # 버퍼 크기 확인 및 처리
        # 30초 분량의 오디오 데이터 (16kHz, 16-bit, mono = 2바이트 * 16000 * 30 = 960,000바이트)
        buffer_threshold = min(settings.DEFAULT_BUFFER_SIZE, settings.MAX_AUDIO_BUFFER_MB * 1024 * 1024)
        
        if len(session["buffer"]) >= buffer_threshold and not session["is_processing"]:
            logger.info(f"버퍼 임계값 도달, 처리 시작: {connection_id}, 임계값: {buffer_threshold}, 현재 크기: {len(session['buffer'])}")
            # 병렬로 처리
            asyncio.create_task(self._process_audio_buffer(connection_id))
        
        return True
        
    async def handle_connection(self, websocket: WebSocket, language: str = "ko", scenario: str = "presentation") -> None:
        """
        WebSocket 연결 처리
        
        Args:
            websocket: WebSocket 연결
            language: 인식 언어
            scenario: 시나리오 타입 (dating, interview, presentation)
        """
        connection_id = await self.connection_manager.connect(websocket)
        
        # 세션 초기화
        await self._initialize_session(connection_id, language, scenario)
        
        try:
            # STT 모델 로드 확인
            if not await self._load_model_if_needed(connection_id):
                return
                
            # 환영 메시지 전송
            await self.connection_manager.send_json(connection_id, {
                "type": "connected",
                "message": "STT 서비스에 연결되었습니다. 오디오 데이터를 전송해주세요.",
                "connection_id": connection_id
            })
            
            # 메시지 수신 대기
            while True:
                try:
                    # WebSocket 연결 상태 확인
                    if websocket.client_state == WebSocketState.DISCONNECTED:
                        logger.info(f"WebSocket이 이미 연결 해제됨: {connection_id}")
                        break
                    
                    logger.debug(f"WebSocket 메시지 수신 대기 중: {connection_id}")
                    # 메시지 수신
                    message = await websocket.receive()
                    logger.debug(f"WebSocket 메시지 수신: {connection_id}, 타입: {'text' if 'text' in message else 'bytes'}")
                    
                    # 텍스트 메시지인 경우 (명령)
                    if "text" in message:
                        if not await self._handle_text_message(connection_id, message["text"]):
                            break
                    
                    # 바이너리 메시지인 경우 (오디오 데이터)
                    elif "bytes" in message:
                        if not await self._handle_binary_message(connection_id, message["bytes"]):
                            break
                
                except WebSocketDisconnect:
                    # 연결이 종료된 경우
                    logger.info(f"WebSocket 연결 종료됨: {connection_id}")
                    break
                except RuntimeError as e:
                    if "disconnect message has been received" in str(e):
                        logger.info(f"WebSocket 연결이 이미 종료됨: {connection_id}")
                        break
                    else:
                        logger.error(f"런타임 에러 발생: {connection_id} - {str(e)}", exc_info=True)
                        break
                except Exception as e:
                    # 기타 예외 처리
                    logger.error(f"메시지 수신 중 오류 발생: {connection_id} - {str(e)}", exc_info=True)
                    # 오류 메시지 전송 시도 (연결이 유효한 경우에만)
                    try:
                        if websocket.client_state == WebSocketState.CONNECTED:
                            await self.connection_manager.send_json(connection_id, {
                                "type": "error",
                                "message": f"오류가 발생했습니다: {str(e)}"
                            })
                    except:
                        # 오류 메시지 전송 실패시 로그만 남기고 계속 진행
                        logger.warning(f"오류 메시지 전송 실패: {connection_id}")
                    break
        
        finally:
            # 세션 정리
            if connection_id in self.sessions:
                del self.sessions[connection_id]
            
            # 연결 종료
            self.connection_manager.disconnect(connection_id)
    
    async def _process_audio_buffer(self, connection_id: str, is_final: bool = False) -> None:
        """
        오디오 버퍼 처리
        
        Args:
            connection_id: 연결 ID
            is_final: 최종 처리 여부
        """
        if connection_id not in self.sessions:
            return
        
        session = self.sessions[connection_id]
        
        # 이미 처리 중인 경우 반환
        logger.info(f"오디오 버퍼 처리 시작: {connection_id}, 최종 처리: {is_final}, 현재 버퍼 크기: {len(session['buffer'])} bytes")
        if session["is_processing"]:
            logger.warning(f"이미 처리 중이므로 건너뛰었습니다: {connection_id}")
            return
        
        # 처리 중 플래그 설정
        session["is_processing"] = True
        
        try:
            # 버퍼에 데이터가 있는지 확인
            if len(session["buffer"]) == 0:
                session["is_processing"] = False
                logger.info(f"처리할 오디오 데이터 없음: {connection_id}")
                return
            
            # 버퍼에서 데이터 가져오기
            if is_final:
                # 최종 처리인 경우 모든 데이터 사용
                audio_data = bytes(session["buffer"])
                session["buffer"] = bytearray()
            else:
                # 일부 처리인 경우 버퍼 앞부분 사용
                buffer_size = len(session["buffer"])
                use_size = min(buffer_size, settings.MAX_AUDIO_BUFFER_MB * 1024 * 1024)
                
                audio_data = bytes(session["buffer"][:use_size])
                session["buffer"] = session["buffer"][use_size:]
                
            try:
                # 바이너리 데이터를 numpy 배열로 변환
                # 16-bit PCM, 단일 채널 오디오 가정
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                logger.info(f"오디오 데이터 NumPy 배열로 변환 완료: {connection_id}, 배열 크기: {audio_np.shape}, 오디오 길이: {len(audio_np) / settings.SAMPLE_RATE:.2f}초")
                
                # 오디오 데이터가 충분한지 확인
                if len(audio_np) < 512:  # 너무 짧은 오디오는 처리하지 않음
                    session["is_processing"] = False
                    return
                    
                # WhisperX 처리
                segment_id = session["segment_count"]
                session["segment_count"] += 1
                
                # 실제 STT 처리
                if stt_processor.model is not None:
                    try:
                        # 시나리오별 transcribe 파라미터 준비
                        scenario = session.get("scenario", "presentation")
                        vad_params = settings.SCENARIO_VAD_PARAMS.get(scenario, settings.TRANSCRIBE_PARAMS["vad_parameters"])
                        
                        transcribe_params = {
                            "language": session["language"],
                            "beam_size": 5 if scenario != "interview" else 10,  # 면접은 더 정확하게
                            "word_timestamps": True,  # 실시간 처리에서는, 단어 타임스탬프가 필요
                            "vad_filter": settings.TRANSCRIBE_PARAMS.get("vad_filter", True),
                            "task": settings.TRANSCRIBE_PARAMS.get("task", "transcribe"),
                            "condition_on_previous_text": settings.TRANSCRIBE_PARAMS.get("condition_on_previous_text", True),
                            "vad_parameters": vad_params
                        }
                        
                        # 이전 인식 결과를 초기 프롬프트로 사용하여 연속성 보장
                        if session["last_transcription"]:
                            transcribe_params["initial_prompt"] = session["last_transcription"]
                        
                        logger.debug(f"WebSocket Transcribe 매개변수: {transcribe_params}")
                        
                        # 타임아웃 설정 - 10초 이상 걸리면 취소
                        segments, info = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(None, lambda: stt_processor.model.transcribe(
                                audio_np, **transcribe_params
                            )),
                            timeout=10
                        )
                        logger.info(f"WebSocket 모델 추론 완료: {connection_id}, 감지된 언어: {info.language}, 확률: {info.language_probability:.2f}")
                        
                        # 결과 수집 및 후처리
                        segments_list = list(segments)
                        
                        # 결과 텍스트 추출
                        text = ""
                        for segment in segments_list:
                            if hasattr(segment, 'text'):
                                text += segment.text + " "
                        
                        text = text.strip()
                        
                        if not text:
                            session["is_processing"] = False
                            return
                        
                        # 현재 인식 결과 저장 (다음 세그먼트의 프롬프트로 사용)
                        session["last_transcription"] = text
                        
                        # 시나리오와 언어 정보
                        scenario = session.get("scenario", "presentation")
                        detected_language = info.language if hasattr(info, 'language') else session["language"]
                        
                        # 세그먼트 기반 말하기 속도 메트릭 계산
                        speech_metrics = calculate_segment_based_metrics(
                            segments_list,
                            len(audio_np) / settings.SAMPLE_RATE,
                            scenario,
                            detected_language
                        )
                        
                        # 음절 기반 메트릭 추가 (선택적)
                        syllable_metrics = None
                        if detected_language in ["ko", "ja", "zh"] and text:
                            syllable_count = count_syllables(text, detected_language)
                            spm_active = (syllable_count / speech_metrics["speech_duration"] * 60) if speech_metrics["speech_duration"] > 0 else 0
                            spm_total = (syllable_count / speech_metrics["total_duration"] * 60) if speech_metrics["total_duration"] > 0 else 0
                            
                            syllable_metrics = {
                                "syllable_count": syllable_count,
                                "spm_active": round(spm_active, 2),
                                "spm_total": round(spm_total, 2)
                            }
                        
                        # 속도 변동성 계산
                        variability_metrics = calculate_speech_variability(segments_list)
                        
                        # 감정분석 서비스 호출 (병렬 처리)
                        emotion_result = None
                        try:
                            # 오디오 바이트 데이터로 변환 (16-bit PCM으로 다시 변환)
                            audio_bytes = (audio_np * 32768.0).astype(np.int16).tobytes()
                            emotion_result = await call_emotion_analysis(audio_bytes, scenario, detected_language)
                        except Exception as e:
                            logger.warning(f"감정분석 서비스 호출 실패: {str(e)}")
                        
                        # 결과 전송
                        try:
                            result_data = {
                                "type": "transcription",
                                "text": text,
                                "is_final": is_final,
                                "segment_id": segment_id,
                                "scenario": scenario,
                                "language": detected_language,
                                "language_probability": info.language_probability,
                                # 말하기 속도 메트릭
                                "speech_metrics": {
                                    # 주요 지표
                                    "evaluation_wpm": speech_metrics["evaluation_wpm"],
                                    "speed_category": speech_metrics["speed_category"],
                                    "speech_pattern": speech_metrics["speech_pattern"],
                                    # 세그먼트 통계
                                    "average_segment_wpm": speech_metrics["average_segment_wpm"],
                                    "median_segment_wpm": speech_metrics["median_segment_wpm"],
                                    "wpm_cv": speech_metrics["wpm_cv"],
                                    # 전체 메트릭
                                    "wpm_active": speech_metrics["wpm_active"],
                                    "wpm_total": speech_metrics["wpm_total"],
                                    "speech_density": speech_metrics["speech_density"],
                                    # Pause 정보
                                    "pause_metrics": speech_metrics["pause_metrics"],
                                    "pause_pattern": speech_metrics["pause_pattern"]
                                },
                                # 속도 변동성 메트릭
                                "variability_metrics": variability_metrics,
                                # 음절 메트릭 (있는 경우)
                                "syllable_metrics": syllable_metrics,
                                # 세그먼트 상세 정보
                                "segments": speech_metrics["segment_metrics"]
                            }
                            
                            # 감정분석 결과 추가
                            if emotion_result:
                                result_data["emotion_analysis"] = {
                                    "primary_emotion": emotion_result["primary_emotion"],
                                    "top_emotions": emotion_result["top_emotions"],
                                    "scenario_applied": emotion_result["scenario_applied"],
                                    "processing_time": emotion_result["processing_time"],
                                    "model_used": emotion_result["model_used"]
                                }
                                logger.info(f"감정분석 결과 포함 - 주 감정: {emotion_result['primary_emotion']['emotion_kr']} ({emotion_result['primary_emotion']['probability']:.3f})")
                            else:
                                result_data["emotion_analysis"] = None
                                logger.debug("감정분석 결과 없음")
                            
                            # 단어 수준 타임스탬프 정보 추가
                            words_with_timestamps = []
                            for segment in segments_list:
                                if hasattr(segment, 'words') and segment.words:
                                    for word in segment.words:
                                        words_with_timestamps.append({
                                            "word": word.word,
                                            "start": word.start,
                                            "end": word.end,
                                            "probability": word.probability
                                        })
                            
                            if words_with_timestamps:
                                result_data["words"] = words_with_timestamps
                            
                            await self.connection_manager.send_json(connection_id, result_data)

                            # 상세 로깅 추가
                            logger.info(f"말하기 속도 분석 (시나리오: {scenario}):")
                            logger.info(f"  - 텍스트: {text[:50]}...")
                            logger.info(f"  - 언어: {detected_language}")
                            logger.info(f"  - 세그먼트 평균 WPM: {speech_metrics['average_segment_wpm']}")
                            logger.info(f"  - 세그먼트 중앙값 WPM: {speech_metrics['median_segment_wpm']}")
                            logger.info(f"  - 전체 시간 WPM: {speech_metrics['wpm_total']}")
                            logger.info(f"  - 평가 WPM: {speech_metrics['evaluation_wpm']}")
                            logger.info(f"  - 발화 밀도: {speech_metrics['speech_density']:.1%}")
                            logger.info(f"  - 속도 카테고리: {speech_metrics['speed_category']}")
                            logger.info(f"  - 말하기 패턴: {speech_metrics['speech_pattern']}")
                            logger.info(f"  - Pause 패턴: {speech_metrics['pause_pattern']}")
                            logger.info(f"  - 평균 Pause: {speech_metrics['pause_metrics'].get('average_duration', 0):.2f}초")
                            logger.info(f"  - 세그먼트 수: {len(segments_list)}")
                            
                            if syllable_metrics:
                                logger.info(f"  - SPM (발화): {syllable_metrics['spm_active']}")
                                logger.info(f"  - SPM (전체): {syllable_metrics['spm_total']}")
                            
                            # 처음 3개 세그먼트만 상세 로그
                            for i, seg in enumerate(speech_metrics["segment_metrics"][:3]):
                                logger.info(f"    Segment {i+1}: WPM={seg['wpm']:.1f}, Duration={seg['duration']:.2f}s, Text='{seg['text'][:30]}...')")
                            
                            if result_data.get("words"):
                                 logger.info(f"  - 단어 타임스탬프 수: {len(result_data['words'])}")

                            # 전체 JSON 응답은 DEBUG 레벨로 유지 (필요시 활성화)
                            logger.debug(f"  - 전체 전송 JSON: {json.dumps(result_data, ensure_ascii=False, indent=2)}")
                            logger.info(f"STT 결과 전송 완료: {connection_id}")

                        except (RuntimeError, WebSocketDisconnect) as e:
                            logger.info(f"결과 전송 중 연결 종료: {connection_id} - {str(e)}")
                            return
                                
                    except asyncio.TimeoutError:
                        # 처리 시간 초과
                        logger.warning(f"오디오 처리 시간 초과: {connection_id}")
                        try:
                            await self.connection_manager.send_json(connection_id, {
                                "type": "error",
                                "message": "오디오 처리 시간이 초과되었습니다."
                            })
                        except:
                            pass
                    except Exception as e:
                        # 기타 오류
                        logger.error(f"오디오 처리 중 오류 발생: {connection_id} - {str(e)}", exc_info=True)
                        try:
                            await self.connection_manager.send_json(connection_id, {
                                "type": "error",
                                "message": f"오디오 처리 중 오류 발생: {str(e)}"
                            })
                        except:
                            pass
                else:
                    logger.error(f"STT 모델이 초기화되지 않았습니다: {connection_id}")
                    try:
                        await self.connection_manager.send_json(connection_id, {
                            "type": "error",
                            "message": "STT 모델이 초기화되지 않았습니다."
                        })
                    except:
                        pass
            except Exception as e:
                logger.error(f"오디오 데이터 변환 중 오류 발생: {connection_id} - {str(e)}", exc_info=True)
                try:
                    await self.connection_manager.send_json(connection_id, {
                        "type": "error",
                        "message": f"오디오 데이터 변환 중 오류 발생: {str(e)}"
                    })
                except:
                    pass
        finally:
            # 처리 완료 플래그 설정
            session["is_processing"] = False


# 싱글톤 인스턴스 생성
websocket_manager = STTWebSocketManager() 