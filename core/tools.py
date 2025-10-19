# core/tools.py
import os
from github import Github, UnknownObjectException, ContentFile
from langchain.tools import tool

# Inisialisasi koneksi ke GitHub API
github_token = os.getenv("GITHUB_ACCESS_TOKEN")
g = Github(github_token)

def _get_repo_from_url(repo_url: str):
    """Fungsi helper untuk mendapatkan objek repo dari URL."""
    repo_path = repo_url.replace("https://github.com/", "").strip('/')
    try:
        return g.get_repo(repo_path)
    except UnknownObjectException:
        raise ValueError(f"Repositori '{repo_path}' tidak ditemukan atau bersifat privat.")

@tool
def get_readme_content(repo_url: str) -> str:
    """
    Paling baik digunakan PERTAMA KALI untuk pertanyaan umum tentang sebuah repositori.
    Fungsi ini mengambil konten dari file README.md untuk memahami tujuan utama,
    cara setup, dan ringkasan umum dari sebuah proyek.
    """
    try:
        repo = _get_repo_from_url(repo_url)
        readme = repo.get_readme()
        return readme.decoded_content.decode('utf-8')
    except Exception as e:
        return f"Error saat mengambil README: {e}"

@tool
def get_repository_structure(repo_url: str) -> str:
    """
    Gunakan untuk memahami bagaimana file dan folder diorganisir dalam direktori utama (root) repositori.
    Sangat berguna jika pengguna bertanya 'tunjukkan struktur kodenya'.
    Input untuk tool ini HANYA URL repositori.
    """
    # --- PERUBAHAN UTAMA DI SINI ---
    # Kita menyederhanakan fungsi ini agar hanya menerima satu argumen: repo_url.
    # Path secara otomatis diatur ke direktori utama ('/').
    try:
        repo = _get_repo_from_url(repo_url)
        path = "/" # Path diatur secara internal, tidak lagi dari input agent.
        contents = repo.get_contents(path)
        structure = f"Struktur untuk '{repo_url}' di path '{path}':\n"
        
        dirs = [c.path for c in contents if c.type == 'dir']
        files = [c.path for c in contents if c.type == 'file']

        for d in dirs:
            structure += f"📁 {d}/\n"
        for f in files:
            structure += f"📄 {f}\n"
            
        return structure
    except Exception as e:
        return f"Error saat mengambil struktur repositori: {e}"

@tool
def analyze_dependencies(repo_url: str) -> str:
    """
    Digunakan secara spesifik untuk mengidentifikasi library, framework, atau teknologi
    yang digunakan dalam proyek dengan cara membaca file dependensi seperti
    requirements.txt atau package.json.
    """
    try:
        repo = _get_repo_from_url(repo_url)
        dependency_files = {
            "requirements.txt": "Python",
            "package.json": "JavaScript/Node.js"
        }
        
        found_dependencies = []
        for filename, tech in dependency_files.items():
            try:
                file_content = repo.get_contents(filename)
                if isinstance(file_content, ContentFile):
                    content = file_content.decoded_content.decode('utf-8')
                    found_dependencies.append(f"Ditemukan dependensi {tech} (dari {filename}):\n---\n{content}\n---")
            except UnknownObjectException:
                continue
        
        if not found_dependencies:
            return "Tidak ditemukan file dependensi umum (seperti requirements.txt atau package.json)."
            
        return "\n".join(found_dependencies)
    except Exception as e:
        return f"Error saat menganalisis dependensi: {e}"