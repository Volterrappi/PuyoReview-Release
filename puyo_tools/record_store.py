"""Standalone local review records, grouped in user-created folders."""
import json
import csv
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path.home() / "PuyoReview" / "records"
INDEX = ROOT / "index.json"

def _atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def _safe_name(name):
    value = str(name).strip(" .")
    if not value or value in (".", ".."):
        raise ValueError("フォルダ名を入力してください")
    if any(ord(ch) < 32 or ch in '/\\:*?"<>|' for ch in value):
        raise ValueError("フォルダ名に使えない文字があります")
    return value[:70]

def _inside(path):
    path = Path(path).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("記録フォルダ外です")
    return path

def ensure():
    ROOT.mkdir(parents=True, exist_ok=True)
    if not INDEX.exists():
        _atomic(INDEX, {"version": 1, "folders": ["未分類"], "records": []})
    (ROOT / "未分類").mkdir(exist_ok=True)

def read_index():
    ensure()
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("記録一覧の形式が不正です")
    return data

def folders():
    return list(read_index().get("folders", ["未分類"]))

def add_folder(name):
    name = _safe_name(name)
    data = read_index()
    if name in data["folders"]:
        raise ValueError("同じ名前のフォルダがあります")
    (ROOT / name).mkdir(exist_ok=False)
    data["folders"].append(name)
    _atomic(INDEX, data)
    return name

def list_records(folder=None):
    records = read_index()["records"]
    return [r for r in records if folder is None or r.get("folder") == folder]

def save(folder, name, analysis_type, memo, board, next_pairs, result, screenshot=None, csv_rows=None):
    data = read_index()
    if folder not in data["folders"]:
        raise ValueError("保存先フォルダがありません")
    if len(board) != 13 or any(len(line) != 6 or not set(line) <= set(".RBGYPO") for line in board):
        raise ValueError("盤面が不正です")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    uid = uuid.uuid4().hex
    order = 1 + max((int(r.get("number", 0)) for r in data["records"] if r.get("folder") == folder), default=0)
    target = _inside(ROOT / folder / uid)
    target.mkdir(parents=True)
    item = dict(id=uid, number=order, folder=folder, name=name.strip() or now,
                analysis_type=analysis_type, memo=memo, saved_at=now, source_type="manual",
                board=list(board), next_pairs=list(next_pairs), analysis_result=result,
                screenshot=None, csv_file=None, version=2)
    try:
        if screenshot is not None:
            picture = target / "screenshot.png"
            screenshot.convert("RGB").save(picture, format="PNG")
            item["screenshot"] = picture.name
        if csv_rows is not None:
            rows = iter(csv_rows)
            first = next(rows, None)
            with (target / "candidates.csv").open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(first) if first is not None else ['探索番号'])
                writer.writeheader()
                if first is not None:
                    writer.writerow(first)
                    writer.writerows(rows)
            item["csv_file"] = "candidates.csv"
        _atomic(target / "record.json", item)
        data["records"].append({k:item[k] for k in ("id","number","folder","name","analysis_type","memo","saved_at")})
        _atomic(INDEX, data)
    except Exception:
        shutil.rmtree(target, ignore_errors=True)
        raise
    return item

def load(record_id):
    data = read_index()
    found = next((r for r in data["records"] if r["id"] == record_id), None)
    if found is None:
        raise ValueError("記録が見つかりません")
    path = _inside(ROOT / found["folder"] / record_id / "record.json")
    return json.loads(path.read_text(encoding="utf-8"))


def record_directory(record_id):
    found = next((r for r in read_index()["records"] if r["id"] == record_id), None)
    if found is None:
        raise ValueError("記録が見つかりません")
    return _inside(ROOT / found["folder"] / record_id)


def attachment(record_id, key):
    """Resolve relative attachments, including moved legacy absolute image paths."""
    item = load(record_id)
    value = item.get(key)
    if not value:
        return None
    directory = record_directory(record_id)
    # Attachments belong to the record. Do not open a legacy external path.
    name = str(value).replace("\\", "/").rsplit("/", 1)[-1]
    if name in ("", ".", ".."):
        return None
    path = _inside(directory / name)
    return path if path.is_file() else None

def move(record_id, destination):
    data = read_index()
    if destination not in data["folders"]:
        raise ValueError("移動先フォルダがありません")
    found = next((r for r in data["records"] if r["id"] == record_id), None)
    if found is None:
        raise ValueError("記録が見つかりません")
    if found["folder"] == destination:
        return
    origin = _inside(ROOT / found["folder"] / record_id)
    target = _inside(ROOT / destination / record_id)
    if target.exists():
        raise ValueError("移動先に同じIDがあります")
    item = load(record_id)
    old_folder, old_number = item["folder"], item["number"]
    number = 1 + max((int(r.get("number",0)) for r in data["records"] if r.get("folder") == destination), default=0)
    shutil.move(str(origin), str(target))
    try:
        item["folder"], item["number"] = destination, number
        _atomic(target / "record.json", item)
        found["folder"], found["number"] = destination, number
        _atomic(INDEX, data)
    except Exception:
        shutil.move(str(target), str(origin))
        item["folder"], item["number"] = old_folder, old_number
        _atomic(origin / "record.json", item)
        raise

def update(record_id, name, memo):
    data = read_index()
    row = next((r for r in data["records"] if r["id"] == record_id), None)
    if row is None: raise ValueError("記録が見つかりません")
    item = load(record_id)
    item["name"] = name.strip() or item["name"]
    item["memo"] = memo
    path = _inside(ROOT / row["folder"] / record_id / "record.json")
    _atomic(path,item)
    row["name"],row["memo"] = item["name"],item["memo"]
    _atomic(INDEX,data)
