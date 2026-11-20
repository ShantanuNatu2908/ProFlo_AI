import random
from git import GitCommandError
import subprocess

def random_commit(message):
    cmd = ['git', 'commit', '-m', message]
    try:
        process = subprocess.run(cmd, check=True)
        return True, "Commit added successfully."
    except subprocess.CError as e:
        if str(e) == 'The exit code was non-zero':
            return False, f"Error while committing: {str(e)}"
        else:
            raise

def generate_random_commit():
    # Generate random commit message
    message = ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789=+-*/.:') for _ in range(50))

    status, message = random_commit(message)
    if status:
        print(f"Commit added successfully. Commit hash: {message}")
        repo_str = subprocess.check_output(['git', 'repository', '--user-dir', '.'])
        repo = GitRepository(repo_str.decode().strip())