import re

def transform_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    new_lines = []
    in_blockquote = False
    
    for line in lines:
        # 如果是引用块起始
        if line.startswith("> "):
            # 去除 "> " 前缀，保留内容
            stripped = line[2:]
            new_lines.append(stripped)
            in_blockquote = True
        elif line == ">":
            # 单独的 > 可能是空引用
            new_lines.append("")
        elif in_blockquote and not line.startswith(">"):
            # 引用块结束，加一个空行作为分隔
            if line.strip() != "":
                # 离开引用块
                in_blockquote = False
                new_lines.append("")
                new_lines.append(line)
            else:
                # 空行 - 继续但保持退出状态
                in_blockquote = False
                new_lines.append("")
        else:
            new_lines.append(line)
            if line.strip() == "":
                in_blockquote = False
    
    new_content = "\n".join(new_lines)
    
    # 清理多余的空行
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    return new_content

for f in ["研究现状.md", "研究方向方案.md"]:
    p = f
    transform_file(p)
    print(f"Processed: {p}")

# 验证
print("\n=== 研究现状.md 前 15 行 ===")
with open("研究现状.md", "r", encoding="utf-8") as f:
    for i, line in enumerate(f.readlines()[:15]):
        print(f"{i+1:2}: {line.rstrip()}")
