from collections import deque
import heapq

def bfs_shortest(graph, start, goal):
    """BFS - finds path with fewest edges. No limits."""
    if start == goal:
        return [start]
    
    visited = {start}
    q = deque([(start, [start])])
    
    while q:
        node, path = q.popleft()
        
        for neigh, _, _ in graph.adj.get(node, []):
            if neigh in visited:
                continue
            if neigh == goal:
                return path + [neigh]
            visited.add(neigh)
            q.append((neigh, path + [neigh]))
    
    return None

def dfs_path_safe(graph, start, goal, max_nodes=1000000, max_depth=5000):
    """
    Iterative DFS with optional limits for safety.
    Default limits are very high to handle any distance.
    """
    if start == goal:
        return [start]
    
    stack = [(start, [start])]
    visited_nodes = 0
    
    while stack:
        node, path = stack.pop()
        visited_nodes += 1
        
        if visited_nodes > max_nodes:
            return None
        
        if len(path) > max_depth:
            continue
        
        if node == goal:
            return path
        
        for neigh, _, _ in graph.adj.get(node, []):
            if neigh in path:
                continue
            stack.append((neigh, path + [neigh]))
    
    return None

def dijkstra(graph, start, goal):
    """Dijkstra's algorithm - finds shortest weighted path. No limits."""
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    
    while pq:
        d, node = heapq.heappop(pq)
        
        if d > dist.get(node, float("inf")):
            continue
        
        if node == goal:
            break
        
        for neigh, w, _ in graph.adj.get(node, []):
            nd = d + w
            if nd < dist.get(neigh, float("inf")):
                dist[neigh] = nd
                prev[neigh] = node
                heapq.heappush(pq, (nd, neigh))
    
    if goal not in prev and start != goal:
        return None, float("inf")
    
    path = []
    cur = goal
    while cur != start:
        path.append(cur)
        cur = prev.get(cur)
        if cur is None:
            return None, float("inf")
    path.append(start)
    path.reverse()
    
    return path, dist.get(goal, 0.0)

def enumerate_paths_dfs(graph, start, goal, max_paths=50, max_depth=500, max_total_weight=None):
    """
    DFS-based path enumerator - finds multiple alternative paths.
    User controls limits via parameters.
    """
    results = []
    stack = [(start, [start], 0.0)]
    iterations = 0
    
    while stack and len(results) < max_paths:
        iterations += 1
        
        # Very generous iteration limit for long distances
        if iterations > 5000000:  # 5 million iterations
            break
        
        node, path, tw = stack.pop()
        
        if len(path) > max_depth:
            continue
        
        if node == goal:
            results.append((path, tw))
            if len(results) >= max_paths:
                break
            continue
        
        neighbors = graph.adj.get(node, [])
        
        for neigh, w, _ in neighbors:
            if neigh in path:
                continue
            
            new_tw = tw + w
            
            if max_total_weight and new_tw > max_total_weight:
                continue
            
            stack.append((neigh, path + [neigh], new_tw))
    
    return results