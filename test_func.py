import src.eagle_api as EG


if __name__ == "__main__":

    # print(len(EG.EAGLE_list_items(tags=['誘惑'])['data']))
    # print(EG.EAGLE_list_items(tags=['誘惑'])['data'])
    # print(EG.EAGLE_list_items(tags=['誘惑'])['data'][0])
    #### dictionary 或是list of dictionary


    

    # # 測試資料夾操作
    # print("列出所有資料夾：")
    # print(EG.EAGLE_get_folders())   ###OK
    # print(EG.EAGLE_get_folders()['data'])

    # print("列出最近使用的資料夾：")
    # print(EG.EAGLE_get_recent_folders())  ###OK
    # print(EG.EAGLE_get_recent_folders()['data'])  ###OK

    # print("創建新資料夾：")
    # print(EG.EAGLE_create_folder(folderName="測試資料夾A", tags=["Test", "Example"]))  ###OK, tags失效

    # M4MTN1IV8O4GD

    # print("重命名資料夾：")
    # print(EG.EAGLE_update_folder_name(folderId="M4MTN1IV8O4GD", newName="新名稱B"))  ###OK

    # print("更新資料夾屬性：")
    # print(EG.EAGLE_update_folder_details(folderId="M4MTN1IV8O4GD", newName="更新名稱", newDescription="測試描述", newColor="blue"))  ###OK
    

    # # 測試圖片操作
    # print("從 URL 新增單張圖片：")
    # print(EG.EAGLE_add_img_from_url(
    #     url="https://cover1.baozimh.org/cover/tx/woweixiedi/13_22_32_fecfb359afd95c39ecb5cffd6e74089c_1676298724340.webp",
    #     folderId="M4MTN1IV8O4GD",
    #     name="測試圖片",
    #     tags=["Test", "Sample"]
    # ))  ###OK

                                        # print("從多個 URL 新增圖片：")
                                        # items = [
                                        #     {"url": "https://example.com/sample1.jpg", "name": "圖片1", "tags": ["Tag1"]},
                                        #     {"url": "https://example.com/sample2.jpg", "name": "圖片2", "tags": ["Tag2"]},
                                        # ]
                                        # print(EAGLE_add_multiple_img_from_json(items=items, folderId="example_folder_id"))

    # # 測試書籤操作
    # print("新增書籤：")
    # print(EG.EAGLE_add_bookmark(url="https://example.com", name="測試書籤", tags=["Bookmark", "Test"]))  ### OK

    # # 測試雜項操作
    # print("獲取應用資訊：")
    # print(EG.EAGLE_get_application_info())  ### OK

    # print("獲取當前資源庫的詳細信息：")
    # library_info = EG.EAGLE_get_library_info()
    # print(library_info.keys())
    # print(library_info['data'].keys())
    # print(library_info['data'].get('library'))
    # print(library_info['data']['folders'])


    # current_library_path = EG.EAGLE_get_current_library_path()
    # print(f"當前 Eagle 資源庫的路徑是: {current_library_path}")
    

###### --------------------------------------------------------------
    # # 獲取前 10 個項目，按創建日期降序排列
    # print("獲取圖片列表（按創建日期降序排列）：")
    # result = EG.EAGLE_list_items(limit=10, orderBy="-CREATEDATE")
    # print(result)

    # # 按關鍵字過濾
    # print("按關鍵字 '設計' 搜尋：")
    # result = EG.EAGLE_list_items(keyword="loli")
    # # print(result)   ### list of dictionarys
    # print(type(result))
    # # print(result.keys())
    # print(result['data'].keys())
    # print(result['data']['data'][0])

    # # 按標籤過濾
    # print("按標籤 'Design' 和 'Poster' 過濾：")
    # result = EG.EAGLE_list_items(tags=["Design", "Poster"])
    # print(result)

    # # 按資料夾過濾
    # print("按資料夾 ID 過濾：")
    # result = EG.EAGLE_list_items(folders=["KAY6NTU6UYI5Q", "KBJ8Z60O88VMG"])
    # print(result)

    # # 按擴展名過濾
    # print("過濾所有 PNG 圖片：")
    # result = EG.EAGLE_list_items(ext="png")
    # print(result)



    # # 更新圖片標籤  ######還沒驗證
    # print("更新圖片標籤：")
    # result = EAGLE_update_item_tags(itemId="example_item_id", tags=["UpdatedTag1", "UpdatedTag2"])
    # print(result)








    df_folders_info = EG.EAGLE_get_folders_df()
    print(df_folders_info.head())  # 显示前 5 行
    print(df_folders_info.columns)

    

    folder_id = "LYZL8I7X27EE1"
    print(EG.get_folder_name(df_folders_info, folder_id))
    # cover_id = EG.get_folder_cover_id(df_folders_info, folder_id)
    # print(f"Cover ID for folder {folder_id}: {cover_id}")    
    # print(EG.get_folder_cover(folder_id))
        

    