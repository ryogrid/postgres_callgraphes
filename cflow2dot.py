#!/usr/bin/env python3
import re
import sys

def parse_cflow_line(line: str):
    """
    cflow 出力の 1 行から以下の情報を取り出す:
      - indent_level: ネストレベル(推定)
      - func_name: 関数名
    取り出せない場合は (None, None) を返す。

    質問文で示された cflow 出力例:
         1 main: int (int argc, char *argv[]), <src/backend/main/main.c 71>
         2     pgwin32_install_crashdump_handler: <>
         3     get_progname: <>
         4     startup_hacks: void (const char *progname), <src/backend/main/main.c 283>
         5         setvbuf: <>
         6         WSAStartup: <>
         ...
    という形式を想定。
    """

    # 行末の不要な空白や改行を除去
    line = line.rstrip()
    if not line:
        return None, None

    # 行頭の空白＋行番号をパース
    #   例: "    1 main: int(...)"
    #        ^^^^ (空白)
    #            ^ (行番号 1)
    match_line_num = re.match(r'^\s*(\d+)(.*)$', line)
    if not match_line_num:
        return None, None

    line_number = match_line_num.group(1)
    rest = match_line_num.group(2)

    # 行番号の後に続く空白を調べてインデント量を取得
    #   例: "    main: int(...)"
    #        ↑ leading_spaces
    match_spaces = re.match(r'^(\s+)(.*)$', rest)
    if match_spaces:
        leading_spaces = match_spaces.group(1)
        after_spaces = match_spaces.group(2)
    else:
        leading_spaces = ""
        after_spaces = rest

    # cflow 出力では、呼び出し階層が 4 スペースごとに深くなるケースが多い
    indent_count = len(leading_spaces)
    indent_level = indent_count // 4

    # after_spaces から関数名を取り出す
    #   多くの場合 "funcName: 戻り値 (...) ," のような形
    #   最初の ':' の手前が関数名
    if ':' in after_spaces:
        func_name_part, _, _ = after_spaces.partition(':')
        func_name = func_name_part.strip()
    else:
        # ':' がない場合、たとえば "someFunc <>" のような行など
        # とりあえず全体を関数名としてみる
        func_name = after_spaces.strip()

    if not func_name:
        return None, None

    return indent_level, func_name


def cflow_to_dot(file_path: str) -> str:
    """
    cflow の出力 (質問文例にある形式) をパースし、
    Graphviz (DOT 形式) の文字列を生成して返す。
    """
    edges = set()  # (親関数, 子関数) のセット
    stack = []     # (indent_level, func_name) を保持するスタック

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            indent_level, func_name = parse_cflow_line(line)
            if func_name is None:
                continue

            # スタックの先頭が現在より同じか深いレベルなら pop
            while stack and stack[-1][0] >= indent_level:
                stack.pop()

            # 親子関係の登録
            if indent_level > 0 and stack:
                parent_func = stack[-1][1]
                edges.add((parent_func, func_name))

            # スタックに現在の関数を積む
            stack.append((indent_level, func_name))

    # DOT 形式の出力を組み立てる
    # 注意: 特殊文字を含む関数名の場合はダブルクォートで囲んでおく
    #       ここでは単純にダブルクォートで囲うことにする
    lines = []
    lines.append('digraph cflow {')
    lines.append('    rankdir=TB;')  # 上→下方向に階層を描画 (好みに応じて LR など)
    lines.append('    node [shape=box];')

    for src, dst in edges:
        # グラフ中のノード名として安全に扱うため、ダブルクォートで囲む
        s_quoted = f"\"{src}\""
        d_quoted = f"\"{dst}\""
        lines.append(f"    {s_quoted} -> {d_quoted};")

    lines.append('}')
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python cflow2dot.py <cflow_output.txt>", file=sys.stderr)
        sys.exit(1)

    file_path = sys.argv[1]
    dot_text = cflow_to_dot(file_path)
    print(dot_text)


if __name__ == "__main__":
    main()
