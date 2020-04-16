from firecares.celery import app
import os
import shutil


@app.task(queue='cleanup')
def remove_file(path):
    """
    Removes a path from the file system.
    """

    if os.path.isdir(path):
        return shutil.rmtree(path=path, ignore_errors=True)

    return os.unlink(path)
