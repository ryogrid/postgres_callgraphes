#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import networkx as nx
from collections import deque

def parse_dotfile(filename):
    """
    .dotファイルから "XXX" -> "YYY"; の形式のエッジを抽出し (src, dst) のタプルで返す。
    """
    edges = []
    edge_pattern = re.compile(r'^\s*"([^"]+)"\s*->\s*"([^"]+)";')

    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            m = edge_pattern.match(line)
            if m:
                src, dst = m.groups()
                edges.append((src, dst))
    return edges


def build_digraph(edges):
    """
    与えられたエッジリストから NetworkX DiGraph を構築して返す
    """
    G = nx.DiGraph()
    for src, dst in edges:
        G.add_edge(src, dst)
    return G


def is_ignored_node(node: str) -> bool:
    """
    mainノードを除き、ノード名が小文字で始まるノードは無視する。
    - node が "main" の場合は無視しない。
    - それ以外で先頭文字が小文字 (a-z) の場合は無視する。
    """
    if node == "main":
        return False
    # 先頭文字が小文字かどうか
    return len(node) > 0 and node[0].islower()


def find_root_candidates(graph):
    """
    グラフ中のノードから「main」または末尾が「Main」のものをルート候補として返す。
    ただし、is_ignored_node(node) == True のノードは候補から除外。
    """
    roots = []
    for node in graph.nodes():
        if not is_ignored_node(node):  # 小文字開始かつ "main" でないものは無視
            if node == 'main' or node.endswith('Main'):
                roots.append(node)
    return roots


def collect_subgraph_nodes_up_to_3_hops(graph, root):
    """
    root から最大3ホップ以内で到達可能なノードを BFS で探索。
    - ルート以外の末尾 "Main" ノードに到達した場合は、そのノード自身は含むが
      そこから先は探索を進めない。
    - mainノードを除き、小文字で始まるノードは無視する（visited にも入れない）。
    """
    visited = set()
    queue = deque()

    # ルートは無視対象ではないはずだが、一応チェックしてから入れる
    if not is_ignored_node(root):
        queue.append((root, 0))
        visited.add(root)

    while queue:
        current_node, depth = queue.popleft()

        # 末尾が "Main" で、かつルートでない場合は先を辿らない
        if current_node != root and current_node.endswith("Main"):
            continue

        # 3ホップ以内なら子ノードを探索
        if depth < 3:
            for nxt in graph.successors(current_node):
                # 小文字開始ノード (かつ "main" でない) は無視
                if is_ignored_node(nxt):
                    continue

                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, depth + 1))

    return visited


def filter_sub_edges(edges, sub_nodes, root):
    """
    sub_nodes に含まれるノード間のエッジのみ抽出。
    さらに「root以外の末尾 'Main' ノード s から出るエッジ」は除外。
    """
    sub_edges = []
    for (s, t) in edges:
        if s in sub_nodes and t in sub_nodes:
            # ルート以外で末尾 "Main" のノード s からのエッジは含めない
            if s != root and s.endswith("Main"):
                continue
            sub_edges.append((s, t))
    return sub_edges


def write_subgraph_dot(output_filename, root, subgraph_edges):
    """
    要件にある固定フォーマットで .dot ファイルを書き出す。
    """
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write("digraph cflow {\n")
        f.write("    rankdir=TB;\n")
        f.write("    node [shape=box];\n")
        f.write("    overlap=false;\n")
        f.write("    splines=true;\n")
        f.write(f"    root=\"{root}\";\n\n")

        for (src, dst) in subgraph_edges:
            f.write(f"    \"{src}\" -> \"{dst}\";\n")

        f.write("}\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python split_graph.py <input.dot>")
        sys.exit(1)

    input_filename = sys.argv[1]

    # 1. DOTファイルからエッジを抽出
    edges = parse_dotfile(input_filename)

    # 2. DiGraphを構築
    G = build_digraph(edges)

    # 3. ルート候補 (main or 末尾が Main のノード) の取得
    root_candidates = find_root_candidates(G)
    if not root_candidates:
        print("No root candidates found ('main' or '*Main'). Nothing to do.")
        return

    # 4. 各ルートごとに最大3ホップまで辿った部分グラフを抽出・出力
    for root in root_candidates:
        # BFSでノード集合を取得
        sub_nodes = collect_subgraph_nodes_up_to_3_hops(G, root)
        # 無視対象ノード(小文字始まり)はここでも含まないが、理論上もう既に入っていないはず

        # エッジをフィルタ
        sub_edges = filter_sub_edges(edges, sub_nodes, root)

        # 書き出し
        output_filename = f"{root}.dot"
        write_subgraph_dot(output_filename, root, sub_edges)
        print(f"Generated: {output_filename}")


if __name__ == "__main__":
    main()

