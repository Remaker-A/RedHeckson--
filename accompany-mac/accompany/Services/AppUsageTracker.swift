import AppKit
import Combine

@MainActor
final class AppUsageTracker: ObservableObject {

    // MARK: - Public state

    struct AppSession {
        let bundleId: String
        let appName: String
        let category: AppCategory
        let startedAt: Date
    }

    @Published private(set) var currentApp: AppSession?

    /// Accumulated usage per bundle ID within the current hour window.
    @Published private(set) var hourlyUsage: [String: TimeInterval] = [:]

    /// Number of foreground-app switches in the last 60 minutes.
    @Published private(set) var switchCountLastHour: Int = 0

    /// Total screen time today (seconds).
    @Published private(set) var screenTimeToday: TimeInterval = 0

    // MARK: - Private

    private struct SwitchEntry {
        let bundleId: String
        let timestamp: Date
    }

    private var switchLog: [SwitchEntry] = []
    private var dailyUsage: [String: TimeInterval] = [:]
    private var lastDayReset: Date = Calendar.current.startOfDay(for: Date())
    private var observer: NSObjectProtocol?

    // MARK: - Lifecycle

    init() {
        seedCurrentApp()
        observer = NSWorkspace.shared.notificationCenter.addObserver(
            forName: NSWorkspace.didActivateApplicationNotification,
            object: nil, queue: .main
        ) { [weak self] notification in
            Task { @MainActor [weak self] in
                self?.handleAppSwitch(notification)
            }
        }
    }

    deinit {
        if let observer { NSWorkspace.shared.notificationCenter.removeObserver(observer) }
    }

    // MARK: - Snapshot helpers

    func buildUsageEntries() -> [AppUsageEntry] {
        dailyUsage.map { (bundleId, seconds) in
            let appName = NSWorkspace.shared.runningApplications
                .first(where: { $0.bundleIdentifier == bundleId })?
                .localizedName ?? bundleId
            return AppUsageEntry(
                appName: appName,
                bundleId: bundleId,
                durationMinutes: seconds / 60.0,
                category: AppCategoryClassifier.classify(bundleId).rawValue
            )
        }
        .sorted { $0.durationMinutes > $1.durationMinutes }
    }

    func buildHourlyUsageEntries() -> [AppUsageEntry] {
        hourlyUsage.map { (bundleId, seconds) in
            let appName = NSWorkspace.shared.runningApplications
                .first(where: { $0.bundleIdentifier == bundleId })?
                .localizedName ?? bundleId
            return AppUsageEntry(
                appName: appName,
                bundleId: bundleId,
                durationMinutes: seconds / 60.0,
                category: AppCategoryClassifier.classify(bundleId).rawValue
            )
        }
        .sorted { $0.durationMinutes > $1.durationMinutes }
    }

    // MARK: - Internal

    private func seedCurrentApp() {
        guard let app = NSWorkspace.shared.frontmostApplication else { return }
        let bundleId = app.bundleIdentifier ?? "unknown"
        currentApp = AppSession(
            bundleId: bundleId,
            appName: app.localizedName ?? "unknown",
            category: AppCategoryClassifier.classify(bundleId),
            startedAt: Date()
        )
    }

    private func handleAppSwitch(_ notification: Notification) {
        guard let app = notification.userInfo?[NSWorkspace.applicationUserInfoKey]
                as? NSRunningApplication else { return }

        let now = Date()
        resetDayIfNeeded(now)

        if let prev = currentApp {
            let duration = now.timeIntervalSince(prev.startedAt)
            hourlyUsage[prev.bundleId, default: 0] += duration
            dailyUsage[prev.bundleId, default: 0] += duration
            screenTimeToday += duration
        }

        let bundleId = app.bundleIdentifier ?? "unknown"
        currentApp = AppSession(
            bundleId: bundleId,
            appName: app.localizedName ?? "unknown",
            category: AppCategoryClassifier.classify(bundleId),
            startedAt: now
        )

        switchLog.append(SwitchEntry(bundleId: bundleId, timestamp: now))
        pruneOldEntries(now)
    }

    private func pruneOldEntries(_ now: Date) {
        let oneHourAgo = now.addingTimeInterval(-3600)
        switchLog.removeAll { $0.timestamp < oneHourAgo }
        switchCountLastHour = switchLog.count

        // Rebuild hourly usage from switch log
        hourlyUsage = [:]
        for i in 0..<switchLog.count {
            let entry = switchLog[i]
            let end = (i + 1 < switchLog.count) ? switchLog[i + 1].timestamp : now
            let clamped = max(entry.timestamp, oneHourAgo)
            let duration = end.timeIntervalSince(clamped)
            if duration > 0 {
                hourlyUsage[entry.bundleId, default: 0] += duration
            }
        }
    }

    private func resetDayIfNeeded(_ now: Date) {
        let todayStart = Calendar.current.startOfDay(for: now)
        if todayStart > lastDayReset {
            dailyUsage = [:]
            screenTimeToday = 0
            lastDayReset = todayStart
        }
    }
}
