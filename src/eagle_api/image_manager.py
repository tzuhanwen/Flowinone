from .fetcher import EagleApi

class EagleImage:

    def __init__(self, eagle: EagleApi):
        self.eg = eagle

    def add_img_from_json(self, payload):
        return self.eg.request("item/addFromURL", "POST", payload)
    
    # query 圖片用
    def get_list(self):
        pass
        # 去jupyter notebook找

    ##### 下載圖片用 ######

    def add_image_from_url(
        self, 
        url: str, 
        folderId: str, 
        name: str | None = None, 
        website: str | None = None,
        tags: list[str] | None = None
    ):
        """
        從 URL 新增單張圖片。

        ### 這個跟下面一次新增多個的函數是一起的，想好怎麼設計
        ### 注意重複時目前得手動更改
        """

        # data = {
        #     "url": "http://imgcdn.atyun.com/2018/09/1_7PdM6h3jL3lDRS1b1CR9Wg.png",
        #     "folderId": 'LDUADJJ4IBNUA',
        #     "name": "test_dsfsdfsdfg",
        #     "website": "https://test123/default",
        #     "tags": ["Illustration", "Design"],
        #     # "headers": {XDD} #爬蟲用
        # }

        payload = {"url": url, "folderId": folderId, "name": name, "website": website, "tags": tags}
        return self.eg.request("item/addFromURL", "POST", payload)





    # EAGLE_add_images_from_urls
    def add_multiple_from_json(self, payload):
        ### 舊版，沒使用GPT
        ### 注意重複時目前得手動更改

        ### download multiple images example
        # data = {
        #   "items": [
        #       {
        #           "url": "http://imgcdn.atyun.com/2018/09/0_7i8JA5t1Nx3HlK4E-e1536217892333.jpg",
        # #           "name": "Work", #不命名就會用原始檔名
        # #           "website": "https://dribbble.com/shots/12020761-Work", #可命可不命
        # #           "tags": ["Illustration", "Design"],
        #       },
        #       {
        #           "url": "http://imgcdn.atyun.com/2018/09/1_EM8x5jAL-SeUUG7b4anCQg.gif",
        # #           "name": "Work2", #不命名就會用原始檔名
        # #           "website": "https://dribbble.com/shots/12061400-work2", #可命可不命
        # #           "tags": ["Illustration", "Design"],
        #       }
        #   ],
        #   "folderId": 'LDUCBHJTFP952',
        # }
        # EAGLE_add_multiple_img_from_json(data)

        return self.eg.request("item/addFromURLs", "POST", payload)


    def add_bookmark(self, url: str, name: str, tags: list[str] | None = None):
        """
        新增書籤。
        ### 注意項目重複時目前得手動更改
        
        ### add_bookmark example
        eg.EAGLE_add_bookmark(
            url = "https://www.pixiv.net/artworks/83585181",
            name = "アルトリア･キャスター",
            tags = ['aa','bb_test']
        )    
        """

        payload = {"url": url, "name": name, "tags": tags}
        return self.eg.request("item/addBookmark", "POST", payload)

