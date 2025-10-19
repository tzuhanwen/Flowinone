from .fetcher import EagleApi
from .folder_manager import EagleFolder, EagleFolders
from .image_manager import EagleImage


class Eagle:

    def __init__(self, port: int = 41595, raise_on_error: bool = False) -> None:
        self.eg = EagleApi(port, raise_on_error)
        self.folder = EagleFolder(self.eg)
        self.folders = EagleFolders(self.eg)
        self.image = EagleImage(self.eg)
    
    ##### 雜 #####

    def get_tags(self):
        """
        獲取 Eagle 庫中所有標籤。
        """
        return self.eg.request("tag/list")

    def get_item_info(self, item_id: str):
        """
        取得指定項目的詳細資訊。
        """
        response = self.eg.request("item/info", "GET", {"itemId": item_id})
        if response.get("status") == "success":
            return response

        # 某些版本的 API 可能使用 id 參數。
        return self.eg.request("item/info", "GET", {"id": item_id})


    def get_application_info(self):
        """
        獲取 Eagle App 應用資訊。
        """
        return self.eg.request("application/info")

    def get_library_info(self, raise_on_error: bool = False):
        """
        獲取當前運行的 Eagle 資源庫的詳細信息。

        Returns:
            dict: 包含資源庫詳細信息的字典。如果請求失敗，返回錯誤信息。
        """
        data = self.eg.request("library/info", "GET", raise_on_error=raise_on_error)
        return data

    def get_current_library_path(self) -> str:
        """
        获取当前 Eagle 资源库的路径。

        Returns:
            str: 当前资源库的路径。如果请求失败或路径未找到，则返回错误信息。
        """
        lib_info = self.eg.request("library/info", "GET")

        # 提取资源库路径
        library_path = lib_info.get("library", {}).get("path")
        if not library_path:
            raise ValueError("Library path not found in response.")
        
        return library_path

    def update_item_tags(self, itemId: str, tags: list[str]):
        """                 
        未驗證
        更新指定圖片的標籤。

        Args:
            itemId (str): 圖片的 ID。
            tags (List[str]): 新的標籤列表。

        Returns:
            dict: 包含更新操作結果的字典。
        """
        payload = {"itemId": itemId, "tags": tags}
        return self.eg.request("item/update", "POST", payload)



    def list_items(
        self, 
        limit: int = 200,
        offset: int = 0, 
        orderBy: str | None = None, 
        keyword: str | None = None, 
        ext: str | None = None, 
        # reverse: bool = False,  # (reverse目前無法使用，API有bug)
        tags: list[str] | None = None,
        folders: list[str] | None = None
    ):
        """
        重要的搜尋功能
        使用 /api/item/list 獲取圖片列表。

        Args:
            limit (int): 返回的最大項目數量，默認為 200。
            offset (int): 偏移量，用於分頁，默認為 0。
            orderBy (Optional[str]): 排序方式，可用值：CREATEDATE, FILESIZE, NAME, RESOLUTION。
            reverse (bool): 是否按降序排序，默认为 False（升序）。
            keyword (Optional[str]): 按關鍵字過濾。
            ext (Optional[str]): 按文件擴展名過濾，如 jpg, png。
            tags (Optional[List[str]]): 按標籤過濾，列表中的標籤以逗號分隔。
            folders (Optional[List[str]]): 按資料夾過濾，資料夾 ID 列表以逗號分隔。

        Returns:
            dict: 包含請求結果的字典。

        """
        
        ### 目前reverse功能壞掉
        # # 构建排序参数，添加 "-" 表示降序
        # if orderBy and reverse:
        #     print('reverse true----------')
        #     orderBy = f"-{orderBy}"

        # 构建请求参数
        payload = {
            "limit": limit,
            "offset": offset,
            "orderBy": orderBy,
            "keyword": keyword,
            "ext": ext,
            "tags": tags,
            "folders": ",".join(folders) if folders else None,
        }
        # 过滤掉值为 None 的键
        payload = {k: v for k, v in payload.items() if v is not None}

        # 使用通用请求函数
        return self.eg.request("item/list", "GET", payload)


    # #### 之後再做
    # def add_items_from_path(self, filePaths: list[str], folderId: str):
    #     """
    #     批量將本地文件導入到指定資料夾。

    #     Args:
    #         filePaths (List[str]): 文件的絕對路徑列表。
    #         folderId (str): 資料夾的 ID。

    #     Returns:
    #         dict: 包含導入操作結果的字典。
    #     """

    #     payload = {"paths": filePaths, "folderId": folderId}
    #     data = self.eg.request(
    #         'http://localhost:41595/api/item/addFromPath', "POST", payload
    #     )

    #     if data is None:
    #         raise ValueError("Failed to add items from path.")