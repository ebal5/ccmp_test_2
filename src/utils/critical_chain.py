from typing import List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session

from ..models import Task, Project

def calculate_critical_chain(db: Session, project_id: int) -> List[Task]:
    """
    Calculate the critical chain for a project
    
    Args:
        db: Database session
        project_id: Project ID
        
    Returns:
        List of tasks in the critical chain
    """
    # Get all tasks for the project
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # Build dependency graph
    dependency_graph = _build_dependency_graph(tasks)
    
    # Find all paths through the graph
    paths = _find_all_paths(dependency_graph)
    
    # Find the longest path (by duration)
    critical_chain = _find_longest_path(paths, tasks)
    
    # Update tasks in the database
    for task in tasks:
        task.is_critical_chain = task.id in critical_chain
        db.add(task)
    
    db.commit()
    
    # Return tasks in the critical chain
    return [task for task in tasks if task.id in critical_chain]

def _build_dependency_graph(tasks: List[Task]) -> Dict[int, List[int]]:
    """
    Build a dependency graph from tasks
    
    Args:
        tasks: List of tasks
        
    Returns:
        Dictionary mapping task IDs to lists of dependent task IDs
    """
    graph = {}
    
    for task in tasks:
        graph[task.id] = []
        
    for task in tasks:
        for dependency in task.dependencies:
            graph[dependency.id].append(task.id)
            
    return graph

def _find_all_paths(graph: Dict[int, List[int]]) -> List[List[int]]:
    """
    Find all paths through the dependency graph
    
    Args:
        graph: Dependency graph
        
    Returns:
        List of paths (each path is a list of task IDs)
    """
    # Find start nodes (no dependencies)
    start_nodes = []
    all_dependent_nodes = set()
    
    for node, dependents in graph.items():
        all_dependent_nodes.update(dependents)
        
    for node in graph:
        if node not in all_dependent_nodes:
            start_nodes.append(node)
            
    # Find all paths from start nodes
    all_paths = []
    
    for start_node in start_nodes:
        paths = _find_paths_from_node(graph, start_node)
        all_paths.extend(paths)
        
    return all_paths

def _find_paths_from_node(graph: Dict[int, List[int]], start_node: int, path: List[int] = None) -> List[List[int]]:
    """
    Find all paths from a start node
    
    Args:
        graph: Dependency graph
        start_node: Starting node
        path: Current path (for recursion)
        
    Returns:
        List of paths from the start node
    """
    if path is None:
        path = []
        
    current_path = path + [start_node]
    
    if not graph[start_node]:
        # End node
        return [current_path]
        
    paths = []
    
    for next_node in graph[start_node]:
        if next_node not in current_path:  # Avoid cycles
            new_paths = _find_paths_from_node(graph, next_node, current_path)
            paths.extend(new_paths)
            
    return paths

def _find_longest_path(paths: List[List[int]], tasks: List[Task]) -> List[int]:
    """
    Find the longest path by duration
    
    Args:
        paths: List of paths
        tasks: List of tasks
        
    Returns:
        The longest path (list of task IDs)
    """
    # Create a mapping of task IDs to tasks
    task_map = {task.id: task for task in tasks}
    
    longest_path = []
    longest_duration = 0
    
    for path in paths:
        duration = sum(task_map[task_id].estimated_time for task_id in path if task_id in task_map)
        
        if duration > longest_duration:
            longest_duration = duration
            longest_path = path
            
    return longest_path

def identify_feeding_chains(db: Session, project_id: int, critical_chain: List[int]) -> List[Tuple[List[int], int]]:
    """
    Identify feeding chains that merge into the critical chain
    
    Args:
        db: Database session
        project_id: Project ID
        critical_chain: List of task IDs in the critical chain
        
    Returns:
        List of tuples (feeding_chain, merge_point) where feeding_chain is a list of task IDs
        and merge_point is the task ID in the critical chain where the feeding chain merges
    """
    # Get all tasks for the project
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    
    # Build dependency graph
    dependency_graph = _build_dependency_graph(tasks)
    
    # Find all paths through the graph
    all_paths = _find_all_paths(dependency_graph)
    
    # Find feeding chains
    feeding_chains = []
    
    for path in all_paths:
        # Check if this path intersects with the critical chain
        intersection = set(path) & set(critical_chain)
        
        if intersection and set(path) != set(critical_chain):
            # This is a feeding chain
            # Find the merge point (first task in the intersection)
            merge_points = []
            for task_id in path:
                if task_id in critical_chain:
                    merge_points.append(task_id)
                    
            if merge_points:
                # Get the feeding chain (tasks before the merge point)
                merge_point = merge_points[0]
                merge_index = path.index(merge_point)
                feeding_chain = path[:merge_index]
                
                if feeding_chain:
                    feeding_chains.append((feeding_chain, merge_point))
                    
    return feeding_chains