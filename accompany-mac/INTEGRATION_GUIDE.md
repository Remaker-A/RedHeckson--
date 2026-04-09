# 桌面上下文采集模块 — 集成指南

将以下新增文件添加到 Xcode 项目后，按如下步骤集成到现有代码中。

---

## 1. 新增文件清单（拖入 Xcode 项目）

```
accompany/
├── Models/
│   └── DesktopContextModels.swift     ← 数据模型 & Codable 结构体
├── Services/
│   ├── AppCategoryClassifier.swift    ← bundleId → 类别映射
│   ├── AppUsageTracker.swift          ← Level 1: 应用使用追踪
│   ├── WindowTitleTracker.swift       ← Level 2: 窗口标题追踪
│   ├── ScreenCaptureAnalyzer.swift    ← Level 3: 截屏理解
│   └── DesktopContextService.swift    ← 统一调度 + HTTP 上报
└── Views/
    └── DesktopContextSettingsView.swift ← 隐私级别设置 UI
```

## 2. 修改 NotchWindowController.swift

在 `NotchWindowController` 类中：

```swift
// 1) 新增属性（与 emotionService / whiteNoiseService 同级）
private let desktopContextService = DesktopContextService()

// 2) 在 init() 末尾启动服务
desktopContextService.start()

// 3) 把 desktopContextService 传给 NotchViewController
let contentController = NotchViewController(
    viewModel: viewModel,
    emotionService: emotionService,
    whiteNoiseService: whiteNoiseService,
    desktopContextService: desktopContextService,  // ← 新增
    onToggleExpanded: { [weak self] in
        self?.viewModel.toggle()
    }
)

// 4) 在右键菜单中添加隐私级别子菜单
// 在 showMenu(at:) 方法里，soundMenuItem 之前添加：
let ctxMenu = NSMenu()
for level in DesktopPrivacyLevel.allCases {
    let item = NSMenuItem(
        title: level.displayName,
        action: #selector(selectPrivacyLevel(_:)),
        keyEquivalent: ""
    )
    item.target = self
    item.representedObject = level.rawValue
    item.state = desktopContextService.privacyLevel == level ? .on : .off
    ctxMenu.addItem(item)
}
let ctxMenuItem = NSMenuItem(title: "桌面感知", action: nil, keyEquivalent: "")
ctxMenuItem.submenu = ctxMenu
menu.addItem(ctxMenuItem)

// 5) 添加对应的 selector 方法
@objc
private func selectPrivacyLevel(_ sender: NSMenuItem) {
    guard let raw = sender.representedObject as? Int,
          let level = DesktopPrivacyLevel(rawValue: raw) else { return }
    desktopContextService.privacyLevel = level
}
```

## 3. 修改 ExpandedView.swift（可选）

如果希望在展开面板中显示设置入口：

```swift
struct ExpandedView: View {
    @ObservedObject var whiteNoiseService: WhiteNoiseService
    @ObservedObject var desktopContextService: DesktopContextService  // ← 新增
    @State private var pickerVisible = false
    @State private var ctxSettingsVisible = false  // ← 新增

    var body: some View {
        ZStack(alignment: .topTrailing) {
            // ... 现有内容 ...

            VStack(alignment: .trailing, spacing: 6) {
                // 现有音效按钮
                SoundToggleButton(/* ... */) { /* ... */ }

                // 新增：桌面感知设置按钮
                ContextSettingsButton(isOpen: ctxSettingsVisible) {
                    withAnimation(.spring(response: 0.22, dampingFraction: 0.8)) {
                        ctxSettingsVisible.toggle()
                        pickerVisible = false
                    }
                }

                if ctxSettingsVisible {
                    DesktopContextSettingsView(service: desktopContextService)
                        .transition(
                            .scale(scale: 0.88, anchor: .topTrailing)
                            .combined(with: .opacity)
                        )
                }

                // 现有音效选择器
                if pickerVisible { /* ... */ }
            }
        }
    }
}
```

## 4. Info.plist 权限描述（Level 2/3 需要）

如果用户选择了 Level 2 或 Level 3，需要在 Info.plist 中添加：

```xml
<!-- Level 2: 辅助功能 -->
<key>NSAccessibilityUsageDescription</key>
<string>用于感知你正在做什么，让陪伴更有温度</string>

<!-- Level 3: 屏幕录制 (ScreenCaptureKit 自动处理权限弹窗) -->
```

## 5. 后端对接

确保 companion-agent 后端已部署最新代码（包含 `/api/desktop/*` 路由），
默认地址 `http://localhost:8000`。可在右键菜单或设置面板中修改。
