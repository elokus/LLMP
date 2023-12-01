import streamlit as st
import scripts.components as components
import scripts.utils as utils


base_path = "../data/jobs"


def main(base_path):
    # Load job register
    selected_job_id, base_path = components.display_sidebar(base_path)
    # Add a top navigation menu
    menu = ["Metadata", "Generation Log", "Event Log"]

    # Load job data
    metadata, event_logs, generation_logs = utils.load_job(base_path, selected_job_id)

    components.display_header(metadata, selected_job_id)
    components.display_job_sidebar(metadata, event_logs)

    tab1, tab2, tab3 = st.tabs(menu)

    # tab 1 - metadata
    components.display_metadata(tab1, metadata, base_path, selected_job_id)

    # tab 2 - generation log
    components.display_generation_logs(tab2, generation_logs, base_path, selected_job_id)

    # tab 3 - event log
    components.display_event_logs(tab3, event_logs)


if __name__ == "__main__":
    main(base_path)