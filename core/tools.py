import os
from github import Github, UnknownObjectException, ContentFile
from langchain.tools import tool
from urllib.parse import urlparse

github_token = os.getenv("GITHUB_ACCESS_TOKEN")
g = Github(github_token)

def _get_repo_from_url(repo_url: str):
    """Fungsi helper untuk mendapatkan objek repo dari URL GitHub apa pun."""
    try:
        parsed_path = urlparse(repo_url).path.strip('/')
        path_parts = parsed_path.split('/')
        repo_path = f"{path_parts[0]}/{path_parts[1]}"
        
        return g.get_repo(repo_path)
    except UnknownObjectException:
        raise ValueError(f"Repositori '{repo_path}' tidak ditemukan atau bersifat privat.")
    except IndexError:
        raise ValueError(f"URL repositori tidak valid: {repo_url}")

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
    """Gunakan untuk memahami bagaimana file dan folder diorganisir dalam direktori utama (root) repositori."""
    try:
        repo = _get_repo_from_url(repo_url)
        contents = repo.get_contents("/")
        
        structure = f"Struktur untuk '{repo.full_name}' di path '/':\n"
        dirs = [c.path for c in contents if c.type == 'dir']
        files = [c.path for c in contents if c.type == 'file']

        for d in dirs:
            structure += f"📁 {d}/\n"
        for f in files:
            structure += f"📄 {f}\n"
            
        return structure.strip()
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error saat mengambil struktur repositori: Pastikan URL benar dan repositori dapat diakses. Detail: {e}"

@tool
def analyze_dependencies(repo_url: str) -> str:
    """Digunakan secara spesifik untuk membaca file dependensi seperti requirements.txt atau package.json."""
    try:
        repo = _get_repo_from_url(repo_url)
        dependency_files = ["requirements.txt", "package.json"]
        
        found_dependencies = []
        for filename in dependency_files:
            try:
                file_content = repo.get_contents(filename)
                content = file_content.decoded_content.decode('utf-8')
                found_dependencies.append(f"Konten dari '{filename}':\n---\n{content}\n---")
            except UnknownObjectException:
                continue
        
        if not found_dependencies:
            return "Informasi: Tidak ditemukan file dependensi umum (requirements.txt, package.json)."
            
        return "\n".join(found_dependencies)
    except ValueError as e:
        return f"Error: {e}"
    except Exception as e:
        return f"Error saat menganalisis dependensi: {e}"
    