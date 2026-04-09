import AppKit
import Combine

/// Orchestrates desktop context collection (three trackers) and uploads
/// periodic snapshots to the companion-agent FastAPI backend.
@MainActor
final class DesktopContextService: ObservableObject {

    // MARK: - Sub-trackers

    let appTracker = AppUsageTracker()
    let windowTracker = WindowTitleTracker()
    let screenAnalyzer = ScreenCaptureAnalyzer()

    // MARK: - Configuration

    @Published var privacyLevel: DesktopPrivacyLevel {
        didSet {
            UserDefaults.standard.set(privacyLevel.rawValue, forKey: Self.privacyLevelKey)
            applyPrivacyLevel()
        }
    }

    /// The base URL of the companion-agent backend (e.g. "http://localhost:8000").
    @Published var backendURL: String {
        didSet { UserDefaults.standard.set(backendURL, forKey: Self.backendURLKey) }
    }

    @Published private(set) var lastUploadTime: Date?
    @Published private(set) var isRunning: Bool = false

    // MARK: - Private

    private static let privacyLevelKey = "desktopContextPrivacyLevel"
    private static let backendURLKey = "desktopContextBackendURL"

    private var snapshotTimer: Timer?
    private var heartbeatTimer: Timer?

    // MARK: - Init

    init() {
        let savedLevel = UserDefaults.standard.integer(forKey: Self.privacyLevelKey)
        self.privacyLevel = DesktopPrivacyLevel(rawValue: savedLevel) ?? .appUsageOnly
        self.backendURL = UserDefaults.standard.string(forKey: Self.backendURLKey) ?? "http://localhost:8000"
    }

    // MARK: - Lifecycle

    func start() {
        guard !isRunning else { return }
        isRunning = true
        applyPrivacyLevel()

        heartbeatTimer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in await self?.sendHeartbeat() }
        }

        snapshotTimer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in await self?.sendSnapshot() }
        }

        if let heartbeatTimer { RunLoop.main.add(heartbeatTimer, forMode: .common) }
        if let snapshotTimer { RunLoop.main.add(snapshotTimer, forMode: .common) }

        Task { await sendHeartbeat() }
    }

    func stop() {
        isRunning = false
        heartbeatTimer?.invalidate()
        heartbeatTimer = nil
        snapshotTimer?.invalidate()
        snapshotTimer = nil
        windowTracker.stopTracking()
        screenAnalyzer.stopCapturing()
    }

    // MARK: - Privacy level management

    private func applyPrivacyLevel() {
        // Level 1 is always active (AppUsageTracker runs on init)

        if privacyLevel.rawValue >= DesktopPrivacyLevel.withWindowTitle.rawValue {
            if WindowTitleTracker.hasAccessibilityPermission {
                windowTracker.startTracking()
            }
        } else {
            windowTracker.stopTracking()
        }

        if privacyLevel.rawValue >= DesktopPrivacyLevel.withScreenCapture.rawValue {
            screenAnalyzer.startCapturing(intervalMinutes: 5)
        } else {
            screenAnalyzer.stopCapturing()
        }
    }

    // MARK: - Network: Heartbeat

    private func sendHeartbeat() async {
        guard let app = appTracker.currentApp else { return }
        let payload = DesktopHeartbeatPayload(
            frontmostApp: app.appName,
            frontmostCategory: app.category.rawValue,
            bundleId: app.bundleId
        )
        await post(path: "/api/desktop/heartbeat", body: payload)
    }

    // MARK: - Network: Snapshot

    private func sendSnapshot() async {
        guard let app = appTracker.currentApp else { return }

        var payload = DesktopSnapshotPayload(
            frontmostApp: app.appName,
            frontmostCategory: app.category.rawValue,
            hourlyUsage: appTracker.buildHourlyUsageEntries(),
            appSwitchCountLastHour: appTracker.switchCountLastHour,
            screenTimeTodayMinutes: Int(appTracker.screenTimeToday / 60)
        )

        if privacyLevel.rawValue >= DesktopPrivacyLevel.withWindowTitle.rawValue {
            payload.windowTitleHint = windowTracker.titleHint
        }

        if privacyLevel.rawValue >= DesktopPrivacyLevel.withScreenCapture.rawValue {
            payload.activitySummary = screenAnalyzer.activitySummary
        }

        await post(path: "/api/desktop/snapshot", body: payload)
        lastUploadTime = Date()
    }

    // MARK: - HTTP helper

    private func post<T: Encodable>(path: String, body: T) async {
        guard let url = URL(string: backendURL + path) else { return }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.timeoutInterval = 10

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(body)
            _ = try await URLSession.shared.data(for: request)
        } catch {
            // Silently ignore upload failures — the companion may be offline.
        }
    }
}
