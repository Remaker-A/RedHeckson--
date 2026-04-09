import SwiftUI

/// A compact settings panel for desktop context privacy level,
/// designed to appear inside the expanded notch panel or as a popover.
struct DesktopContextSettingsView: View {
    @ObservedObject var service: DesktopContextService

    @State private var showBackendField = false

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("桌面感知")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(.white.opacity(0.8))

            ForEach(DesktopPrivacyLevel.allCases, id: \.rawValue) { level in
                PrivacyLevelRow(
                    level: level,
                    isSelected: service.privacyLevel == level
                ) {
                    withAnimation(.easeInOut(duration: 0.15)) {
                        service.privacyLevel = level
                    }
                }
            }

            if service.isRunning, let lastTime = service.lastUploadTime {
                HStack(spacing: 4) {
                    Circle()
                        .fill(.green)
                        .frame(width: 6, height: 6)
                    Text("已连接 · 上次同步 \(timeAgo(lastTime))")
                        .font(.system(size: 9))
                        .foregroundStyle(.white.opacity(0.4))
                }
                .padding(.top, 2)
            }

            Divider()
                .background(Color.white.opacity(0.1))

            Button {
                withAnimation(.easeInOut(duration: 0.15)) {
                    showBackendField.toggle()
                }
            } label: {
                HStack {
                    Image(systemName: "server.rack")
                        .font(.system(size: 10))
                    Text("后端地址")
                        .font(.system(size: 10))
                    Spacer()
                    Image(systemName: showBackendField ? "chevron.up" : "chevron.down")
                        .font(.system(size: 8))
                }
                .foregroundStyle(.white.opacity(0.5))
            }
            .buttonStyle(.plain)

            if showBackendField {
                TextField("http://localhost:8000", text: $service.backendURL)
                    .textFieldStyle(.plain)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.7))
                    .padding(6)
                    .background(
                        RoundedRectangle(cornerRadius: 6)
                            .fill(Color.white.opacity(0.08))
                    )
            }
        }
        .padding(12)
        .frame(width: 220)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.black.opacity(0.7))
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .strokeBorder(Color.white.opacity(0.1), lineWidth: 1)
                )
        )
    }

    private func timeAgo(_ date: Date) -> String {
        let seconds = Int(Date().timeIntervalSince(date))
        if seconds < 60 { return "刚刚" }
        if seconds < 3600 { return "\(seconds / 60)分钟前" }
        return "\(seconds / 3600)小时前"
    }
}

// MARK: - Row

private struct PrivacyLevelRow: View {
    let level: DesktopPrivacyLevel
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 12))
                    .foregroundStyle(isSelected ? .white : .white.opacity(0.3))

                VStack(alignment: .leading, spacing: 1) {
                    Text(level.displayName)
                        .font(.system(size: 11, weight: isSelected ? .semibold : .regular))
                        .foregroundStyle(isSelected ? .white : .white.opacity(0.6))
                    Text(level.description)
                        .font(.system(size: 9))
                        .foregroundStyle(.white.opacity(0.35))
                }

                Spacer()
            }
            .padding(.vertical, 4)
            .padding(.horizontal, 8)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isSelected ? Color.white.opacity(0.1) : Color.clear)
            )
        }
        .buttonStyle(.plain)
    }
}
