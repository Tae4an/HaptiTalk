// 데이터베이스 접근
var dbName = _getEnv('MONGO_INITDB_DATABASE');
db = db.getSiblingDB(dbName);

// 인증 설정
db.auth(
  _getEnv('MONGO_INITDB_ROOT_USERNAME'),
  _getEnv('MONGO_INITDB_ROOT_PASSWORD')
);

// sessions 컬렉션 인덱스
db.sessions.createIndex(
  { sessionId: 1 },
  { name: "idx_session_id", unique: true }
);
db.sessions.createIndex(
  { userId: 1, createdAt: -1 },
  { name: "idx_user_created" }
);
db.sessions.createIndex(
  { status: 1, type: 1 },
  { name: "idx_status_type" }
);

// sessionAnalytics 컬렉션 인덱스
db.sessionAnalytics.createIndex(
  { userId: 1, sessionType: 1, createdAt: -1 },
  { name: "idx_user_type_date" }
);
db.sessionAnalytics.createIndex(
  { sessionId: 1 },
  { name: "idx_session_id", unique: true }
);

// hapticFeedbacks 컬렉션 인덱스
db.hapticFeedbacks.createIndex(
  { sessionId: 1, timestamp: 1 },
  { name: "idx_session_time" }
);
db.hapticFeedbacks.createIndex(
  { userId: 1, feedbackType: 1 },
  { name: "idx_user_feedback_type" }
);

// speechFeatures 컬렉션 인덱스
db.speechFeatures.createIndex(
  { sessionId: 1, "segment.start": 1 },
  { name: "idx_session_segment" }
);
db.speechFeatures.createIndex(
  { userId: 1, timestamp: 1 },
  { name: "idx_user_timestamp" }
);

// userModels 컬렉션 인덱스
db.userModels.createIndex(
  { userId: 1 },
  { name: "idx_user_id", unique: true }
);

// sessionSegments 컬렉션 인덱스
db.sessionSegments.createIndex(
  { sessionId: 1, segmentIndex: 1 },
  { name: "idx_session_segment", unique: true }
);
db.sessionSegments.createIndex(
  { userId: 1, timestamp: -1 },
  { name: "idx_user_timestamp" }
);
db.sessionSegments.createIndex(
  { sessionId: 1, timestamp: 1 },
  { name: "idx_session_time" }
);

print("MongoDB indexes created successfully");