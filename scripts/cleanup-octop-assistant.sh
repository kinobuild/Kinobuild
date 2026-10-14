#!/usr/bin/env bash
# 从已建 agent 的工作区软删除 octop-assistant 技能（用户端立即不再显示）
#
# 背景：该技能来自 general-assistant 专家模板，模板改动只影响新建 agent；
# 已存在的 agent 工作区里是拷贝，需要逐个软删除（写入 removed: true 标记）。
#
# 用法：
#   1. 在服务器上拿到管理员 JWT（浏览器 F12 → Application → Local Storage → token）
#   2. BASE=https://kinoguild.xingtudesign.com TOKEN=<jwt> bash cleanup-octop-assistant.sh

set -euo pipefail

BASE="${BASE:-http://127.0.0.1:8088}"
TOKEN="${TOKEN:?需要设置 TOKEN=<管理员 JWT>}"
SKILL="octop-assistant"

echo "目标: $BASE"
echo

# 1) 列出所有 agent
agents=$(curl -sS --max-time 30 "$BASE/api/agents?scope=all" -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json; d=json.load(sys.stdin); [print(a["agent_id"]) for a in (d if isinstance(d,list) else d.get("agents",[]))]')

if [ -z "$agents" ]; then
  echo "没有拿到任何 agent，检查 TOKEN 是否有效"
  exit 1
fi

echo "共 $(echo "$agents" | wc -l | tr -d ' ') 个 agent"
echo

hit=0
for a in $agents; do
  # 只看该 agent 是否有这个技能
  has=$(curl -sS --max-time 20 "$BASE/api/agents/$a/skills" -H "Authorization: Bearer $TOKEN" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('1' if any(s.get('slug')=='$SKILL' for s in d) else '')" 2>/dev/null || true)

  if [ -n "$has" ]; then
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 -X DELETE \
      "$BASE/api/agents/$a/skills/$SKILL" -H "Authorization: Bearer $TOKEN")
    printf "  %-10s 删除 → HTTP %s\n" "$a" "$code"
    hit=$((hit + 1))
  fi
done

echo
if [ "$hit" -eq 0 ]; then
  echo "没有 agent 带这个技能（可能已经清理过）"
else
  echo "已处理 $hit 个 agent"
fi

echo
echo "验证：再跑一次本脚本，应显示「没有 agent 带这个技能」。"
echo "注意：这一层只清理已建 agent；要让新建 agent 也干净，"
echo "      需要拉取包含 7601ddaa 的代码并重新构建镜像。"
