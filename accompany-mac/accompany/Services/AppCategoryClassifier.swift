import Foundation

struct AppCategoryClassifier {

    private static let exactMap: [String: AppCategory] = [
        // Coding
        "com.microsoft.VSCode": .coding,
        "com.microsoft.VSCodeInsiders": .coding,
        "com.apple.dt.Xcode": .coding,
        "com.sublimetext.4": .coding,
        "com.sublimetext.3": .coding,
        "dev.zed.Zed": .coding,
        "com.cursor.Cursor": .coding,

        // Terminal
        "com.googlecode.iterm2": .terminal,
        "com.apple.Terminal": .terminal,
        "dev.warp.Warp-Stable": .terminal,
        "net.kovidgoyal.kitty": .terminal,

        // Browser
        "com.apple.Safari": .browser,
        "com.google.Chrome": .browser,
        "org.mozilla.firefox": .browser,
        "com.microsoft.edgemac": .browser,
        "company.thebrowser.Browser": .browser,

        // Communication
        "com.tencent.xinWeChat": .communication,
        "com.apple.MobileSMS": .communication,
        "com.tencent.qq": .communication,
        "com.hnc.Discord": .communication,
        "com.tinyspeck.slackmacgap": .communication,
        "ru.keepcoder.Telegram": .communication,

        // Meeting
        "us.zoom.xos": .meeting,
        "com.tencent.meeting": .meeting,
        "com.microsoft.teams2": .meeting,

        // Media
        "com.spotify.client": .media,
        "com.apple.Music": .media,
        "com.apple.TV": .media,
        "com.bilibili.bili-universal": .media,

        // Office
        "com.apple.iWork.Keynote": .office,
        "com.apple.iWork.Pages": .office,
        "com.apple.iWork.Numbers": .office,
        "com.microsoft.Word": .office,
        "com.microsoft.Excel": .office,
        "com.microsoft.Powerpoint": .office,
        "com.apple.Notes": .office,
        "md.obsidian": .office,
        "com.electron.logseq": .office,
        "com.notion.Notion": .office,

        // Design
        "com.figma.Desktop": .design,
        "com.bohemiancoding.sketch3": .design,
    ]

    private static let prefixMap: [(String, AppCategory)] = [
        ("com.jetbrains.", .coding),
        ("com.tencent.", .communication),
    ]

    static func classify(_ bundleId: String) -> AppCategory {
        if let exact = exactMap[bundleId] { return exact }
        for (prefix, category) in prefixMap where bundleId.hasPrefix(prefix) {
            return category
        }
        return .other
    }
}
