from os import listdir, path, makedirs, remove

in_path = "result"
out_path = "wait_for_upload"
if not path.exists(out_path):
    makedirs(out_path)

# 遍历文件夹
path_one = listdir(in_path)
for nickname in path_one:
    # url -> line
    history_data = {}
    # 读取历史数据
    with open(
        f"result/{nickname}/history_data_{nickname}",
        "r",
        encoding="utf-8",
    ) as r:
        lines = r.readlines()
    # 历史数据去重
    for line in lines:
        try:
            tt, uu = line.split(" *** ")
            history_data[uu.strip()] = line.strip()
        except Exception as e:
            print("****** WARNING ******")
            print(f"wrong line file path: result/{nickname}/history_data_{nickname}")
            print(f"wrong line: line")
            print(repr(e))
            print("****** WARNING ******")

    # 遍历文件夹里的文件
    files = listdir(f"{in_path}/{nickname}")
    for file in files:
        # 检查带有new_data_标识的文件
        if file.find("new_data_") != -1:
            url_list = []
            with open(f"{in_path}/{nickname}/{file}", "r", encoding="utf-8") as r:
                lines = r.readlines()

            for line in lines:
                try:
                    title, url = line.split(" *** ")
                    title, url = title.strip(), url.strip()
                    # 检查标题和url
                    if title and url:
                        # 判断url是否爬过
                        if url not in history_data:
                            history_data[url] = f"{title} *** {url}"
                            # 检查新url是否有重复
                            if url not in url_list:
                                url_list.append(url.strip() + "\n")
                except:
                    print(f"行 {line} 解析失败，忽略")

            # with open(f"{out_path}/{file}/title_list_{file}", "w", encoding="utf-8") as w:
            #     w.writelines(title_list)
            # 输出url文件
            with open(f"{out_path}/{nickname}_{file}", "w", encoding="utf-8") as w:
                w.writelines(url_list)
            print(f"{out_path}/{nickname}_{file}")
            # 删除new_data_文件
            remove(f"{in_path}/{nickname}/{file}")

    # 输出新的历史数据文件
    duplicate_data = []
    for url in history_data:
        duplicate_data.append(history_data[url] + "\n")
    with open(
        f"result/{nickname}/history_data_{nickname}",
        "w",
        encoding="utf-8",
    ) as w:
        w.writelines(duplicate_data)

print("\n完成")
