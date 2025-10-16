from pathlib import Path
from difflib import SequenceMatcher

def list_filenames_recursive(root: str) -> set[str]:
    root_path = Path(root)
    return {p.name for p in root_path.rglob('*') if p.is_file()}

def find_similar_filenames(names1: set[str], names2: set[str], threshold: float = 0.5) -> list[tuple[str, str, float]]:
    similar_pairs: list[tuple[str, str, float]] = []
    for name1 in names1:
        for name2 in names2:
            score = SequenceMatcher(None, name1, name2).ratio()
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

    similar_pairs = find_similar_filenames(names1, names2, threshold=0.5)

    print(f"相似度≥50%的文件名配对数量：{len(similar_pairs)}")
    for name1, name2, score in similar_pairs:
        print(f"{score:.2f}\t{name1}\t<->\t{name2}")

if __name__ == "__main__":
    main()