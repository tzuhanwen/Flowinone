import pandas as pd
from .fetcher import EagleApi


class EagleFolder:
    def __init__(self, eagle: EagleApi):
        self.eg = eagle

    def create(self, folderName: str):  # tags: Optional[List[str]] = None
        """
        https://api.eagle.cool/folder/create
        創建新的資料夾。

        tags目前創建失敗
        parent id還沒弄
        """
        payload = {"folderName": folderName}  # , "tags": tags
        return self.eg.request("folder/create", "POST", payload)

    def update_name(self, folderId: str, newName: str):
        """
        重命名資料夾。
        """
        payload = {"folderId": folderId, "newName": newName}
        return self.eg.request("folder/rename", "POST", payload)

    def EAGLE_update_folder_details(
        self,
        folderId: str,
        newName: str | None = None,
        newDescription: str | None = None,
        newColor: str | None = None,
    ):
        """
        更新資料夾屬性（名稱、描述、顏色）。

        var data = {
        "folderId": "KMUFMKTBHINM4",
        "newName": "New Name",
        "newDescription": "New Description",
        "newColor": "red"
        };

        """
        payload = {"folderId": folderId}
        if newName:
            payload["newName"] = newName
        if newDescription:
            payload["newDescription"] = newDescription
        if newColor:
            payload["newColor"] = newColor
        return self.eg.request("folder/update", "POST", payload)


class EagleFolders:
    def __init__(self, eagle: EagleApi):
        self.eg = eagle

    def get_folders(self):
        """
        獲取所有資料夾列表。
        """
        return self.eg.request("folder/list")

    def get_recent_folders(self):
        """
        獲取最近使用的資料夾列表。
        """
        return self.eg.request("folder/listRecent")

    def get_df(self) -> pd.DataFrame:
        """
        获取 Eagle 文件夹列表，并将其转换为 Pandas DataFrame。

        Returns:
            pd.DataFrame: 包含文件夹信息的 DataFrame，如果请求失败，则返回空 DataFrame。
        """
        folders = self.get_folders()
        if folders is None:
            return pd.DataFrame()  # 返回空的 DataFrame

        # 提取文件夹数据
        if not folders:
            print("No folder data found.")
            return pd.DataFrame()

        return pd.DataFrame(folders)

    def get_df_all(self, flatten: bool = True) -> pd.DataFrame:
        """
        获取 Eagle 文件夹列表，并将其转换为 Pandas DataFrame。
        如果 flatten=True，會遞迴展開所有 children folders 合併成一張表。

        Returns:
            pd.DataFrame: 包含所有資料夾（包括子資料夾）的資訊。
        """
        folders = self.get_folders()
        if folders is None:
            return pd.DataFrame()  # 返回空的 DataFrame

        # 提取文件夹数据
        if not folders:
            print("No folder data found.")
            return pd.DataFrame()

        all_folders = []

        def extract_folder_info(folder, parent_name=""):
            # 加入當前資料夾
            info = folder.copy()
            info["parentName"] = parent_name
            info.pop("children", None)  # 暫時移除 children，避免 DataFrame 爆掉
            all_folders.append(info)

            # 遞迴加入 children 資訊
            for child in folder.get("children", []):
                extract_folder_info(child, parent_name=folder.get("name"))

        for folder in folders:
            extract_folder_info(folder)

        return pd.DataFrame(all_folders)
