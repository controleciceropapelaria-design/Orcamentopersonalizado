import requests
import base64

def save_csv_to_github(df, repo, path, token, branch="main", commit_message="Update CSV via Streamlit"):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}"}
    # Pega o SHA do arquivo atual (necessário para update)
    get_resp = requests.get(url, headers=headers, params={"ref": branch})
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    # Converte o DataFrame para CSV e codifica em base64
    csv_content = df.to_csv(index=False).encode()
    b64_content = base64.b64encode(csv_content).decode()

    data = {
        "message": commit_message,
        "content": b64_content,
        "branch": branch,
    }
    if sha:
        data["sha"] = sha

    resp = requests.put(url, headers=headers, json=data)
    return resp.status_code, resp.json()
