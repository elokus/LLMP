import pandas as pd
import streamlit as st
import utils


# ============================== Main ==============================


def display_header(metadata, job_id):
    if metadata is not None:
        st.title(metadata["job_name"])
        st.write(f"Job ID: {job_id}")
        st.markdown("Here you can monitor the performance and configuration of your job."
                    " You can edit metadata, examples and previous generations."
                    " Edits in metadata and examples will create a new version of the job."
                    " Old version settings will be preserved, so you can always roll back to a previous version.")
    else:
        st.write("Job loading failed!")


# === Sidebar ===


def display_sidebar(base_path):
    st.sidebar.title("LLMP Monitor")
    edited_base_path = st.sidebar.text_input("Base path", base_path)
    if edited_base_path != base_path:
        st.cache.clear_cache()
        base_path = edited_base_path
    st.markdown("---")
    st.sidebar.write("Select a job to monitor:")
    job_register = utils.load_registry(base_path)

    # Display job names in sidebar
    job_names = [n for n in job_register.keys() if not utils.is_valid_uuid(n)]
    selected_job_name = st.sidebar.selectbox("Select a job", job_names)
    selected_job_id = job_register[selected_job_name]
    return selected_job_id, base_path


def display_job_sidebar(metadata, event_logs):
    if not metadata or not event_logs:
        st.sidebar.write("...")
        return

    st.sidebar.markdown("---")
    # version
    st.sidebar.markdown(f"### Current Version: {metadata['version']}")

    # metrics
    generation_events = [event for event in event_logs if event["event_type"] == "generation"]
    if len(generation_events) > 0:
        metrics = [event["event_metrics"] for event in generation_events]
        df = pd.DataFrame(metrics)



        # Execution time
        mean_exec_time = df["execution_time"].mean()
        max_exec_time = df["execution_time"].max()
        delta = mean_exec_time - max_exec_time
        st.sidebar.metric("Mean execution time", value=f"{mean_exec_time:.2f} s", delta=f"{delta:.2f} s")

        # Token usage
        mean_token_usage = df["token_usage"].mean()
        max_token_usage = df["token_usage"].max()
        delta = mean_token_usage - max_token_usage
        st.sidebar.metric("Mean token usage", value=mean_token_usage, delta=delta)

        # failure rate
        failure_rate = df["failure_rate"].mean() -1
        max_failure_rate = df["failure_rate"].max() -1
        delta = failure_rate - max_failure_rate
        st.sidebar.metric("Mean failure rate", value=failure_rate, delta=delta)


# ============================== Tabs ==============================


# === Metadata ===


def display_metadata(tab, metadata, base_path, job_id):
    if metadata is None:
        tab.write("No metadata found!")
        return None

    edited_metadata = display_editable_metadata(tab, metadata)

    if tab.button("Save changes"):
        utils.save_metadata(edited_metadata, 'metadata.json', base_path, job_id)
        tab.write("Changes saved!")


def display_editable_metadata(tab, metadata):

    edited_metadata = {}
    edited_metadata["idx"] = metadata["idx"]
    edited_metadata["job_name"] = tab.text_input("Job name", metadata['job_name'])
    edited_metadata["instruction"] = tab.text_area("Instruction", metadata['instruction'])

    for key, value in metadata.items():
        if key in ["idx", "instruction", "job_name"]:
            continue

        elif key in ['input_model', 'output_model']:
            with tab.expander(f"{key}"):
                edited_metadata[key] = utils.editable_io_model(st, value, key)
        elif key in ['config', 'event_log']:
            with tab.expander(f"{key}"):
                edited_metadata[key] = utils.editable_data_in_tab(st, key, value)
        else:
            edited_metadata[key] = utils.editable_data_in_tab(tab, key, value)
    return edited_metadata


# === Generation Log ===


def display_generation_logs(tab, generation_logs, base_path, job_id):
    if generation_logs is None:
        tab.write("No generation log found!")
        return None
    tab.markdown("## Generation Logs")
    tab.markdown("Submit your changes by clicking the 'Save changes' button at the bottom of the page.\n"
                 "Changes to the output of a generation event will be marked as 'Human Verified' in the event log and "
                 "will have a higher rank (weight) in optimization runs.\n"
                 "When you click 'Save changes', all generation events will be marked as 'Human Verified'.\n\n---")
    generation_log_entries(tab, generation_logs, base_path, job_id)


def generation_log_entries(tab, generation_logs, base_path, job_id):
    edited_generation_logs = []
    for i, entry in enumerate(generation_logs):
        unique_key = f"gen_{i}_{entry['event_id']}"
        edited_entry = _generation_log_entry(tab, entry)
        if tab.button("Save changes", key=unique_key):
            utils.update_jsonl_entry(base_path, job_id, "generation_log.jsonl", edited_entry)
            tab.write("Changes saved!")
        edited_generation_logs.append(edited_entry)
        tab.divider()


def _generation_log_entry(tab, entry):
    col1, col2 = tab.columns([2, 3])
    col1.markdown("### Event ID")
    col2.write(" ")
    verified = entry.get("verified")
    verified = col2.checkbox(
        label=f"verified",
        value=verified,
        key=f"{entry['event_id']}_verified",
    )
    tab.write(f":violet[{entry['event_id']}]")
    tab.write(" ")
    col1, col2 = tab.columns([2,3])
    col1.markdown("##### Input")
    col1.json(entry['input'])

    output_dict = {}
    col2.markdown("##### Output")
    for key, value in entry['output'].items():
        if isinstance(value, list):
            if len(value) > 0 and isinstance(value[0], dict):
                output_dict[key] = col2.data_editor(value, key=f"{entry['event_id']}_{key}")
            else:
                output_dict[key] = []
                for i, item in enumerate(value):
                    unique_key = f"{entry['event_id']}_{key}_{i}"
                    edited_item = col2.text_input(f"{key} {i}", item, key=unique_key)
                    output_dict[key].append(edited_item)
        else:
            unique_key = f"{entry['event_id']}_{key}"
            edited_value = col2.text_input(key, value, key=unique_key)
            output_dict[key] = edited_value

    # Return the edited entry
    return {"event_id": entry['event_id'], "input": entry['input'], "output": output_dict, "verified": verified}


# === Event Log ===

def display_event_logs(tab, event_logs):
    if event_logs is None:
        tab.write("No event log found!")
        return None

    for event in event_logs:
        display_event_entry(tab, event)
        tab.markdown("---")


def display_event_entry(tab, event):
    tab.write(f"Event ID: {event['event_id']}")
    tab.json(event)



