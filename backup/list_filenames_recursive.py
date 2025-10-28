from pathlib import Path
from difflib import SequenceMatcher
import re

def list_filenames_recursive(root: str) -> set[str]:
    root_path = Path(root)
    return {p.name for p in root_path.rglob('*') if p.is_file()}

def normalize_filename(name: str) -> str:
    stem = Path(name).stem
    suffix = Path(name).suffix
    # 移除“_products”（不区分大小写），并清理多余下划线
    stem = re.sub(r"_products", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"__+", "_", stem).strip("_")
    return f"{stem}{suffix}"

def find_similar_filenames(names1: set[str], names2: set[str], threshold: float = 0.5) -> list[tuple[str, str, float]]:
    similar_pairs: list[tuple[str, str, float]] = []
    for name1 in names1:
        for name2 in names2:
            norm1 = normalize_filename(name1)
            norm2 = normalize_filename(name2)
            score = SequenceMatcher(None, norm1, norm2).ratio()
            if score >= threshold:
                similar_pairs.append((name1, name2, score))
    # 按相似度从高到低排序
    similar_pairs.sort(key=lambda x: x[2], reverse=True)
    return similar_pairs

def main():
    dir1 = r"C:\Users\wyz\Desktop\dev-2025\knowledge_scripts\data\202508_02\extracted_products_batch"
    dir2 = r"C:\Users\wyz\Desktop\dev-2025\mall_rag_admin\data\正弘城_新品\extracted_products_batch"

    names1 = list_filenames_recursive(dir1)
    names2 = list_filenames_recursive(dir2)

    threshold = 0.9
    similar_pairs = find_similar_filenames(names1, names2, threshold=threshold)

    print(f"相似度≥{int(threshold*100)}%的文件名配对数量：{len(similar_pairs)}")
    for name1, name2, score in similar_pairs:
        print(f"{score:.2f}\t{name1}\t<->\t{name2}")

    # 统计未匹配到的文件名（两侧分别统计）
    matched_left = {a for a, _, _ in similar_pairs}
    matched_right = {b for _, b, _ in similar_pairs}
    unmatched_left = sorted(n for n in names1 if n not in matched_left)
    unmatched_right = sorted(n for n in names2 if n not in matched_right)

    print(f"\n未匹配到（左侧目录）数量：{len(unmatched_left)}")
    for n in unmatched_left:
        print(n)

    print(f"\n未匹配到（右侧目录）数量：{len(unmatched_right)}")
    for n in unmatched_right:
        print(n)

if __name__ == "__main__":
    main()