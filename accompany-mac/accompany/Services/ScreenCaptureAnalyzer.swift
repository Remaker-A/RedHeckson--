import AppKit
import Combine
import ScreenCaptureKit

@MainActor
final class ScreenCaptureAnalyzer: ObservableObject {

    @Published private(set) var activitySummary: String = ""
    @Published private(set) var isCapturing: Bool = false

    /// Vision LLM endpoint (e.g. OpenAI-compatible /v1/chat/completions).
    var llmBaseURL: String = ""
    var llmAPIKey: String = ""
    var llmModel: String = "gpt-4o-mini"

    private var captureTimer: Timer?

    // MARK: - Public

    func startCapturing(intervalMinutes: Int = 5) {
        guard !isCapturing else { return }
        isCapturing = true

        Task { await captureAndAnalyze() }

        captureTimer = Timer.scheduledTimer(
            withTimeInterval: Double(intervalMinutes * 60),
            repeats: true
        ) { [weak self] _ in
            Task { @MainActor [weak self] in await self?.captureAndAnalyze() }
        }
        if let captureTimer {
            RunLoop.main.add(captureTimer, forMode: .common)
        }
    }

    func stopCapturing() {
        captureTimer?.invalidate()
        captureTimer = nil
        isCapturing = false
    }

    // MARK: - Capture + Analyze

    private func captureAndAnalyze() async {
        do {
            let image = try await captureScreen()
            guard let jpegData = imageToJPEG(image, maxWidth: 1280, quality: 0.5) else { return }
            let summary = try await analyzeWithVisionLLM(jpegData)
            activitySummary = summary
        } catch {
            print("ScreenCaptureAnalyzer: \(error.localizedDescription)")
        }
    }

    private func captureScreen() async throws -> CGImage {
        let content = try await SCShareableContent.excludingDesktopWindows(
            false, onScreenWindowsOnly: true
        )
        guard let display = content.displays.first else {
            throw ScreenCaptureError.noDisplay
        }

        let filter = SCContentFilter(
            display: display,
            excludingApplications: [],
            exceptingWindows: []
        )

        let config = SCStreamConfiguration()
        config.width = 1280
        config.height = 720
        config.showsCursor = false

        return try await SCScreenshotManager.captureImage(
            contentFilter: filter, configuration: config
        )
    }

    // MARK: - Image processing

    private func imageToJPEG(_ cgImage: CGImage, maxWidth: Int, quality: CGFloat) -> Data? {
        let nsImage = NSImage(cgImage: cgImage, size: NSSize(width: cgImage.width, height: cgImage.height))
        let scale = min(1.0, CGFloat(maxWidth) / CGFloat(cgImage.width))
        let newSize = NSSize(
            width: CGFloat(cgImage.width) * scale,
            height: CGFloat(cgImage.height) * scale
        )

        let resized = NSImage(size: newSize)
        resized.lockFocus()
        nsImage.draw(in: NSRect(origin: .zero, size: newSize))
        resized.unlockFocus()

        guard let tiff = resized.tiffRepresentation,
              let bitmap = NSBitmapImageRep(data: tiff) else { return nil }
        return bitmap.representation(using: .jpeg, properties: [.compressionFactor: quality])
    }

    // MARK: - Vision LLM

    private func analyzeWithVisionLLM(_ jpegData: Data) async throws -> String {
        guard !llmBaseURL.isEmpty, !llmAPIKey.isEmpty else {
            throw ScreenCaptureError.noLLMConfig
        }

        let base64 = jpegData.base64EncodedString()
        let url = URL(string: "\(llmBaseURL)/v1/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(llmAPIKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 30

        let body: [String: Any] = [
            "model": llmModel,
            "max_tokens": 100,
            "messages": [
                [
                    "role": "user",
                    "content": [
                        [
                            "type": "text",
                            "text": "用一句简短的中文描述用户当前正在做什么。只关注活动类型（编程/浏览/会议/写文档/看视频等），不要描述具体内容。如果看到敏感信息请忽略。直接输出描述，不要任何前缀。"
                        ],
                        [
                            "type": "image_url",
                            "image_url": [
                                "url": "data:image/jpeg;base64,\(base64)",
                                "detail": "low"
                            ]
                        ]
                    ]
                ]
            ]
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 200 else {
            throw ScreenCaptureError.llmRequestFailed
        }

        let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        let choices = json?["choices"] as? [[String: Any]]
        let message = choices?.first?["message"] as? [String: Any]
        let content = message?["content"] as? String
        return content?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
    }
}

// MARK: - Errors

enum ScreenCaptureError: LocalizedError {
    case noDisplay
    case noLLMConfig
    case llmRequestFailed

    var errorDescription: String? {
        switch self {
        case .noDisplay: return "No display available for capture"
        case .noLLMConfig: return "Vision LLM API not configured"
        case .llmRequestFailed: return "Vision LLM request failed"
        }
    }
}
