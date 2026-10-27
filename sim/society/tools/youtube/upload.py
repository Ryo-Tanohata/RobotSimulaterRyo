"""川辺の五人の動画を YouTube に上げる (YouTube Data API。2026-10-28 本人の希望。上げる作業は Claude、もとの画質のまま)

  py -3 sim/society/tools/youtube/upload.py --auth          はじめの許可 (ブラウザに Google の許可の画面が出る。本人が「許可」を押す)
  py -3 sim/society/tools/youtube/upload.py G1F2 G1F3       動画を上げる (名前は app/society_<名前>.mp4。題と説明文は videos.py の一覧)
  py -3 sim/society/tools/youtube/upload.py --list          上げたもの・まだのもの

- 鍵と許可のしるしは、リポジトリの外の C:/Users/<あなた>/.youtube_kawabe/ (client_secret.json・token.json) にだけ置く。GitHub に入れない
- 上げた動画は非公開・子ども向けではない。再生リスト「川辺の五人 (話の順)」の、話の順の位置に入れる
- 上げた記録: sim/society/video/youtube_uploaded.json (番号・YouTube の id)。docs/youtube_upload.md の URL の欄も書く
- 無料の枠は 1 日に 6 本ほど (1 本 1600)。こえると、その日は上がらない (料金はかからない)
- 同意画面が「お試し」なので、許可は 7 日で切れる。切れたら --auth をもう一度
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import videos  # noqa: E402  題と説明文の一覧 (V・title・desc)

REPO = Path(__file__).resolve().parents[4]
APP = REPO / "sim/society/app"
LOG = REPO / "sim/society/video/youtube_uploaded.json"
DOC = REPO / "docs/youtube_upload.md"
KEY = Path.home() / ".youtube_kawabe"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
PLAYLIST = "川辺の五人 (話の順)"


def creds(force=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    tok = KEY / "token.json"
    c = None if force or not tok.exists() else Credentials.from_authorized_user_file(str(tok), SCOPES)
    if c and c.expired and c.refresh_token:
        try:
            c.refresh(Request())
        except Exception:  # 7 日で切れた (お試しの同意画面)
            c = None
    if not c or not c.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(KEY / "client_secret.json"), SCOPES)
        c = flow.run_local_server(port=0, prompt="consent", authorization_prompt_message="ブラウザで許可してください: {url}",
                                  success_message="許可できました。このタブは閉じてかまいません。")
    tok.write_text(c.to_json(), encoding="utf-8")
    return c


def yt():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=creds(), cache_discovery=False)


def load_log():
    return json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}


def save_log(log):
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    rows = DOC.read_text(encoding="utf-8").splitlines() if DOC.exists() else []
    byn = {v["n"]: v for v in log.values()}
    out = []
    for r in rows:  # | 番号 | 題 | 動画 | URL |
        p = r.split("|")
        if len(p) == 6 and p[1].strip().isdigit() and int(p[1]) in byn:
            v = byn[int(p[1])]
            p[4] = f" https://youtu.be/{v['video_id']}{' (試しの縮めた写し)' if v.get('lite') else ''} "
            r = "|".join(p)
        out.append(r)
    if out:
        DOC.write_text("\n".join(out) + "\n", encoding="utf-8")


def playlist_id(api):
    req = api.playlists().list(part="snippet", mine=True, maxResults=50)
    while req:
        res = req.execute()
        for p in res.get("items", []):
            if p["snippet"]["title"] == PLAYLIST:
                return p["id"]
        req = api.playlists().list_next(req, res)
    res = api.playlists().insert(part="snippet,status", body={"snippet": {"title": PLAYLIST, "defaultLanguage": "ja"},
                                                               "status": {"privacyStatus": "private"}}).execute()
    return res["id"]


def place(api, pid, video_id, n, log):
    """再生リストの、話の順の位置に入れる (番号の小さい動画の数 = 位置)"""
    num = {v["video_id"]: v["n"] for v in log.values()}
    items, req = [], api.playlistItems().list(part="snippet", playlistId=pid, maxResults=50)
    while req:
        res = req.execute()
        items += res.get("items", [])
        req = api.playlistItems().list_next(req, res)
    if any(i["snippet"]["resourceId"]["videoId"] == video_id for i in items):
        return
    pos = sum(1 for i in items if num.get(i["snippet"]["resourceId"]["videoId"], 999) < n)
    api.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": pid, "position": pos,
                                                                 "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()


def upload(api, name, log):
    from googleapiclient.http import MediaFileUpload
    idx = {vid: (i, t, what, part) for i, (vid, t, what, part) in enumerate(videos.V, 1)}
    if name not in idx:
        sys.exit(f"一覧にない名前: {name} (videos.py の V を見る)")
    n, t, what, part = idx[name]
    if name in log and not log[name].get("lite"):
        print(f"{n:02d} {name}: もう上げてある https://youtu.be/{log[name]['video_id']}")
        return
    f = APP / f"society_{name}.mp4"
    if not f.exists():
        sys.exit(f"動画がない: {f}")
    body = {"snippet": {"title": videos.title(n, t), "description": videos.desc(n, name, what, part), "categoryId": "28",
                        "defaultLanguage": "ja", "defaultAudioLanguage": "ja"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}
    req = api.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(f), chunksize=8 * 1024 * 1024, resumable=True))
    res = None
    while res is None:
        st, res = req.next_chunk()
        if st:
            print(f"  {name}: {int(st.progress() * 100)}%", flush=True)
    log[name] = {"n": n, "video_id": res["id"], "title": body["snippet"]["title"], "file_bytes": f.stat().st_size}
    save_log(log)
    place(api, playlist_id(api), res["id"], n, log)
    print(f"{n:02d} {name}: 上げた https://youtu.be/{res['id']} (非公開・再生リストに入れた)")


def main(argv):
    if "--auth" in argv:
        creds(force=True)
        print("許可のしるしを保存した:", KEY / "token.json")
        return
    log = load_log()
    if "--list" in argv or not argv:
        for i, (vid, t, *_x) in enumerate(videos.V, 1):
            v = log.get(vid)
            print(f"{i:02d} {vid:6s} {'https://youtu.be/' + v['video_id'] + (' (縮めた写し)' if v.get('lite') else '') if v else 'まだ'}")
        return
    api = yt()
    for name in argv:
        upload(api, name, log)


if __name__ == "__main__":
    main(sys.argv[1:])
