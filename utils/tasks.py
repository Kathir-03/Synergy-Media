# tasks.py

from celery import Celery, group
# Import the state and agent functions from your original script
from streamlit_integration import (
    AgentState,
    transcription_agent,
    twitter_agent,
    linkedin_agent,
    instagram_agent
)

# Initialize Celery and connect it to your Redis server
app = Celery('tasks',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

# This is the master task your Streamlit app will call
@app.task(name='tasks.start_pipeline')
def start_repurposing_pipeline(video_url: str):
    """
    Master task that runs transcription, then launches parallel content generation.
    """
    # Step 1: Initialize the AgentState, just like your old main() function
    agent_state = AgentState(video_url)
    
    # Step 2: Run the transcription task first. This is a blocking call.
    # We call the function directly, as it will run within this master task.
    transcription_success = transcription_agent(agent_state)
    
    if not transcription_success:
        raise ValueError("Transcription failed, cannot proceed.")

    # Step 3: Create a group of parallel tasks to run the other agents.
    # .s() creates a "signature" of the task, packaging it up with its arguments.
    # We pass the entire state dictionary to each parallel task.
    parallel_tasks = group(
        twitter_task_worker.s(agent_state.state),
        linkedin_task_worker.s(agent_state.state),
        instagram_task_worker.s(agent_state.state),
    )

    # Step 4: Execute the group and wait for all tasks to finish.
    task_group_result = parallel_tasks.apply_async()
    results = task_group_result.get(timeout=600) 
    
    # Step 5: Process results into a clean dictionary to return to the front end.
    final_output = {
        "twitter_thread": results[0],
        "linkedin_pdf_path": "linkedin_post.pdf", # We know the filename
        "instagram_reel_path": "instagram_reel.mp4" # We know the filename
    }
    
    return final_output

# --- Worker Task Definitions ---
# We create new "worker" functions that know how to handle the AgentState.

@app.task
def twitter_task_worker(state_dict: dict):
    # Recreate the AgentState object from the dictionary
    agent_state = AgentState(state_dict['youtube_url'])
    agent_state.state = state_dict
    
    # Call the original twitter_agent function
    twitter_agent(agent_state)
    
    # Return the relevant piece of state
    return agent_state.get("twitter_thread")

@app.task
def linkedin_task_worker(state_dict: dict):
    agent_state = AgentState(state_dict['youtube_url'])
    agent_state.state = state_dict
    
    linkedin_agent(agent_state)
    
    # This task doesn't need to return anything as the filename is fixed
    return "linkedin_post.pdf" 

@app.task
def instagram_task_worker(state_dict: dict):
    agent_state = AgentState(state_dict['youtube_url'])
    agent_state.state = state_dict
    
    instagram_agent(agent_state)
    
    # This task doesn't need to return anything as the filename is fixed
    return "instagram_reel.mp4"