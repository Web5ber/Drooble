import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class AutoCommitHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_commit_time = 0
        self.commit_delay = 5  # Wait 5 seconds after last change before committing
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Skip venv and .git directories
        if 'venv' in event.src_path or '.git' in event.src_path:
            return
        
        # Skip temporary files
        if event.src_path.endswith('.pyc') or event.src_path.endswith('.tmp'):
            return
        
        print(f"File modified: {event.src_path}")
        self.schedule_commit()
    
    def schedule_commit(self):
        current_time = time.time()
        self.last_commit_time = current_time
    
    def try_commit(self):
        if time.time() - self.last_commit_time >= self.commit_delay:
            self.commit_changes()
            self.last_commit_time = 0
    
    def commit_changes(self):
        try:
            # Check if there are changes to commit
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if result.stdout.strip():
                print("Auto-committing changes...")
                
                # Add all changes
                subprocess.run(['git', 'add', '.'], check=True)
                
                # Commit with a timestamp message
                commit_message = f"Auto-commit: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(['git', 'commit', '-m', commit_message], check=True)
                
                # Push to remote
                subprocess.run(['git', 'push'], check=True)
                
                print("Auto-commit completed successfully!")
            else:
                print("No changes to commit")
        except subprocess.CalledProcessError as e:
            print(f"Error during auto-commit: {e}")

def main():
    event_handler = AutoCommitHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()
    
    print("Auto-commit watcher started. Press Ctrl+C to stop.")
    
    try:
        while True:
            event_handler.try_commit()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()
