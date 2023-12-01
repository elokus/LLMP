import streamlit as st
import pandas as pd
import json
import os

import uuid

def is_valid_uuid(s):
    try:
        uuid.UUID(str(s))
        return True
    except ValueError:
        return False


def load_json(file):
    with open(file, 'r') as f:
        data = json.load(f)
    return data


def load_registry(base_path):
    with open(os.path.join(base_path, 'job_register.json'), 'r') as f:
        job_register = json.load(f)
    return job_register


def save_json(data, filename, base_path):
    old_data = load_json(filename)
    if old_data["job_name"] != data["job_name"]:
        registry = load_registry(base_path)
        registry[data["job_name"]] = registry.pop(old_data["job_name"])
        with open(os.path.join(base_path, 'job_register.json'), 'w') as f:
            json.dump(registry, f)

    st.write(f"Saving changes to {filename}")
    st.write(json.dumps(data))

    with open(filename, 'w') as f:
        json.dump(data, f)

def _display_metadata(metadata):
    edited_metadata = {"idx": metadata["idx"]}
    st.write(f"Job ID: {metadata['idx']}")
    edited_metadata["job_name"] = st.text_input("Job name", metadata['job_name'])
    edited_metadata["instruction"] = st.text_area("Instruction", metadata['instruction'])

    for key, value in metadata.items():
        if key in ["idx", "instruction", "job_name"]:
            continue
        elif key in ['input_model', 'output_model', 'config', 'event_log']:
            with st.expander(f"{key}"):
                st.write(f"{key}:")
                edited_metadata[key] = display_editable_data_by_type(key, value)
        else:
            edited_metadata[key] = display_editable_data_by_type(key, value)
    return edited_metadata


def display_editable_list(key, value, unique_key=None):
    if unique_key is None:
        unique_key = key
    edited_value = []
    for i, item in enumerate(value):
        unique_key = f"{unique_key}_{i}"
        edited_value.append(display_editable_data_by_type(f"{key} {i}", item, unique_key=unique_key))
    return edited_value


def display_editable_dict(key, value, unique_key=None):
    if unique_key is None:
        unique_key = key
    edited_value = {}
    for sub_key, sub_value in value.items():
        unique_key = f"{unique_key}_{sub_key}"
        edited_value[sub_key] = display_editable_data_by_type(sub_key, sub_value, unique_key=unique_key)
    return edited_value


def display_editable_data_by_type(key, value, unique_key=None):
    if unique_key is None:
        unique_key = key
    if isinstance(value, list):
        return display_editable_list(key, value, unique_key)
    elif isinstance(value, dict):
        return display_editable_dict(key, value, unique_key)
    elif isinstance(value, bool):
        return st.checkbox(key, value, key=unique_key)
    elif isinstance(value, str):
        return st.text_input(key, value, key=unique_key)
    elif isinstance(value, int):
        return st.number_input(key, value, key=unique_key)
    else:
        return st.text_input(key, str(value), key=unique_key)


def display_model(model, prefix):
    edited_model = {"lines": []}
    for i, line in enumerate(model["lines"]):
        edited_line = {}
        for key, value in line.items():
            unique_key = f"{prefix}_{i}_{key}"
            if isinstance(value, bool):
                edited_value = st.checkbox(key, value, key=unique_key)
            elif isinstance(value, str):
                edited_value = st.text_input(key, value, key=unique_key)
            elif isinstance(value, int):
                edited_value = st.number_input(key, value, key=unique_key)
            else:
                edited_value = st.text_input(key, str(value), key=unique_key)
            edited_line[key] = edited_value
        edited_model["lines"].append(edited_line)
    return edited_model


def display_generation_entry(entry):
    st.write(f"Event ID: {entry['event_id']}")
    st.json(entry['input'])

    output_dict = {}
    for key, value in entry['output'].items():
        if isinstance(value, list):
            output_dict[key] = []
            for i, item in enumerate(value):
                unique_key = f"{entry['event_id']}_{key}_{i}"
                edited_item = st.text_input(f"{key} {i}", item, key=unique_key)
                output_dict[key].append(edited_item)
        else:
            unique_key = f"{entry['event_id']}_{key}"
            edited_value = st.text_input(key, value, key=unique_key)
            output_dict[key] = edited_value

    # Return the edited entry
    return {"event_id": entry['event_id'], "input": entry['input'], "output": output_dict}

base_path = 'C:/Users/Lukasz/Codes/LLMP/_notebooks/data/jobs'  # replace with your base directory

# Load job register
with open(os.path.join(base_path, 'job_register.json'), 'r') as f:
    job_register = json.load(f)

# Display job names in sidebar
selected_job_name = st.sidebar.selectbox("Select a job", [n for n in job_register.keys() if not is_valid_uuid(n)])

# Get selected job id
selected_job_id = job_register[selected_job_name]

# Construct paths to metadata.json and generation_log.json
metadata_path = os.path.join(base_path, selected_job_id, 'metadata.json')
generation_log_path = os.path.join(base_path, selected_job_id, 'generation_log.jsonl')

# Add a top navigation menu
menu = ["Metadata", "Generation Log"]
choice = st.radio("Menu", menu, horizontal=True)

# Create placeholders for the outputs
metadata_placeholder = st.empty()
generation_log_placeholder = st.empty()

# Load and display metadata and generation log
if os.path.exists(metadata_path) and os.path.exists(generation_log_path):
    if choice == "Metadata":
        metadata = load_json(metadata_path)
        edited_metadata = display_metadata(metadata)

        # Assuming you have a button that triggers the save operation
        if st.button('Save changes'):
            # Save JSON data back to the file
            save_json(edited_metadata, metadata_path, base_path)
    elif choice == "Generation Log":
        generation_log_placeholder.write('Generation Log:')
        with open(generation_log_path, 'r') as f:
            for line in f:
                entry = json.loads(line)
                display_generation_entry(entry)
else:
    st.write(f"No data found for job {selected_job_name}")
    st.write(f"in path: {metadata_path}")
