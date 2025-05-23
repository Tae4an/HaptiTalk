import SwiftUI

struct SessionSummaryView: View {
    @Environment(\.presentationMode) var presentationMode
    @EnvironmentObject var appState: AppState
    
    let sessionMode: String
    let totalTime: String
    let mainEmotion: String
    let likeabilityPercent: String
    let coreFeedback: String
    @State private var currentTime: String = ""
    @State private var showDetailAnalysis: Bool = false
    
    let timer = Timer.publish(every: 60, on: .main, in: .common).autoconnect()
    
    init(sessionMode: String = "소개팅 모드", 
         totalTime: String = "1:32:05", 
         mainEmotion: String = "긍정적", 
         likeabilityPercent: String = "88%", 
         coreFeedback: String = "여행 주제에서 높은 호감도를 보였으며, 경청하는 자세가 매우 효과적이었습니다.") {
        self.sessionMode = sessionMode
        self.totalTime = totalTime
        self.mainEmotion = mainEmotion
        self.likeabilityPercent = likeabilityPercent
        self.coreFeedback = coreFeedback
        
        // 현재 시간 초기화
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        self._currentTime = State(initialValue: formatter.string(from: Date()))
    }
    
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)
            
            VStack(spacing: 0) {
                // 상단 시간 표시
                HStack {
                    Spacer()
                    Text(currentTime)
                        .font(.system(size: 10, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.top, 8)
                        .padding(.trailing, 15)
                }
                
                // 헤더 (세션 완료 및 모드)
                VStack(spacing: 4) {
                    Text("세션 완료")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.white)
                    
                    Text(sessionMode)
                        .font(.system(size: 11))
                        .foregroundColor(Color(UIColor.lightGray))
                }
                .padding(.top, 15)
                
                // 세션 통계 정보
                ZStack {
                    RoundedRectangle(cornerRadius: 14)
                        .fill(Color.white.opacity(0.1))
                        .frame(height: 92)
                    
                    VStack(spacing: 10) {
                        // 총 시간
                        HStack {
                            Text("총 시간")
                                .font(.system(size: 11))
                                .foregroundColor(Color(UIColor(red: 0.88, green: 0.88, blue: 0.88, alpha: 1.0))) // #E0E0E0
                            
                            Spacer()
                            
                            Text(totalTime)
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(.white)
                        }
                        
                        // 주요 감정
                        HStack {
                            Text("주요 감정")
                                .font(.system(size: 11))
                                .foregroundColor(Color(UIColor(red: 0.88, green: 0.88, blue: 0.88, alpha: 1.0))) // #E0E0E0
                            
                            Spacer()
                            
                            HStack(spacing: 4) {
                                Image(systemName: "face.smiling.fill")
                                    .font(.system(size: 12))
                                    .foregroundColor(.green)
                                
                                Text(mainEmotion)
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundColor(.white)
                            }
                        }
                        
                        // 호감도
                        HStack {
                            Text("호감도")
                                .font(.system(size: 11))
                                .foregroundColor(Color(UIColor(red: 0.88, green: 0.88, blue: 0.88, alpha: 1.0))) // #E0E0E0
                            
                            Spacer()
                            
                            Text(likeabilityPercent)
                                .font(.system(size: 11, weight: .bold))
                                .foregroundColor(.white)
                        }
                    }
                    .padding(.horizontal, 12)
                }
                .padding(.top, 10)
                .padding(.horizontal, 10)
                
                // 핵심 피드백
                ZStack {
                    RoundedRectangle(cornerRadius: 14)
                        .fill(Color(UIColor(red: 0.25, green: 0.32, blue: 0.71, alpha: 0.15))) // #3F51B5 with opacity
                        .frame(height: 88.5)
                    
                    VStack(alignment: .leading, spacing: 6) {
                        Text("핵심 피드백")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundColor(Color(UIColor(red: 0.56, green: 0.79, blue: 0.98, alpha: 1.0))) // #90CAF9
                        
                        Text(coreFeedback)
                            .font(.system(size: 10))
                            .foregroundColor(Color(UIColor(red: 0.88, green: 0.88, blue: 0.88, alpha: 1.0))) // #E0E0E0
                            .lineSpacing(2)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(.horizontal, 12)
                }
                .padding(.top, 12)
                .padding(.horizontal, 10)
                
                Spacer()
                
                // 버튼 섹션
                VStack(spacing: 8) {
                    // 상세 분석 보기 버튼
                    Button(action: {
                        // 상세 분석 화면으로 이동
                        showDetailAnalysis = true
                    }) {
                        Text("상세 분석 보기")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(Color(UIColor(red: 0.25, green: 0.32, blue: 0.71, alpha: 1.0))) // #3F51B5
                            )
                    }
                    
                    // 홈으로 돌아가기 버튼
                    Button(action: {
                        // 세션 요약 저장 (이미 SessionProgressView에서 저장했을 가능성이 높지만, 중복 방지를 위한 조치 필요)
                        saveSessionIfNeeded()
                        
                        // 홈 화면으로 이동
                        presentationMode.wrappedValue.dismiss()
                    }) {
                        Text("홈으로 돌아가기")
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                            .background(
                                RoundedRectangle(cornerRadius: 16)
                                    .fill(Color.white.opacity(0.15))
                            )
                    }
                }
                .padding(.bottom, 20)
                .padding(.horizontal, 10)
            }
            .padding(.horizontal, 10)
        }
        .onReceive(timer) { _ in
            updateCurrentTime()
        }
        .sheet(isPresented: $showDetailAnalysis) {
            // 여기에 상세 분석 화면을 구현할 수 있습니다
            Text("상세 분석 화면")
                .font(.title)
                .foregroundColor(.white)
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.black)
        }
    }
    
    private func updateCurrentTime() {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        currentTime = formatter.string(from: Date())
    }
    
    private func saveSessionIfNeeded() {
        // 이미 저장된 세션이 있는지 확인하고, 없는 경우에만 저장
        let alreadySaved = appState.sessionSummaries.contains { summary in
            summary.sessionMode == sessionMode &&
            summary.totalTime == totalTime &&
            Date().timeIntervalSince(summary.date) < 60 // 최근 1분 이내에 저장된 세션인지 확인
        }
        
        if !alreadySaved {
            let summary = SessionSummary(
                id: UUID(),
                sessionMode: sessionMode,
                totalTime: totalTime,
                mainEmotion: mainEmotion,
                likeabilityPercent: likeabilityPercent,
                coreFeedback: coreFeedback,
                date: Date()
            )
            appState.saveSessionSummary(summary: summary)
        }
    }
}

#Preview {
    SessionSummaryView()
        .environmentObject(AppState())
} 