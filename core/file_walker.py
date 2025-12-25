import os
from typing import List, Generator

class FileWalker:
    def __init__(self, root_dir: str, extensions: List[str] = None):
        self.root_dir = os.path.abspath(root_dir)
        self.extensions = [e.lower() for e in extensions] if extensions else ['.py']
        self.ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', 'dist', 'build'}

    def walk(self) -> Generator[str, None, None]:
        print(f"🔎 Scanning: {self.root_dir}...")
        for root, dirs, files in os.walk(self.root_dir, topdown=True):
            # In-place list modification to prune recursion
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.extensions):
                    yield os.path.join(root, file)
