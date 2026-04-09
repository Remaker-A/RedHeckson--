import AppKit
import Combine

@MainActor
final class WindowTitleTracker: ObservableObject {

    @Published private(set) var rawTitle: String = ""
    @Published private(set) var titleHint: String = ""

    private var pollTimer: Timer?

    /// Check whether Accessibility permission is granted.
    static var hasAccessibilityPermission: Bool {
        AXIsProcessTrusted()
    }

    /// Prompt the system dialog that asks the user to grant accessibility permission.
    static func requestAccessibilityPermission() {
        let options = [kAXTrustedCheckOptionPrompt.takeRetainedValue(): true] as CFDictionary
        AXIsProcessTrustedWithOptions(options)
    }

    func startTracking(interval: TimeInterval = 30) {
        guard Self.hasAccessibilityPermission else {
            Self.requestAccessibilityPermission()
            return
        }
        poll()
        pollTimer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in self?.poll() }
        }
        if let pollTimer {
            RunLoop.main.add(pollTimer, forMode: .common)
        }
    }

    func stopTracking() {
        pollTimer?.invalidate()
        pollTimer = nil
    }

    // MARK: - Private

    private func poll() {
        guard let app = NSWorkspace.shared.frontmostApplication else { return }

        let axApp = AXUIElementCreateApplication(app.processIdentifier)
        var focusedWindow: AnyObject?
        let windowResult = AXUIElementCopyAttributeValue(
            axApp, kAXFocusedWindowAttribute as CFString, &focusedWindow
        )
        guard windowResult == .success, let window = focusedWindow else {
            rawTitle = ""
            titleHint = ""
            return
        }

        var titleValue: AnyObject?
        let titleResult = AXUIElementCopyAttributeValue(
            window as! AXUIElement, kAXTitleAttribute as CFString, &titleValue
        )
        guard titleResult == .success, let title = titleValue as? String else {
            rawTitle = ""
            titleHint = ""
            return
        }

        rawTitle = title
        titleHint = sanitize(title, appName: app.localizedName ?? "")
    }

    /// Strip sensitive details; keep only the activity-type hint.
    private func sanitize(_ title: String, appName: String) -> String {
        let bundleId = NSWorkspace.shared.frontmostApplication?.bundleIdentifier ?? ""
        let category = AppCategoryClassifier.classify(bundleId)

        switch category {
        case .coding:
            return extractCodingHint(title, appName: appName)
        case .browser:
            return extractBrowserHint(title)
        case .meeting:
            return "会议中"
        case .communication:
            return "在使用\(appName)"
        case .media:
            return "在使用\(appName)"
        default:
            return "在使用\(appName)"
        }
    }

    private func extractCodingHint(_ title: String, appName: String) -> String {
        // "main.swift — MyProject" → "在 Xcode 中编辑 Swift 文件"
        let parts = title.components(separatedBy: CharacterSet(charactersIn: "—–-"))
        let fileName = parts.first?.trimmingCharacters(in: .whitespaces) ?? ""

        if let ext = fileName.split(separator: ".").last {
            let lang = fileExtToLanguage(String(ext))
            if !lang.isEmpty {
                return "在\(appName)中编辑\(lang)文件"
            }
        }

        if parts.count > 1 {
            let project = parts.last?.trimmingCharacters(in: .whitespaces) ?? ""
            if !project.isEmpty && project != appName {
                return "在\(appName)中编辑项目"
            }
        }
        return "在\(appName)中写代码"
    }

    private func extractBrowserHint(_ title: String) -> String {
        let lower = title.lowercased()
        if lower.contains("youtube") || lower.contains("bilibili") || lower.contains("视频") {
            return "在浏览器中看视频"
        }
        if lower.contains("github") || lower.contains("stackoverflow") || lower.contains("stack overflow") {
            return "在浏览器中查技术资料"
        }
        if lower.contains("twitter") || lower.contains("weibo") || lower.contains("reddit") {
            return "在浏览器中刷社交媒体"
        }
        if lower.contains("mail") || lower.contains("邮") || lower.contains("gmail") || lower.contains("outlook") {
            return "在浏览器中处理邮件"
        }
        return "在浏览器中浏览网页"
    }

    private func fileExtToLanguage(_ ext: String) -> String {
        let map: [String: String] = [
            "swift": "Swift", "py": "Python", "js": "JavaScript",
            "ts": "TypeScript", "tsx": "React", "jsx": "React",
            "rs": "Rust", "go": "Go", "java": "Java",
            "c": "C", "cpp": "C++", "h": "C/C++",
            "vue": "Vue", "html": "HTML", "css": "CSS",
            "md": "Markdown", "json": "JSON", "yaml": "YAML",
        ]
        return map[ext.lowercased()] ?? ""
    }
}
