from pathlib import Path

def list_filenames_recursive(root: str) -> set[str]:
    root_path = Path(root)
    return {p.name for p in root_path.rglob('*') if p.is_file()}

def main():
    dir1 = r"C:\Users\wyz\Desktop\dev-2025\knowledge_scripts\data\202508_02\extracted_products_batch"
    dir2 = r"C:\Users\wyz\Desktop\dev-2025\mall_rag_admin\data\正弘城_新品\extracted_products_batch"

    names1 = list_filenames_recursive(dir1)
    names2 = list_filenames_recursive(dir2)

    same_names = names1 & names2

    print(f"两个目录中同名文件数量：{len(same_names)}")
    # 如需查看具体同名文件名，取消下一行注释
    # for name in sorted(same_names): print(name)

if __name__ == "__main__":
    main()