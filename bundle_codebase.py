import os

base_dir = r"C:\Users\Nandini\.gemini\antigravity\scratch\kep_printgrid"
output_file = os.path.join(base_dir, "KEP_PRINTGRID_ALL_CODE.md")

include_extensions = {".py", ".html", ".css", ".js", ".txt", ".example", ".md", ".json"}
exclude_dirs = {".git", "__pycache__", "media", "staticfiles", ".system_generated"}
exclude_files = {"KEP_PRINTGRID_ALL_CODE.md", "db.sqlite3", "connector_private_key.pem"}

all_files = []
for root, dirs, files in os.walk(base_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    for file in files:
        if file in exclude_files:
            continue
        ext = os.path.splitext(file)[1].lower()
        if ext in include_extensions:
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            all_files.append((rel_path, full_path, ext))

all_files.sort(key=lambda x: x[0])

with open(output_file, "w", encoding="utf-8") as out:
    out.write("# KEP PrintGrid - Complete Project Codebase Bundle\n\n")
    out.write("This single file contains the entire source code for all backend models, views, templates, APIs, Windows local connector, encryption algorithms, automated tests, and configuration files of **KEP PrintGrid**.\n\n")
    out.write("## Table of Files Included\n\n")
    for rel_path, _, _ in all_files:
        norm_path = rel_path.replace("\\", "/")
        out.write(f"- `{norm_path}`\n")
    out.write("\n---\n\n")

    for rel_path, full_path, ext in all_files:
        norm_path = rel_path.replace("\\", "/")
        lang = "python"
        if ext in [".html"]:
            lang = "html"
        elif ext in [".css"]:
            lang = "css"
        elif ext in [".js"]:
            lang = "javascript"
        elif ext in [".json"]:
            lang = "json"
        elif ext in [".md"]:
            lang = "markdown"
        elif ext in [".txt", ".example"]:
            lang = "text"

        out.write(f"## File: `{norm_path}`\n\n")
        out.write(f"```{lang}\n")
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            out.write(content)
        except Exception as e:
            out.write(f"# Could not read file: {e}\n")
        out.write("\n```\n\n---\n\n")

print(f"Successfully compiled {len(all_files)} files into {output_file} (Size: {os.path.getsize(output_file)} bytes)")
