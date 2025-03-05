from typing import List, Dict, Any, Optional
import math

def calculate_project_buffer(task_durations: List[float], buffer_factor: float = 0.5) -> float:
    """
    Calculate project buffer using the square root of the sum of squares method
    
    Args:
        task_durations: List of task durations (50% estimates)
        buffer_factor: Factor to adjust buffer size (default: 0.5)
        
    Returns:
        Project buffer size in the same units as task_durations
    """
    # Calculate the sum of squares of task durations
    sum_of_squares = sum(duration ** 2 for duration in task_durations)
    
    # Calculate buffer using square root of sum of squares
    buffer = math.sqrt(sum_of_squares) * buffer_factor
    
    return buffer

def calculate_feeding_buffer(task_durations: List[float], buffer_factor: float = 0.5) -> float:
    """
    Calculate feeding buffer for non-critical chains
    
    Args:
        task_durations: List of task durations in the feeding chain
        buffer_factor: Factor to adjust buffer size (default: 0.5)
        
    Returns:
        Feeding buffer size in the same units as task_durations
    """
    return calculate_project_buffer(task_durations, buffer_factor)

def calculate_buffer_status(buffer_size: float, buffer_consumed: float) -> str:
    """
    Calculate buffer status based on consumption percentage
    
    Args:
        buffer_size: Total buffer size
        buffer_consumed: Amount of buffer consumed
        
    Returns:
        Buffer status: "green", "yellow", or "red"
    """
    if buffer_size <= 0:
        return "red"
        
    consumption_percentage = (buffer_consumed / buffer_size) * 100
    
    if consumption_percentage <= 33:
        return "green"
    elif consumption_percentage <= 66:
        return "yellow"
    else:
        return "red"

def calculate_estimated_completion_date(
    project_progress: float,
    buffer_consumption: float,
    start_date,
    target_end_date
) -> Optional[Any]:
    """
    Calculate estimated completion date based on current progress and buffer consumption
    
    Args:
        project_progress: Percentage of project completed (0-100)
        buffer_consumption: Percentage of buffer consumed (0-100)
        start_date: Project start date
        target_end_date: Target end date
        
    Returns:
        Estimated completion date
    """
    if project_progress <= 0:
        return target_end_date
        
    # Calculate total project duration in days
    total_duration = (target_end_date - start_date).days
    
    # Calculate expected progress based on elapsed time
    import datetime
    today = datetime.datetime.now().date()
    elapsed_days = (today - start_date.date()).days
    expected_progress = (elapsed_days / total_duration) * 100
    
    # Calculate progress ratio (actual vs expected)
    if expected_progress <= 0:
        progress_ratio = 1.0
    else:
        progress_ratio = project_progress / expected_progress
    
    # Adjust for buffer consumption
    if project_progress < 100:
        # Calculate buffer impact
        buffer_impact = buffer_consumption / project_progress
        
        # Adjust progress ratio based on buffer consumption
        adjusted_ratio = progress_ratio * (1 - (buffer_impact * 0.5))
        
        # Calculate remaining duration
        remaining_percentage = 100 - project_progress
        remaining_duration = (remaining_percentage / 100) * total_duration
        
        # Adjust remaining duration based on progress ratio
        if adjusted_ratio > 0:
            adjusted_remaining = remaining_duration / adjusted_ratio
        else:
            adjusted_remaining = remaining_duration * 2
        
        # Calculate estimated completion date
        estimated_completion = today + datetime.timedelta(days=adjusted_remaining)
        
        return estimated_completion
    
    return target_end_date