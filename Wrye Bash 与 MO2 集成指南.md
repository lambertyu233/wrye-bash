# Wrye Bash 与 MO2（Mod Organizer 2）集成指南

> 适用范围：用 MO2 管理《上古卷轴 5：天际 特别版》（Skyrim SE）整合包，并用 Wrye Bash 生成 / 维护 `Bashed Patch, 0.esp`。
> 本文结论已对照本仓库源码核对（见文末「源码依据」）。

---

## 一、核心原则：必须让 WB「跑在 MO2 的 VFS 里」

MO2 用虚拟文件系统（usvfs）把你的整合包叠加到游戏 `Data` 之上。**只有从 MO2 里把 WB 当成一个 executable 启动，WB 才看得到你整合后的 mod**；如果你直接双击 `Wrye Bash.exe`，它看到的是**未经过 MO2 的真实 `Data`**（原版 / 空环境），等于在改错地方。

源码里 `env/windows.py` 的 `in_mo2_vfs()` 正是靠检测 MO2 注入的 `usvfs_x64.dll`（以及 `hook.dll`）来判断自己是否身处 MO2 的 VFS 中——只有 MO2 作为父进程启动 WB 时，这些 DLL 才会被注入。

---

## 二、Wrye Bash 的放置地址

**没有硬性要求，放哪都行**，但建议放一个「中性目录」，例如 `C:\Wrye Bash` 或 `D:\Tools\Wrye Bash`：

- ❌ **不要**装进游戏目录的 `Data` 里（会被当成游戏文件 / 污染）；
- ❌ **不要**装进 MO2 的 `mods` 文件夹（会被 MO2 当成一个 mod 来管理，很乱）；
- ✅ 独立目录最干净。WB 写补丁产物和自身设置都不依赖它自己的位置，只取决于「是否从 MO2 启动」。

---

## 三、从 MO2 启动 WB

1. MO2 顶部菜单 → **Tools（或右键可执行区）→ Edit Executables**；
2. **Add from file…**，选中 `Wrye Bash.exe`（就是你放的那个中性目录里的）；
3. 建议勾选 / 设置 **「Create files in mod instead of overwrite」**，指向一个**专用的空 mod**（例如新建一个叫 `Bash Patch Output` 的空 mod）。这样 WB 构建出的 `Bashed Patch, 0.esp` 会落进这个 mod，而不是散在 Overwrite 里，方便管理；
4. 之后在 MO2 的执行档下拉里选 Wrye Bash 启动即可。

---

## 四、需要加命令行参数吗

**正常情况：不加任何参数**。从 MO2 启动后，游戏路径和 VFS 都由 MO2 接管，WB 自动识别。

只有特殊场景才用（参数定义在 `barg.py`）：

| 参数 | 含义 | 何时用 |
|------|------|--------|
| `-o <游戏根目录>`（`--oblivionPath`） | 强制指定**游戏目录**（含 `SkyrimSE.exe` 的那个），**不是 WB 自己的目录** | WB 装得离游戏很远、且自动检测不到游戏时才需要 |
| `-p <路径>`（`--personalPath`） | 指定 WB 自身设置存放目录（便携 / 多开场景） | 一般不用 |
| `-m <目录>`（`--oblivionMods`） | 覆盖 Bash 根（mods）目录 | 通常别动，交给 MO2 |
| `--no-uac` | 抑制「以管理员重启」的弹窗 | 见下方权限坑 |
| `-b` / `-r` / `-f` | 备份 / 还原 WB 设置 | 与启动整合包无关 |

---

## 五、关键注意事项（踩坑点）

- **构建产物去哪了**：`Bashed Patch, 0.esp` + 日志会写入（被 VFS 映射的）`Data`，MO2 会拦截 → 落到 Overwrite 或你指定的 `Bash Patch Output` mod 里。**必须**在 MO2 右侧「加载顺序（load order）」面板把它放到**最末尾**并保持**激活**（左侧 mod 顺序无所谓，关键是右侧 load order 最后）。
- **分工**：在 MO2 下，WB 只负责「重建 Bashed Patch + 设 Bash Tags + 看冲突」；**装包、启停 mod 仍在 MO2 里做**。改完 mod 列表 / 顺序后，再去 WB 里右键 `Bashed Patch, 0.esp` → **Rebuild Patch…**。
- **权限别乱提**：WB 有时会弹「需要管理员权限重启」。在 MO2 体系下**不要让它提权**——一旦以管理员重启，它会脱离 MO2 的 VFS，反而看不到整合包。保持和 MO2 同一权限级别即可（必要时用 `--no-uac` 抑制弹窗）。
- **帮助文档打不开是正常的**：源码 `gui/doc_viewer.py:67` 明确在 MO2 VFS 下禁用内置 HTML 文档查看器。想看说明直接打开 `Mopy/Docs/` 里的 HTML 文件即可。
- **重建前先排序**：用 LOOT 或 MO2 自带排序定好最终顺序，确认各 mod 的 Bash Tags（尤其 `Delev` / `Relev` / `Filter`），再 Rebuild，并看日志里的 Skipped / Load Error 警告。

---

## 六、一句话总结

> WB 放中性目录 → 从 MO2 当 executable 启动 → 一般不加参数 → 产物落到专用空 mod 并置加载顺序最末。

照这个流程，你的整合包就能用 WB 正常出 Bashed Patch 了。

---

## 七、源码依据（本仓库）

- `Mopy/bash/env/windows.py:1691` — `in_mo2_vfs()`：检测 `hook.dll` / `usvfs_x64.dll` 判断是否在 MO2 虚拟文件系统中运行。
- `Mopy/bash/bash.py:575` — 检测到 `in_mo2_vfs()` 为真时打印「Wrye Bash appears to be running through MO2」。
- `Mopy/bash/gui/doc_viewer.py:67` — `return bool(_wx_html2) and not env.in_mo2_vfs()`：在 MO2 VFS 下禁用内置 HTML 文档查看器。
- `Mopy/bash/barg.py` — 命令行参数定义：`-o/--oblivionPath`、`-m/--oblivionMods`、`-p/--personalPath`、`-u/--userPath`、`-l/--localAppDataPath`、`-b/-r/-f`（备份还原）、`--no-uac`、`--uac`、`-L/--Language`、`-n/--unsupported`。
