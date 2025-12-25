Here is the **Legacy Code Archaeologist** project structured as a complete, professional architectural blueprint. This is organized by development phases, moving from the core infrastructure to the AI intelligence layer, and finally to production deployment.

---

# 🏛️ The Legacy Code Archaeologist: Architectural Blueprint

**Objective:** Build a CLI tool that visualizes technical debt by parsing spaghetti code, analyzing it with AI, and generating an interactive HTML knowledge graph.

## 1. High-Level Architecture & Stack

*   **Language:** Python 3.11+
*   **Parser:** **Tree-sitter** (Polyglot parsing, robust against syntax errors).
*   **AI Engine:** **LangChain** + **OpenAI (GPT-4o)** for semantic analysis and risk scoring.
*   **Visualization:** **Mermaid.js** (Text-to-Diagram) embedded in HTML.
*   **CLI:** **Typer** (User interface).
*   **Database:** **SQLite** (Local caching to save API costs).

---

## 2. Project Setup

### Folder Structure
Follow this **Service-Repository** pattern to separate parsing logic from AI logic.

```text
legacy_archaeologist/
│
├── core/
│   ├── __init__.py
│   ├── file_walker.py        # Recursive file finder (ignores node_modules)
│   ├── parser_engine.py      # Tree-sitter wrapper (CST extraction)
│   ├── graph_builder.py      # Converts data to Mermaid syntax
│   └── cache_manager.py      # SQLite caching system
│
├── ai/
│   ├── __init__.py
│   ├── summarizer.py         # LangChain logic (Code -> JSON Analysis)
│   └── prompts.py            # System prompts
│
├── templates/
│   └── report_template.html  # HTML skeleton
│
├── main.py                   # CLI Entry point
├── requirements.txt          # Dependencies
├── Dockerfile                # Container config
├── docker-compose.yml        # Orchestration
└── .env                      # API Keys
```

### Dependencies (`requirements.txt`)
```text
python-dotenv==1.0.0
typer[all]==0.9.0
rich==13.7.0
tree-sitter==0.20.4
tree-sitter-languages==1.10.0
langchain==0.1.0
langchain-openai==0.0.5
networkx==3.2.1
```

---

## 3. Phase 1: The Core Infrastructure

### A. The File Walker (`core/file_walker.py`)
Finds relevant source files while aggressively pruning "junk" folders like `.git` or `node_modules`.

```python
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
```

### B. The Parser Engine (`core/parser_engine.py`)
Uses Tree-sitter to extract classes, functions, and imports without executing the code.

```python
import os
from tree_sitter_languages import get_language, get_parser

class CodeParser:
    def __init__(self, language_name="python"):
        self.language_name = language_name
        self.language = get_language(language_name)
        self.parser = get_parser(language_name)
        
        # S-Expressions for extraction
        self.QUERIES = {
            "python": """
            (class_definition name: (identifier) @class_name)
            (function_definition name: (identifier) @function_name)
            (import_from_statement module_name: (dotted_name) @import_src)
            (import_statement name: (dotted_name) @import_lib)
            """
        }

    def parse_file(self, file_path):
        if not os.path.exists(file_path): return {}
        
        with open(file_path, "rb") as f:
            code_bytes = f.read()

        tree = self.parser.parse(code_bytes)
        query = self.language.query(self.QUERIES.get(self.language_name))
        captures = query.captures(tree.root_node)

        results = {"classes": [], "functions": [], "imports": []}
        
        for node, tag in captures:
            text = code_bytes[node.start_byte : node.end_byte].decode("utf8")
            if tag == "class_name": results["classes"].append(text)
            elif tag == "function_name": results["functions"].append(text)
            elif tag in ["import_src", "import_lib"]: results["imports"].append(text)
            
        return results
```

---

## 4. Phase 2: The Intelligence Layer (AI)

### The Summarizer (`ai/summarizer.py`)
Uses LangChain to force Structured JSON output regarding the code's risk and purpose.

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

class CodeSummarizer:
    def __init__(self, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.0)
        
        # Define expected JSON structure
        schemas = [
            ResponseSchema(name="summary", description="1-sentence explanation of responsibility."),
            ResponseSchema(name="tags", description="List of 1-3 keywords (e.g., 'Auth', 'DB')."),
            ResponseSchema(name="complexity_score", description="Int 1-10. 10 is technical debt.")
        ]
        self.output_parser = StructuredOutputParser.from_response_schemas(schemas)
        self.format_instructions = self.output_parser.get_format_instructions()

    def analyze_file(self, filename, code_content, metadata):
        # Truncate strictly for cost control
        truncated_code = code_content[:6000] 
        
        template = """
        Analyze source file: "{filename}"
        Metadata: {metadata}
        --- CODE ---
        {code}
        --- END ---
        Provide summary, tags, and risk score (1-10).
        {format_instructions}
        """
        
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm | self.output_parser
        
        try:
            return chain.invoke({
                "filename": filename,
                "metadata": str(metadata),
                "code": truncated_code,
                "format_instructions": self.format_instructions
            })
        except Exception:
            return {"summary": "Analysis Failed", "complexity_score": 0, "tags": []}
```

---

## 5. Phase 3: Optimization & Caching

### The Cache Manager (`core/cache_manager.py`)
Prevents re-analyzing files that haven't changed using MD5 hashing.

```python
import sqlite3
import hashlib

class CacheManager:
    def __init__(self, db_path="archeology_cache.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS file_cache 
            (file_hash TEXT PRIMARY KEY, ai_summary TEXT, complexity_score INTEGER, tags TEXT)
        """)

    def get(self, content):
        h = hashlib.md5(content.encode()).hexdigest()
        row = self.conn.execute("SELECT ai_summary, complexity_score, tags FROM file_cache WHERE file_hash=?", (h,)).fetchone()
        if row:
            return {"summary": row[0], "complexity_score": row[1], "tags": row[2].split(",")}
        return None

    def save(self, content, data):
        h = hashlib.md5(content.encode()).hexdigest()
        self.conn.execute("INSERT OR REPLACE INTO file_cache VALUES (?,?,?,?)", 
            (h, data['summary'], data['complexity_score'], ",".join(data['tags'])))
        self.conn.commit()
```

---

## 6. Phase 4: Visualization

### The Graph Builder (`core/graph_builder.py`)
Generates Mermaid syntax with dynamic color coding based on risk scores.

```python
class MermaidGenerator:
    def __init__(self, nodes):
        self.nodes = nodes

    def sanitize(self, name):
        return name.replace(".", "_").replace("/", "_").replace("-", "_")

    def generate_graph(self):
        lines = ["graph TD"]
        # Styles
        lines.append("classDef danger fill:#ffcccc,stroke:#ff0000,stroke-width:2px;")
        lines.append("classDef warning fill:#fff4cc,stroke:#ffaa00,stroke-width:2px;")
        lines.append("classDef safe fill:#ccffcc,stroke:#00aa00,stroke-width:1px;")

        for node in self.nodes:
            nid = self.sanitize(node['short_name'])
            risk = node.get('complexity_score', 0)
            style = "danger" if risk >= 8 else "warning" if risk >= 5 else "safe"
            
            lines.append(f'    {nid}("{node["short_name"]}<br/>Risk: {risk}"):::{style}')
            
            for imp in node.get('imports', []):
                # Simple heuristic linkage
                for target in self.nodes:
                    if imp == target['short_name'].replace(".py", ""):
                        lines.append(f"    {nid} --> {self.sanitize(target['short_name'])}")
                        
        return "\n".join(lines)
```

---

## 7. Phase 5: The Controller (`main.py`)

Integrates all modules into a CLI command.

```python
import os, typer, json
from rich.console import Console
from rich.progress import track
from dotenv import load_dotenv

from core.file_walker import FileWalker
from core.parser_engine import CodeParser
from core.graph_builder import MermaidGenerator
from core.cache_manager import CacheManager
from ai.summarizer import CodeSummarizer

load_dotenv()
app = typer.Typer()
console = Console()

@app.command()
def audit(path: str, output: str = "report.html"):
    walker = FileWalker(path)
    parser = CodeParser("python")
    cache = CacheManager()
    
    ai_active = bool(os.getenv("OPENAI_API_KEY"))
    summarizer = CodeSummarizer() if ai_active else None
    
    analyzed_nodes = []
    
    for file_path in track(list(walker.walk()), description="Auditing..."):
        # 1. Parse Structure
        data = parser.parse_file(file_path)
        data['short_name'] = os.path.basename(file_path)
        
        # 2. Read Content
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # 3. Check Cache -> AI Analysis
        if ai_active:
            cached_data = cache.get(content)
            if cached_data:
                data.update(cached_data)
            else:
                ai_data = summarizer.analyze_file(data['short_name'], content, data)
                cache.save(content, ai_data)
                data.update(ai_data)
        
        analyzed_nodes.append(data)

    # 4. Generate Output
    mermaid_code = MermaidGenerator(analyzed_nodes).generate_graph()
    
    with open("templates/report_template.html", "r") as f:
        html = f.read().replace("", mermaid_code)
        
    with open(output, "w") as f:
        f.write(html)
        
    console.print(f"[bold green]Done![/bold green] Report saved to {output}")

if __name__ == "__main__":
    app()
```

---

## 8. Deployment (Docker)

**Dockerfile**
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["python", "main.py"]
```

**docker-compose.yml**
```yaml
version: '3.8'
services:
  archeologist:
    build: .
    env_file: .env
    volumes:
      - ./reports:/app/reports
      - /path/to/target/project:/codebase
    command: audit /codebase --output reports/final.html
```

---

## 9. Usage Guide

1.  **Install:** `pip install -r requirements.txt`
2.  **Configure:** Add `OPENAI_API_KEY` to `.env`.
3.  **Run:**
    ```bash
    python main.py audit ./my_legacy_project
    ```
4.  **View:** Open `report.html` to see the color-coded architectural map.
