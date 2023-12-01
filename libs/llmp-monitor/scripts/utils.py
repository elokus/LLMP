import json
import os
import uuid
import streamlit as st


def is_valid_uuid(s):
    try:
        uuid.UUID(str(s))
        return True
    except ValueError:
        return False


def load_registry(base_path):
    with open(os.path.join(base_path, 'job_register.json'), 'r') as f:
        job_register = json.load(f)
    return job_register


def save_registry(job_register, base_path):
    with open(os.path.join(base_path, 'job_register.json'), 'w') as f:
        json.dump(job_register, f)


def update_jsonl_entry(base_path, job_id, filename, entry):
    filepath = os.path.join(base_path, job_id, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = [json.loads(line) for line in f]
        for i, item in enumerate(data):
            if item["event_id"] == entry["event_id"]:
                data[i] = entry
                break
        with open(filepath, 'w') as f:
            for item in data:
                json.dump(item, f)
                f.write('\n')
        return data
    return None


def append_jsonl_entry(base_path, job_id, filename, entry):
    filepath = os.path.join(base_path, job_id, filename)
    if os.path.exists(filepath):
        with open(filepath, 'a') as f:
            json.dump(entry, f)
            f.write('\n')
        return entry
    return None


def load_jsonl(base_path, job_id, filename):
    filepath = os.path.join(base_path, job_id, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = [json.loads(line) for line in f]
        return data
    return None

def load_json(base_path, job_id, filename):
    filepath = os.path.join(base_path, job_id, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data
    return None


def save_metadata(data, filename, base_path, job_id):
    old_data = load_json(base_path, data["idx"], filename)
    if compare_metadata(old_data, data):
        data["version"] = old_data["version"] + 1
        append_jsonl_entry(base_path, job_id, "version_history.jsonl", old_data)

    if old_data["job_name"] != data["job_name"]:
        registry = load_registry(base_path)
        registry[data["job_name"]] = registry.pop(old_data["job_name"])
        with open(os.path.join(base_path, 'job_register.json'), 'w') as f:
            json.dump(registry, f)

    with open(os.path.join(base_path, job_id, filename), 'w') as f:
        json.dump(data, f)
    st.rerun()


def compare_metadata(old_data, new_data):
    for key, value in old_data.items():
        if value != new_data[key]:
            return True
    return False


def editable_list_in_tab(tab, key, value, unique_key=None):
    if unique_key is None:
        unique_key = key
    edited_value = []
    for i, item in enumerate(value):
        unique_key = f"{unique_key}_{i}"
        edited_value.append(editable_data_in_tab(tab, f"{key} {i}", item, unique_key=unique_key))
    return edited_value


def editable_dict_in_tab(tab, key, value, unique_key=None):
    if unique_key is None:
        unique_key = key
    edited_value = {}
    for sub_key, sub_value in value.items():
        unique_key = f"{unique_key}_{sub_key}"
        edited_value[sub_key] = editable_data_in_tab(tab, sub_key, sub_value, unique_key=unique_key)
    return edited_value


def editable_data_in_tab(tab, key, value, unique_key=None):
    if unique_key is None:
        unique_key = key
    if isinstance(value, list):
        return editable_list_in_tab(tab, key, value, unique_key)
    elif isinstance(value, dict):
        return editable_dict_in_tab(tab, key, value, unique_key)
    elif isinstance(value, bool):
        return tab.checkbox(key, value, key=unique_key)
    elif isinstance(value, str):
        return tab.text_input(key, value, key=unique_key)
    elif isinstance(value, int):
        return tab.number_input(key, value, key=unique_key)
    else:
        return tab.text_input(key, str(value), key=unique_key)


def editable_io_model(tab, model, prefix):
    edited_model = {"lines": []}
    lines = model["lines"]
    edited_lines = tab.data_editor(lines, key=f"{prefix}_lines")
    edited_model["lines"] = edited_lines
    return edited_model


def load_job(base_path, selected_job_id):
    # Load metadata
    metadata = load_json(base_path, selected_job_id, "metadata.json")
    event_logs = load_jsonl(base_path, selected_job_id, "event_log.jsonl")
    generation_logs = load_jsonl(base_path, selected_job_id, "generation_log.jsonl")
    return metadata, event_logs, generation_logs
