from os import listdir, path, makedirs

in_path = "result"
out_path = "wait_for_upload"
if not path.exists(out_path):
    makedirs(out_path)
    exit(f"{out_path}目录不存在，已创建")
path_one = listdir(in_path)
for nickname in path_one:
    files = listdir(f"{in_path}/{nickname}")
    for file in files:
        if file.find("new_data_") != -1:
            title_list = []
            url_list = []
            if path.exists(f"{in_path}/{nickname}/{file}"):
                print(file)
                with open(f"{in_path}/{nickname}/{file}", "r", encoding="utf-8") as r:
                    lines = r.readlines()
                for line in lines:
                    try:
                        title, url = line.split(" *** ")
                        title_list.append(title + "\n")
                        url_list.append(url.strip() + "\n")
                    except:
                        print(f"行 {line} 解析失败，忽略")

                # with open(f"{out_path}/{file}/title_list_{file}", "w", encoding="utf-8") as w:
                #     w.writelines(title_list)

                with open(f"{out_path}/{nickname}_{file}", "w", encoding="utf-8") as w:
                    w.writelines(url_list)

print("\n完成")
