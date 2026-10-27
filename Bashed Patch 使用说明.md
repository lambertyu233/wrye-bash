# Wrye Bash · Bashed Patch（合成补丁）完整使用说明

> 本文依据本仓库源码（`Mopy/bash/basher/gui_patchers.py`、`patcher_dialog.py`、`patcher/patch_files.py`、`basher/mod_links.py`）与 `Mopy/Docs` 中的官方 Readme 整理，面向**手动操作软件**的用户。
> 适用范围：**Skyrim / Skyrim Special Edition**（其它游戏可用的 Patcher 略有差异，见文末说明）。

---

## 一、Bashed Patch 是什么

Bashed Patch（文件名为 `Bashed Patch, 0.esp`）是 Wrye Bash 生成的一个**特殊插件**，它本身不新增内容，而是把其它插件的修改**合并 / 导入 / 微调**到一起，解决「多个 MOD 改了同一样东西，谁覆盖谁」的冲突问题。

它有三个核心功能（对应源码里的三大类 Patcher 分组）：

| 功能 | 说明 | 对应分组 |
|------|------|----------|
| **合并（Merge）** | 把只包含某些记录类型的「小补丁」合并进 Bashed Patch，合并后原插件可停用，从而节省 255 插件上限的槽位 | General → Merge Patches |
| **导入（Import）** | 把某些特定类型的数据（如演员属性、物品数值、图形、命名等）从指定插件导入补丁，避免兼容性冲突 | Importers |
| **微调（Tweak）** | 直接修改游戏设置/记录，无需再装对应的 MOD | Tweakers |

> ⚠️ **铁律**：每次你改动加载顺序（增删插件、调顺序）后，**进游戏前必须重建（Rebuild）一次 Bashed Patch**。Bashed Patch 默认应位于加载顺序**最末尾**（除非某个 MOD 明确要求它必须最后加载）。

---

## 二、如何打开配置对话框

1. 在 Wrye Bash 的 **Mods（插件）标签页** 里找到 `Bashed Patch, 0.esp`（首次运行 Wrye Bash 时会自动创建）。
2. **右键** 它 → 选择 **`Rebuild Patch…`（重建补丁）**。
3. 弹出 **Bashed Patch 配置对话框**，在这里勾选要启用的 Patcher 与具体来源/选项。

> 源码位置：`basher/mod_links.py` 的 `Mod_RebuildPatch`，它通过 `PatchDialog.display_dialog(...)` 打开对话框。

---

## 三、对话框布局与按钮

对话框分为三块：

- **左侧**：Patcher 列表（按分组排列，每项前有勾选框）。
- **右侧**：当前选中 Patcher 的具体配置（来源插件、勾选项、微调选项等）。
- **底部**：操作按钮。

### 底部按钮

| 按钮 | 作用 |
|------|------|
| **Build Patch（构建补丁）** | 用当前配置开始构建。只要有一个 Patcher 被启用，按钮才可点。 |
| **Select All / Deselect All（列表旁）** | 选中/取消**当前 Patcher** 列表里的所有选项。 |
| **Select All / Deselect All（窗口底部）** | 选中/取消**所有分组、所有选项**。 |
| **Export（导出）** | 把当前配置保存为 `<补丁名>_Configuration.dat`，用于备份/迁移。 |
| **Import（导入）** | 从导出的 `.dat` 文件恢复配置。 |
| **Revert To Saved（恢复到已保存）** | 撤销本次打开后所做的改动，回到上次构建时的配置。 |
| **Revert To Default（恢复默认）** | 把所有 Patcher 重置为默认配置（默认启用项见各节）。 |
| **Cancel（取消）** | 关闭对话框，不构建。 |

### 交互细节（来自源码）

- 把鼠标悬停在某个 Patcher / 选项上，**窗口底部会显示它的简短说明**。
- **加粗** 的项是「自上次构建以来新增的」（需要你留意）；**斜体** 的项表示它「没有可运行的来源」（例如没有可导入的 MOD），不会实际运行。
- 快捷键：**在当前 Patcher 列表上按 `Ctrl+A`** 可全选（按住 `Shift+Ctrl+A` 为全不选）。
- 带多个取值的 Tweak（如数值/开关），**右键**该项可弹出菜单选择不同取值；自定义值会用输入框让你填写。

---

## 四、四大分组与每个 Patcher 详解

Patcher 按 `patcher_group` 分四组：**General / Importers / Tweakers / Special**。下面列出 **Skyrim SE 实际可用** 的项（分组内按字母/逻辑排序）。

### 1. General（常规）

#### Alias Plugin Names（别名插件名）
- 类型：无选项，仅一个文本框。
- 作用：为读取 CSV 来源文件时指定**插件别名**，格式为 `原插件名 >> 别名`。极少需要手动改，一般留给高级 CSV 导入用。

#### Merge Patches（合并补丁）
- 类型：来源列表（默认**自动**，列出所有可合并的插件）。
- 作用：把勾选的、只包含「可合并记录类型」的插件**合并进** Bashed Patch。点「Rebuild Patch」时，WB 会**先**弹出一个对话框，询问是否停用这些可合并插件（以及带 `NoMerge` / `Deactivate` 标签的插件）；**确认**才会停用，**拒绝则保持激活**，构建仍会照常进行。
- ⚠️ **不要从 Data 文件夹里删掉被合并的 MOD**——下次重建时它们必须还在。
- 提示：构建前可保持这些插件**未激活**；合并算法对后续其它 Patcher 仍然正常工作。

> 该 Patcher 仅在游戏支持「合并检查（MergeabilityCheck.MERGE）」时自动加入，Skyrim SE 支持。

---

### 2. Importers（导入）

这一类 Patcher 把指定插件里的特定记录**导入**补丁。大部分「Preserves…（保留…）」类的，若两个 MOD 改了同一项，则**后加载的覆盖先加载的**；其余是「合并」。

> 列表里每个 Import 项默认**自动**勾选带有对应 Bash Tag 的插件（见第五节）。

| Patcher | 作用 | 使用建议 |
|---------|------|----------|
| **Import Actors** | 保留 NPCs/生物（演员）的各项属性修改 | 总是启用（除非 MOD 说明另有要求） |
| **Import Actors: AI Packages** | 合并演员的 AI 包修改 | 总是启用 |
| **Import Actors: Factions** | 保留演员所属派系修改 | 总是启用 |
| **Import Actors: Perks** | 合并 NPC 的 perk 列表修改 | 总是启用（Skyrim 起全游戏可用） |
| **Import Actors: Spells** | 合并演员的法术/效果列表修改 | 总是启用 |
| **Import Cells** | 保留单元格（气候、光照、音乐、名称、归属、水面等）修改 | 总是启用（Fallout 4 除外） |
| **Import Destructible** | 保留「可破坏物件」的修改 | 总是启用（装了可破坏环境 MOD 时必须用） |
| **Import Effect Stats** | 保留魔法/基础效果的属性修改 | 总是启用 |
| **Import Enchantments** | 保留物品（ armor/weapon 等）的附魔修改 | 总是启用 |
| **Import Enchantment Stats** | 保留附魔效果数据修改 | 总是启用 |
| **Import Graphics** | 保留模型/贴图等图形修改 | **看喜好**：选你喜欢的那个 MOD 的图形 |
| **Import Inventory** | 合并各类库存（容器、NPC 等）的物品修改 | 总是启用 |
| **Import Keywords** | 保留各类对象的 Keyword 修改 | 总是启用（Skyrim 起） |
| **Import Names** | 保留各类名称修改 | **看喜好**：选你喜欢的命名 |
| **Import Object Bounds** | 保留大量对象的包围盒（碰撞）修改 | 总是启用（Fallout 3 起） |
| **Import Outfits** | 合并 NPC  outfit（着装）修改 | 总是启用（Skyrim 起） |
| **Import Races** | 保留种族记录的修改（体型、描述、技能、属性、声音等） | 默认关闭；Skyrim 可用，按需启用（Oblivion 亦可用） |
| **Import Races: Spells** | 合并种族能力/法术的增删改 | 总是启用（Fallout 3/NV/FO4 除外） |
| **Import Relations** | 合并派系之间的关系增删改 | 总是启用 |
| **Import Sounds** | 保留各类音效（魔法效果、容器、激活器、灯、天气、门等）修改 | **看喜好**：选你喜欢的音效 |
| **Import Spell Stats** | 保留法术属性（修复 Bug / 重平衡）修改 | 总是启用；多 MOD 重做数值时**看喜好**选其一 |
| **Import Stats** | 保留可拾取物品属性（修复/重平衡）修改 | 总是启用；同上 |
| **Import Text** | 保留长文本（书、装备/法术/武器描述等）修改 | 总是启用（Fallout 4 除外） |

> ❗ Skyrim SE **不可用** 的 Import 类（不在 `game/skyrim/__init__.py` 的 patcher 清单内）：Import Actors: Faces、Import Races: Relations、Import Scripts、Import Weapon Modifications。

---

### 3. Tweakers（微调）

每个 Tweak 可在右侧列表里单独勾选；带 `[方括号]` 取值的，右键可换值。以下为 Skyrim SE 可用分组：

| 分组 | 内容 | 默认启用 |
|------|------|----------|
| **Tweak Assorted（杂项微调）** | 各种杂项调整 | ✅ 默认启用 |
| **Tweak Settings（设置微调 / GMST）** | 调整游戏设置（GMST） | ✅ 默认启用 |
| **Tweak Names（命名微调）** | 按类型/数值给物品改名，或提升剧情友好度等 | 默认关闭 |
| **Tweak Actors（演员微调）** | 调整 NPC/生物相关设置 | 默认关闭 |
| **Tweak Races（种族微调）** | 调整种族记录 | 默认关闭 |

> Skyrim SE 特有的推荐项（来自官方 Readme）：
> - **Tweak Assorted → Magic: Summoning Absorption Fix**：修复影响众多 MOD 的召唤吸收问题，**推荐所有 Skyrim/SE 用户启用**。
> - 纯属个人喜好，按需开启（如改名规则、负重/格挡调整等）。

> ❗ Skyrim SE **不可用**：Tweak Clothes（衣物微调）。

---

### 4. Special（特殊）

| Patcher | 说明 | 默认启用 |
|---------|------|----------|
| **Leveled Lists（等级列表）** | 合并所有插件对等级列表（leveled lists）的修改，是兼容性关键。详见第五节。 | ✅ 默认启用 |
| **Contents Checker（内容检查）** | 检查等级列表、库存、容器里的条目类型是否正确 | ✅ 默认启用 |
| **Timescale Checker（时间流速检查）** | 让草的波动周期匹配你自定义的 timescale；未用非标准 timescale 时不起作用 | ✅ 默认启用 |

> ❗ Skyrim SE **不可用**：Race Checker、NPC Checker、Replace Form IDs、FormID Lists（后两者为 Fallout 系列 / 通用但 Skyrim 未启用）。

#### Leveled Lists 重点说明
等级列表 Patcher 本质是「导入」，但选项**默认自动**判定。规则（由 Bash Tag 驱动）：

- **未标记** 的插件：只能向等级列表**新增**条目；若条目已存在则忽略，且不会把已被删的条目加回来。
- **`Delev`** 标记的插件：可**删除**条目（插件里没有、但其 master 里有的条目会被移除）。
- **`Relev`** 标记的插件：可**重新定级**（改等级/数量），并可覆盖之前的删除；但**不能阻止**更晚加载的 `Delev` 插件再次删它。
- **`Delev` + `Relev`** 同时标记：两者效果叠加。
- 勾选 **Remove Empty Sublists（移除空子列表）**：会清掉空子列表（避免游戏里抽到空列表什么都不出）。**仅当你确认加载顺序里没有「等级列表注入器（leveled list injector）」类 MOD 时才安全开启**，否则可能误删运行时才填充的列表。

手动覆盖某插件的 Delev/Relev：在该列表项上**右键**勾选/取消，或选 **Auto** 回到自动判定。

---

## 五、Bash Tags（Bash 标签）系统

Wrye Bash 用 **Bash Tags** 判断「哪些插件应该把哪些数据导入补丁」。标签来源优先级（由低到高）：

1. 插件头部的 **Description（描述）**（可在 WB 内编辑）
2. LOOT 的 `taglist.yaml`（仅当本机找不到 LOOT masterlist 时）
3. LOOT 的 `masterlist.yaml`
4. LOOT 的 `userlist.yaml`
5. `[游戏]\Data\BashTags\[插件名].txt` 文件
6. **在 Wrye Bash 里手动设置的标签**（最高优先级）

### 与 Bashed Patch 相关的特殊标签

| 标签 | 含义 | 对补丁的影响 |
|------|------|--------------|
| **Delev** | 该 MOD 可删除等级列表条目 | 见 Leveled Lists |
| **Relev** | 该 MOD 可重新定级等级列表条目 | 见 Leveled Lists |
| **Filter** | 该插件不需要所有 master 都安装也能工作 | 缺失 master 时仍可被「过滤」后导入，而不是整个跳过 |
| **NoMerge** | 不该被合并（即使技术上可合并） | 不会出现在 Merge Patches 的待合并列表 |
| **Deactivate** | 应该被停用 | 重建时 WB 会询问停用该插件 |
| **IIM** | 用于 Item Interchange 模式 | 仅在 IIM 模式下被处理 |
| **MustBeActiveIfImported** | 即使被导入补丁也必须保持激活 | WB 不会询问停用它 |

### 手动管理标签
- 在 Mods 侧栏的 **Bash Tags** 字段上方点 **+** 按钮，勾选/取消标签；选中后点 **−** 移除。
- 右键 Bash Tags 字段：可选 **Automatic（回到自动）**、**Copy to Description（写回插件描述）**、**Copy to BashTags（生成 Data\BashTags\xxx.txt）**。
- 构建补丁时，补丁日志的「Active Plugins」一节会列出每个插件当前生效的标签，方便核对。

> 若日志提示某插件「Plugins Needing Filter Tag」：说明它有 import 类标签但 master 缺失且未标 `Filter`，被跳过了。给它加 `Filter` 标签或装齐 master 即可。

---

## 六、构建过程与产物

点 **Build Patch** 后，WB 按以下阶段执行（见 `patch_files.py`）：

1. **Preparing（准备）**：各 Patcher 收集来源数据。
2. **Processing（处理）**：建立读取/写入工厂。
3. **Scanning（扫描）**：逐个加载插件，合并被Merge的、扫描被激活的、过滤 Filter 插件，依次喂给各 Patcher。
4. **Completing（完成）**：各 Patcher 生成记录、裁剪未改动记录、转换 FormID。
5. **保存**：写回 `Bashed Patch, 0.esp`。

完成后：

- 弹出**日志窗口**（同时生成 `Data\Docs\Bashed Patch, 0.txt` 与对应的 `.html`），里面包含：
  - 日期/耗时；
  - **Skipped Imports**（被跳过的导入，因依赖缺失/未激活的插件）；
  - **Plugins Needing Filter Tag**；
  - **Load Error Plugins**（加载出错被跳过）；
  - **World Orphans / Compiled All** 等告警；
  - 完整的 **Active Plugins** 列表（含版本号与标签）。
- 若某个顶级分组所依赖的 master 数量超过游戏上限（`bush.game.Esp.master_limit`：Skyrim LE 为 255、Skyrim SE 为 253），WB 会**自动拆分**为 `Bashed Patch, 0-1.esp`、`-2.esp`…，并提示你删除不再需要的旧拆分件。给补丁打 ESL 标记只是省一个加载槽位，**不会**提高这个上限。
- 若游戏支持 ESL 且设置 `bash.mods.auto_flag_esl` 开启、且补丁新增记录 ≤ 2048，补丁会被**自动 ESL 标记**以省一个槽位。
- 构建后 WB 会尝试**激活** Bashed Patch（及其拆分件）；若设置 `PromptActivateBashedPatch` 开启，会询问你是否激活。

> 构建前若检测到**缺失 master** 或 **delinquent master（插件排在它自己的 master 之前）**，WB 会弹出错误对话框并**中止**构建——请先修正加载顺序（可用 LOOT 排序）。

---

## 七、配置导入 / 导出与复用

- **Export / Import**：把整套 Patcher 配置存成 `.dat` 文件，方便在多套 MOD 方案间切换或备份。导入时兼容旧版「Python」格式；过老的 CBash 格式会提示无法使用。
- **Revert To Saved / Revert To Default**：快速回退到「上次保存」或「出厂默认」。
- 配置会随 `Bashed Patch, 0.esp` 的表属性 `bash.patch.configs` 一起保存，下次重建自动载入。

---

## 八、实战步骤（推荐流程）

1. 用 LOOT（或 WB 自带排序）排好加载顺序，确定最终 MOD 清单。
2. 确认各 MOD 的 Bash Tags 正确（尤其 `Delev`/`Relev`/`Filter`）。
3. 右键 `Bashed Patch, 0.esp` → **Rebuild Patch…**。
4. 在对话框里：
   - General：勾选 **Merge Patches** 并勾选要合并的小补丁；
   - Importers：保留默认的自动勾选（按标签），按需调整 Graphics/Names/Sounds 等「看喜好」项；
   - Tweakers：确认 **Tweak Assorted（含 Summoning Absorption Fix）** 与 **Tweak Settings** 已启用，按需开其它；
   - Special：保留 **Leveled Lists / Contents Checker / Timescale Checker** 启用。
5. 点 **Build Patch**，等待完成，阅读日志有无 Skipped / Load Error 警告。
6. 确认 `Bashed Patch, 0.esp` 位于加载顺序末尾并已激活。

---

## 九、排错速查

| 现象 | 原因 / 处理 |
|------|-------------|
| 构建前弹「missing masters / delinquent」错误 | 有插件缺 master 或排在 master 之前；用排序工具修正后再构建。 |
| 日志里 **Skipped Imports** | 某导入依赖的插件缺失或未激活；停用该导入源，或装齐/激活依赖。 |
| 日志里 **Plugins Needing Filter Tag** | 插件有 import 标签但 master 缺失且未标 Filter；加 `Filter` 标签或装齐 master。 |
| **Load Error Plugins** | 插件格式损坏；看 BashBugDump，修复或移除该插件。 |
| 合并后游戏报缺 ESP | 你把被合并的 MOD 从 Data 删了；重建前必须保留它们。 |
| 补丁被拆成多个 `-N.esp` | master 数超限，属正常；保留拆分件并激活，删除提示里标注「不再需要」的旧件。 |

---

## 十、不同游戏的可用 Patcher 差异

本文清单针对 **Skyrim / Skyrim SE**。其它游戏的 Patcher 集合由 `bush.game.patchers` 决定（源码 `game/<游戏>/__init__.py`），并在 `gui_patchers.initPatchers()` 里据此实例化。例如：

- **Oblivion / Nehrim**：额外有 Import Actors: Faces、Import Races: Relations、Import Scripts、Import Roads，以及 Special 里的 **Race Checker / NPC Checker**。
- **Fallout 3 / NV**：额外有 Import Weapon Modifications、FormID Lists、Replace Form IDs 等。
- **Fallout 4**：部分 Import（Cells/Graphics/Sounds/Spell Stats/Stats/Text）不可用，且无 Tweak Clothes。

判断某个 Patcher 是否在你的游戏里出现，最直接的办法就是打开 **Rebuild Patch…** 对话框看左侧列表——那里列出的就是当前游戏实际支持的的全部 Patcher。

---

*参考源码：`Mopy/bash/basher/gui_patchers.py`、`Mopy/bash/basher/patcher_dialog.py`、`Mopy/bash/patcher/patch_files.py`、`Mopy/bash/basher/mod_links.py`、`Mopy/bash/game/skyrim/__init__.py`；官方文档：`Mopy/Docs/Wrye Bash General Readme.html`、`Wrye Bash Advanced Readme.html`。*
