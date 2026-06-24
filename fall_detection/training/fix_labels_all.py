import os

label_dir = "fall_dataset/labels_all"  # 原始标签所在目录

def fix_all_labels():
    count = 0
    for fname in os.listdir(label_dir):
        if fname.endswith(".txt"):
            fpath = os.path.join(label_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == '1':  # 将类别1 → 0
                    parts[0] = '0'
                    count += 1
                new_lines.append(" ".join(parts) + "\n")

            with open(fpath, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

    print(f"✅ 标签修复完成，共修正 {count} 行")

if __name__ == "__main__":
    fix_all_labels()
