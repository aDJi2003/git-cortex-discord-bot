# core/tools.py
import os
from urllib.parse import urlparse
import requests
from typing import List, Optional
from pydantic import BaseModel, Field

from langchain_core.tools import BaseTool

from inspect import signature

orig_call = BaseTool.__call__

def patched_call(self, *args, **kwargs):
    """
    Perbaikan untuk error:
    - BaseTool.call() got an unexpected keyword argument 'title'
    - BaseTool.invoke() missing 1 required positional argument: 'input'
    """
    # Hapus argumen yang tidak dikenal oleh tool (contoh: title)
    safe_kwargs = {k: v for k, v in kwargs.items() if k in signature(self.invoke).parameters}

    # Jika tool mengharapkan 1 argumen utama bernama 'input', ubah args accordingly
    if "input" in signature(self.invoke).parameters and not args and "input" not in safe_kwargs:
        # Jika tool menerima input tunggal (misal: string atau dict)
        if len(kwargs) == 1:
            first_value = next(iter(kwargs.values()))
            return self.invoke({"input": first_value})
        else:
            return self.invoke({"input": kwargs})
    return self.invoke(*args, **safe_kwargs)

BaseTool.__call__ = patched_call

# LangChain tool decorator (modern)
try:
    from langchain.tools import tool
except Exception:
    # fallback jika versi langchain berbeda
    def tool(*args, **kwargs):
        def decorator(fn):
            return fn
        return decorator

GITHUB_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")


# -------------------------
# Helper functions
# -------------------------
def _normalize_repo_url(repo_url: str) -> str:
    """Return repo path like 'owner/repo' from URL or input."""
    if repo_url.startswith("http"):
        path = urlparse(repo_url).path.strip("/")
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError(f"URL repositori tidak valid: {repo_url}")
        return f"{parts[0]}/{parts[1]}"
    # assume already in owner/repo form
    if "/" not in repo_url:
        raise ValueError(f"Format repositori harus 'owner/repo' atau URL lengkap: {repo_url}")
    return repo_url.strip("/")


def _github_api_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def _raw_base_url(repo_path: str, branch: str = "main") -> str:
    return f"https://raw.githubusercontent.com/{repo_path}/{branch}"


def _api_contents_url(repo_path: str, path: str = "") -> str:
    if path:
        return f"https://api.github.com/repos/{repo_path}/contents/{path}"
    return f"https://api.github.com/repos/{repo_path}/contents"


# -------------------------
# Tools (decorated)
# -------------------------

class RepoInput(BaseModel):
    repo_url: str = Field(..., description="URL repo (https://github.com/owner/repo) atau 'owner/repo'")
    branch: Optional[str] = Field("main", description="Nama branch (default: main)")

class RepoPathInput(RepoInput):
    path: str = Field("/", description="Path file atau direktori relatif di repo. Gunakan '/' untuk root.")


@tool("get_readme_content", return_direct=True)
def get_readme_content(repo_url: str, branch: str = "main") -> str:
    """
    Ambil README.md dari repo — bila branch tidak ada, coba default 'main' atau 'master'.
    Input: repo_url (URL atau owner/repo), optional branch.
    """
    try:
        repo_path = _normalize_repo_url(repo_url)
        # try main then master if 404
        for br in [branch, "main", "master"]:
            raw_url = f"{_raw_base_url(repo_path, br)}/README.md"
            r = requests.get(raw_url, headers=_github_api_headers(), timeout=15)
            if r.status_code == 200:
                return r.text
        return f"README.md tidak ditemukan di branch '{branch}', 'main', atau 'master' untuk repo {repo_path}."
    except Exception as e:
        return f"Error saat mengambil README: {e}"


@tool("get_repository_structure", return_direct=True)
def get_repository_structure(repo_url: str, branch: str = "main") -> str:
    """
    Ambil daftar isi direktori root (file & folder) menggunakan GitHub Contents API.
    Untuk struktur recursive, agent bisa memanggil list_files_in_directory pada subpath.
    """
    try:
        repo_path = _normalize_repo_url(repo_url)
        api_url = _api_contents_url(repo_path, "")
        r = requests.get(api_url, headers=_github_api_headers(), timeout=15)
        if r.status_code != 200:
            return f"Gagal mengambil struktur repo: HTTP {r.status_code} - {r.text}"
        items = r.json()
        dirs = [it["path"] for it in items if it["type"] == "dir"]
        files = [it["path"] for it in items if it["type"] == "file"]
        out = f"Struktur root untuk '{repo_path}':\n"
        for d in dirs:
            out += f"📁 {d}/\n"
        for f in files:
            out += f"📄 {f}\n"
        return out.strip() if (dirs or files) else f"Repositori '{repo_path}' kosong pada root."
    except Exception as e:
        return f"Error saat mengambil struktur repositori: {e}"


@tool("analyze_dependencies", return_direct=True)
def analyze_dependencies(repo_url: str, branch: str = "main") -> str:
    """
    Carilah file dependensi umum (requirements.txt, environment.yml, package.json, pyproject.toml).
    Kembalikan konten bila ditemukan.
    """
    try:
        repo_path = _normalize_repo_url(repo_url)
        candidates = [
            "requirements.txt",
            "pyproject.toml",
            "Pipfile",
            "environment.yml",
            "package.json",
            "setup.py",
        ]
        found = []
        for fname in candidates:
            raw_url = f"{_raw_base_url(repo_path, branch)}/{fname}"
            r = requests.get(raw_url, headers=_github_api_headers(), timeout=10)
            if r.status_code == 200:
                found.append(f"--- {fname} ---\n{r.text}\n")
        if not found:
            return "Tidak ditemukan file dependensi umum (requirements.txt, package.json, pyproject.toml, dll.)"
        return "\n".join(found)
    except Exception as e:
        return f"Error saat menganalisis dependensi: {e}"


@tool("list_files_in_directory", return_direct=True)
def list_files_in_directory(repo_url: str, path: str = "/", branch: str = "main") -> str:
    """
    List file & folder pada path tertentu (relatif).
    path contoh: '/', 'src', 'src/app', 'docs'
    """
    try:
        repo_path = _normalize_repo_url(repo_url)
        # strip leading slash if present
        path_rel = path.lstrip("/")
        api_url = _api_contents_url(repo_path, path_rel)
        r = requests.get(api_url, headers=_github_api_headers(), timeout=15)
        if r.status_code == 404:
            return f"Path '{path}' tidak ditemukan di repo {repo_path}."
        if r.status_code != 200:
            return f"Gagal mengambil isi direktori: HTTP {r.status_code} - {r.text}"
        items = r.json()
        dirs = [it["path"] for it in items if it["type"] == "dir"]
        files = [it["path"] for it in items if it["type"] == "file"]
        out = f"Struktur untuk '{repo_path}' di path '{path}':\n"
        for d in dirs:
            out += f"📁 {d}/\n"
        for f in files:
            out += f"📄 {f}\n"
        return out.strip() if (dirs or files) else f"Direktori '{path}' kosong atau tidak ada."
    except Exception as e:
        return f"Error saat mengambil isi direktori: {e}"


@tool("read_file_content", return_direct=True)
def read_file_content(repo_url: str, file_path: str, branch: str = "main") -> str:
    """
    Baca konten file spesifik via raw.githubusercontent.
    file_path contoh: 'src/app.py' atau 'Dockerfile'
    """
    try:
        repo_path = _normalize_repo_url(repo_url)
        raw_url = f"{_raw_base_url(repo_path, branch)}/{file_path.lstrip('/')}"
        r = requests.get(raw_url, headers=_github_api_headers(), timeout=15)
        if r.status_code == 404:
            return f"File '{file_path}' tidak ditemukan di repo {repo_path} (branch {branch})."
        if r.status_code != 200:
            return f"Gagal mengambil file: HTTP {r.status_code} - {r.text}"
        return r.text
    except Exception as e:
        return f"Error saat membaca file: {e}"


@tool("get_repo_languages", return_direct=True)
def get_repo_languages(repo_url: str) -> str:
    """
    Ambil bahasa pemrograman dan byte counts dari GitHub API.
    """
    try:
        repo_path = _normalize_repo_url(repo_url)
        api_url = f"https://api.github.com/repos/{repo_path}/languages"
        r = requests.get(api_url, headers=_github_api_headers(), timeout=10)
        if r.status_code != 200:
            return f"Gagal mengambil bahasa repo: HTTP {r.status_code} - {r.text}"
        langs = r.json()
        if not langs:
            return "Tidak dapat mendeteksi bahasa pemrograman di repositori ini."
        out = "Bahasa pemrograman yang digunakan:\n"
        for k, v in langs.items():
            out += f"- {k}: {v} bytes\n"
        return out
    except Exception as e:
        return f"Error saat mengambil bahasa repositori: {e}"


# -------------------------
# Export list of tools for agent
# -------------------------
ALL_GITHUB_TOOLS = [
    get_readme_content,
    get_repository_structure,
    analyze_dependencies,
    list_files_in_directory,
    read_file_content,
    get_repo_languages,
]
