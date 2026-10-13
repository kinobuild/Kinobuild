"""电商视觉工坊 — 电商做图技能包（kind=skill）。

本插件**不自己出图**：出图由内置的 ``generate_image`` 工具完成，它已经支持
参考图、输出尺寸、批量张数、随机种子与去水印。

插件只负责把「电商主图」这件事的**行业知识**同步给 Agent：
平台规格、商品保真红线、prompt 结构、风格模板库。

放在 bundled/ 下意味着它随安装包分发；`octop init` / `octop run` 会把它复制到
``~/.octop/plugins/`` 并默认全局关闭，管理员在 Dashboard 插件页打开后，
再按 Agent 启用，技能才会同步进该 Agent 的工作区。
"""

from __future__ import annotations

from octop_harness.plugins import PluginContext


def setup(ctx: PluginContext) -> None:
    # 每个子目录须含 SKILL.md；Agent 启动时同步到工作区 skills/<name>/。
    ctx.skills("skills")
