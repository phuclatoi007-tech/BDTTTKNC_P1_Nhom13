# -*- coding: utf-8 -*-
"""
run_experiments.py - Tự động hóa thực nghiệm benchmark toàn diện cho Nhóm 13
Dự án 1: Pacman - Tìm kiếm và Trò chơi đối kháng
Học phần: Biểu diễn tri thức và tìm kiếm nâng cao (UET.AI2014)
"""
import time
import os
import sys

from src.engine import GameState, GameLoop
from src.agents import SearchAgent, MinimaxAgent, AlphaBetaAgent, ChaserGhostAgent

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_search_exp(map_file, algo, heuristic="mst"):
    agent = SearchAgent(algorithm_name=algo, heuristic=heuristic)
    loop = GameLoop(map_file, [agent], None)
    t0 = time.perf_counter()
    agent._plan_path(loop.state)
    t_total = time.perf_counter() - t0
    m = agent.metrics
    return {
        "map": os.path.basename(map_file),
        "algo": algo,
        "heuristic": heuristic if algo in ("astar", "greedy") else "None",
        "found": m.get("found", False),
        "steps": m.get("plan_length", 0),
        "cost": m.get("path_cost", 0),
        "expanded": m.get("expanded_nodes", 0),
        "frontier": m.get("max_frontier", 0),
        "time_ms": m.get("search_time", t_total) * 1000
    }

def run_adversarial_exp(map_file, depth):
    # Minimax
    loop_m = GameLoop(map_file, [MinimaxAgent(depth=depth)], None, ghost_factory=lambda i: ChaserGhostAgent(i))
    m_act = loop_m.agents[0].get_action(loop_m.state)
    m_val = loop_m.agents[0].last_eval_value
    m_nodes = loop_m.agents[0].expanded_nodes
    m_time = loop_m.agents[0].total_time * 1000

    # Alpha-Beta
    loop_a = GameLoop(map_file, [AlphaBetaAgent(depth=depth)], None, ghost_factory=lambda i: ChaserGhostAgent(i))
    a_act = loop_a.agents[0].get_action(loop_a.state)
    a_val = loop_a.agents[0].last_eval_value
    a_nodes = loop_a.agents[0].expanded_nodes
    a_time = loop_a.agents[0].total_time * 1000

    pruning_pct = ((m_nodes - a_nodes) / m_nodes * 100) if m_nodes > 0 else 0.0

    return {
        "map": os.path.basename(map_file),
        "depth": depth,
        "minimax": {"act": m_act, "val": m_val, "nodes": m_nodes, "time_ms": m_time},
        "alphabeta": {"act": a_act, "val": a_val, "nodes": a_nodes, "time_ms": a_time},
        "pruning_pct": pruning_pct
    }

def main():
    print("="*80)
    print("THỰC NGHIỆM 8.1: TÌM KIẾM ĐƯỜNG ĐI (PATHFINDING)")
    print("="*80)
    search_maps = [
        "maps/map3.txt",
        "maps/map_greedy_vs_astar.txt",
        "maps/map_hep.txt",
        "maps/map_khong_loi_giai_pacman.txt",
        "maps/map_khong_loi_giai_target.txt"
    ]
    algos = [
        ("dfs", None),
        ("bfs", None),
        ("ucs", None),
        ("greedy", "mst"),
        ("astar", "mst")
    ]
    
    res_81 = []
    for mf in search_maps:
        for algo, h in algos:
            r = run_search_exp(mf, algo, h)
            res_81.append(r)
            print(f"{r['map']:28} | {r['algo']:6} | h={r['heuristic']:5} | found={str(r['found']):5} | steps={r['steps']:2} | cost={r['cost']:2} | exp={r['expanded']:4} | time={r['time_ms']:6.2f}ms")

    print("\n" + "="*80)
    print("THỰC NGHIỆM 8.2: SO SÁNH HEURISTIC ĐA MỤC TIÊU (ALL-FOOD SEARCH)")
    print("="*80)
    multi_maps = [
        ("maps/map3.txt", 1),
        ("maps/map4.txt", 5),
        ("maps/map_greedy_vs_astar.txt", 9),
    ]
    h_configs = [
        ("ucs", None, "None (h=0)"),
        ("astar", "maze", "Farthest (Maze)"),
        ("astar", "mst", "MST-based"),
    ]
    res_82 = []
    for mf, food_count in multi_maps:
        for algo, h, label in h_configs:
            r = run_search_exp(mf, algo, h)
            r["food_count"] = food_count
            r["h_label"] = label
            res_82.append(r)
            print(f"{r['map']:28} | foods={food_count:2} | {algo:6} | {label:16} | steps={r['steps']:2} | cost={r['cost']:2} | exp={r['expanded']:5} | time={r['time_ms']:6.2f}ms")

    print("\n" + "="*80)
    print("THỰC NGHIỆM 8.3: SO SÁNH MINIMAX VÀ ALPHA-BETA")
    print("="*80)
    adv_configs = [
        ("maps/map_1ghost.txt", 1),
        ("maps/map_1ghost.txt", 2),
        ("maps/map_1ghost.txt", 3),
        ("maps/map_2ghost_1.txt", 1),
        ("maps/map_2ghost_1.txt", 2),
        ("maps/map_2ghost_1.txt", 3),
    ]
    res_83 = []
    for mf, d in adv_configs:
        r = run_adversarial_exp(mf, d)
        res_83.append(r)
        print(f"{r['map']:20} | depth={d} | Minimax: {r['minimax']['act']:5} val={r['minimax']['val']:7.2f} nodes={r['minimax']['nodes']:5} t={r['minimax']['time_ms']:6.2f}ms | AlphaBeta: {r['alphabeta']['act']:5} val={r['alphabeta']['val']:7.2f} nodes={r['alphabeta']['nodes']:5} t={r['alphabeta']['time_ms']:6.2f}ms | Pruning: {r['pruning_pct']:5.1f}%")

if __name__ == "__main__":
    main()
