#!/usr/bin/env bash
# motion-scan.sh
#
# 工程化兜底校验：扫描 design-style-extractor 产出的 style.skill.md 文件，
# 确认 motion 段不包含违规模式（cubic-bezier 数值 / 带 ms 或 s 单位的 duration /
# transition: 或 animation: CSS 语句）。
#
# 用法:
#   bash motion-scan.sh <path-to-style.skill.md>
#
# 退出码:
#   0  motion 段干净（或文件中没有 motion 段，无可扫描内容）
#   1  motion 段包含至少一项违规模式
#   2  参数错误 / 文件不存在
#
# 设计说明:
#   - bash + grep + awk 实现，便于用户审阅、零依赖
#   - awk 抽取 "## motion" 段（直到下一个 ^## 或 ^# 行结束），grep -nE 跑五条违规正则
#   - 已知 false negative: 用 ".3s" 这种省略前导 0 的写法不会被命中，可在后续版本扩展正则

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <path-to-style.skill.md>" >&2
    exit 2
fi

FILE="$1"

if [[ ! -f "$FILE" ]]; then
    echo "Error: file not found: $FILE" >&2
    exit 2
fi

# 抽取 motion 段：从 "## motion" 行（含子标题，如 "## motion (性格描述)"）开始，
# 到下一个 ^## 或 ^# 行结束。保留原始行号，便于报告位置。
MOTION_SECTION=$(awk '
    BEGIN { in_motion = 0 }
    /^## motion/ { in_motion = 1; print NR": "$0; next }
    /^## / && in_motion { in_motion = 0; next }
    /^# / && in_motion { in_motion = 0; next }
    in_motion { print NR": "$0 }
' "$FILE")

if [[ -z "$MOTION_SECTION" ]]; then
    echo "OK: no '## motion' section found in $FILE (nothing to scan)."
    exit 0
fi

VIOLATIONS=0

scan() {
    local pattern="$1"
    local description="$2"
    local matches
    matches=$(echo "$MOTION_SECTION" | grep -nE "$pattern" || true)
    if [[ -n "$matches" ]]; then
        echo "[VIOLATION] $description"
        echo "  pattern: $pattern"
        echo "$matches" | sed 's/^/  /'
        echo ""
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
}

# 五条违规正则，对应 skill v2 第 4 步硬性禁止条款
scan 'cubic-bezier\([^)]*\)'                   "cubic-bezier numerical value"
scan '[0-9]+[[:space:]]*ms\b'                  "duration with ms unit"
scan '[0-9]+(\.[0-9]+)?[[:space:]]*s\b'        "duration with s unit"
scan 'transition[[:space:]]*:'                 "transition CSS statement"
scan 'animation[[:space:]]*:'                  "animation CSS statement"

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "Total violation categories: $VIOLATIONS"
    echo "Action required: rewrite the motion section using only qualitative / character descriptions."
    echo "See design-style-extractor.skill.md Step 4 for forbidden-clause specifics."
    exit 1
fi

echo "OK: motion section clean (no forbidden numerical values or CSS statements)."
exit 0
