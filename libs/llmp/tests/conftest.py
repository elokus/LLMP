def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    import os
    # delete all files and directories in data/jobs

    target_dir = "data/jobs"
    for file in os.listdir(target_dir):
        file_path = os.path.join(target_dir, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                # remove all files in the directory
                for sub_file in os.listdir(file_path):
                    sub_file_path = os.path.join(file_path, sub_file)
                    os.unlink(sub_file_path)
                os.rmdir(file_path)
        except Exception as e:
            print(e)

