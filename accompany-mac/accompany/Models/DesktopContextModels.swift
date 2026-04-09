import Foundation

// MARK: - Privacy level

enum DesktopPrivacyLevel: Int, Codable, CaseIterable {
    case appUsageOnly = 1
    case withWindowTitle = 2
    case withScreenCapture = 3

    var displayName: String {
        switch self {
        case .appUsageOnly:    return "基础"
        case .withWindowTitle: return "增强"
        case .withScreenCapture: return "完整"
        }
    }

    var description: String {
        switch self {
        case .appUsageOnly:    return "仅追踪应用使用（无需额外权限）"
        case .withWindowTitle: return "加上窗口标题（需辅助功能权限）"
        case .withScreenCapture: return "加上截屏理解（需屏幕录制权限）"
        }
    }
}

// MARK: - App category

enum AppCategory: String, Codable {
    case coding, terminal, browser, communication, meeting, media, office, design, other
}

// MARK: - Snapshot payload (matches backend DesktopSnapshotRequest)

struct DesktopSnapshotPayload: Codable {
    var frontmostApp: String = ""
    var frontmostCategory: String = "other"
    var windowTitleHint: String = ""
    var activitySummary: String = ""
    var hourlyUsage: [AppUsageEntry] = []
    var appSwitchCountLastHour: Int = 0
    var screenTimeTodayMinutes: Int = 0

    enum CodingKeys: String, CodingKey {
        case frontmostApp = "frontmost_app"
        case frontmostCategory = "frontmost_category"
        case windowTitleHint = "window_title_hint"
        case activitySummary = "activity_summary"
        case hourlyUsage = "hourly_usage"
        case appSwitchCountLastHour = "app_switch_count_last_hour"
        case screenTimeTodayMinutes = "screen_time_today_minutes"
    }
}

struct AppUsageEntry: Codable {
    var appName: String
    var bundleId: String
    var durationMinutes: Double
    var category: String

    enum CodingKeys: String, CodingKey {
        case appName = "app_name"
        case bundleId = "bundle_id"
        case durationMinutes = "duration_minutes"
        case category
    }
}

// MARK: - Heartbeat payload (matches backend DesktopHeartbeatRequest)

struct DesktopHeartbeatPayload: Codable {
    var frontmostApp: String
    var frontmostCategory: String = "other"
    var bundleId: String = ""

    enum CodingKeys: String, CodingKey {
        case frontmostApp = "frontmost_app"
        case frontmostCategory = "frontmost_category"
        case bundleId = "bundle_id"
    }
}
