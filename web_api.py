#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @Author: https://github.com/MltrCyber
# @Time: 2023/19/03
# @Update: 2023/16/08
# @Version: 1.0.0
# @instgram: https://instagram.com/haryonokudadiri
# @youtube : https://www.youtube.com/@pecintamantan


import os
import time
import json
import aiohttp
import uvicorn
import zipfile
import threading
import configparser

from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from pydantic import BaseModel
from starlette.responses import RedirectResponse

from scraper import Scraper

# Read config File
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
# Run PORT
port = int(config["Web_API"]["Port"])
# Domain Name
domain = config["Web_API"]["Domain"]
# Limiter
Rate_Limit = config["Web_API"]["Rate_Limit"]

# Buat instance FastAPI
title = "HARY-IT APis Tiktok Downloads"
version = '1.0.0'
update_time = "2023/08/15"
description = """
#### Description
<details>
<summary>Click to expand</summary>
> [Indonesia]
- Mengambil data Douyin dan TikTok dan mengembalikannya. Lebih banyak fitur sedang dalam pengembangan.
- Jika Anda membutuhkan lebih banyak antarmuka, silakan kunjungi [https://api.zone-ryy.asia/docs](https://api.zone-ryy.asia/docs).
- Proyek ini Dibuat Oleh HARY-IT [GitHub: HARY-IT](https://github.com/MltrCyber).
- Semua data titik akhir berasal dari antarmuka resmi Douyin dan TikTok. Jika Anda memiliki pertanyaan atau BUG atau saran, silakan beri masukan di [issues](
- Project ini Bisa Anda Dapatkan dengan menghubungi saya lewat instagram / Sosial Media saya yang lain.
> [English]
- Crawl the data of Douyin and TikTok and return it. More features are under development.
- If you need more interfaces, please visit [https://api.zone-ryy.asia/docs](https://api.zone-ryy.asia/docs).
- This Project Is Made By HARY-IT [GitHub: HARY-IT](https://github.com/MltrCyber).
- All endpoint data comes from the official interface of Douyin and TikTok. If you have any questions or BUGs or suggestions, please feedback in [issues](
- You can get this project by contacting me via Instagram / my other social media.
</details>
#### Contact author
<details>
<summary>Click to expand</summary>
- Instagram : haryonokudadiri
- Email: [haryonokudadiri71@gmail.com](mailto:haryonokudadiri71@gmail.com)
- Github: [https://github.com/MltrCyber](https://github.com/MltrCyber)
</details>
"""
tags_metadata = [
    {
        "name": "Root",
        "description": "Root path info.",
    },
    {
        "name": "API",
        "description": "Hybrid interface, automatically determine the input link and return the simplified data",
    },
    {
        "name": "Douyin",
        "description": "All Douyin API Endpoints",
    },
    {
        "name": "TikTok",
        "description": "All TikTok API Endpoints",
    },
    {
        "name": "Download",
        "description": "Enter the share link and return the download file response.",
    },
    {
        "name": "iOS_Shortcut",
        "description": "Get iOS shortcut info",
    },
]

# Buat objek Scraper
api = Scraper()

# Buat instance FastAPI
app = FastAPI(
    title=title,
    description=description,
    version=version,
    openapi_tags=tags_metadata
)

# Buat objek Pembatas
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

""" ________________________⬇️Model Respons Titik Akhir⬇️________________________"""


# API Root
class APIRoot(BaseModel):
    API_status: str
    Version: str = version
    Update_time: str = update_time
    Request_Rate_Limit: str = Rate_Limit
    Web_APP: str
    API_V1_Document: str
    TikHub_API_Document: str
    GitHub: str


# API untuk mendapatkan model dasar video
class iOS_Shortcut(BaseModel):
    version: str = None
    update: str = None
    link: str = None
    link_en: str = None
    note: str = None
    note_en: str = None


# API untuk mendapatkan model dasar video
class API_Video_Response(BaseModel):
    status: str = None
    platform: str = None
    endpoint: str = None
    message: str = None
    total_time: float = None
    aweme_list: list = None


# Model dasar API penguraian hibrid:
class API_Hybrid_Response(BaseModel):
    status: str = None
    message: str = None
    endpoint: str = None
    url: str = None
    type: str = None
    platform: str = None
    aweme_id: str = None
    total_time: float = None
    official_api_url: dict = None
    desc: str = None
    create_time: int = None
    author: dict = None
    music: dict = None
    statistics: dict = None
    cover_data: dict = None
    hashtags: list = None
    video_data: dict = None
    image_data: dict = None


# Model dasar versi hybrid parsing API lite:
class API_Hybrid_Minimal_Response(BaseModel):
    status: str = None
    message: str = None
    platform: str = None
    type: str = None
    wm_video_url: str = None
    wm_video_url_HQ: str = None
    nwm_video_url: str = None
    nwm_video_url_HQ: str = None
    no_watermark_image_list: list or None = None
    watermark_image_list: list or None = None


""" ________________________⬇️Log titik akhir⬇️________________________"""


# Rekam log permintaan API
async def api_logs(start_time, input_data, endpoint, error_data: dict = None):
    if config["Web_API"]["Allow_Logs"] == "True":
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        total_time = float(format(time.time() - start_time, '.4f'))
        file_name = "API_logs.json"
        # Tulis konten log
        with open(file_name, "a", encoding="utf-8") as f:
            data = {
                "time": time_now,
                "endpoint": f'/{endpoint}/',
                "total_time": total_time,
                "input_data": input_data,
                "error_data": error_data if error_data else "No error"
            }
            f.write(json.dumps(data, ensure_ascii=False) + ",\n")
        print('Berhasil')
        return 1
    else:
        print('Gagal / Server Down')
        return 0


""" ________________________⬇️Root endpoint⬇️________________________"""


# Root
@app.get("/", response_class=ORJSONResponse, response_model=APIRoot, tags=["Root"])
async def root():
    """
    Root path info.
    """
    data = {
        "API_status": "Running",
        "Version": version,
        "Update_time": update_time,
        "Request_Rate_Limit": Rate_Limit,
        "Web_APP": "https://zone-ryy.asia",
        "API_V1_Document": "https://api.zone-ryy.asia/docs",
        "Instagram": "https://instagram.com/haryonokudadiri",
        "GitHub": "https://github.com/MltrCyber",
    }
    return ORJSONResponse(data)


""" ________________________⬇️(Hybrid parsing endpoints)⬇️________________________"""



# Hybrid parsing endpoint, automatically determine the input link and return the simplified data.
@app.get("/api", tags=["API"], response_class=ORJSONResponse, response_model=API_Hybrid_Response)
@limiter.limit(Rate_Limit)
async def hybrid_parsing(request: Request, url: str, minimal: bool = False):
    """
        ## Usage
        - Get [Douyin|TikTok] single video data, the parameter is the video link or share code.
        ## Parameter
        #### url(Required)):
        - The video link.| Share code
        - Example:
        `https://www.douyin.com/video/7153585499477757192`
        `https://v.douyin.com/MkmSwy7/`
        `https://vt.tiktok.com/ZSLbWqyF5/`
        `https://www.tiktok.com/@tvamii/video/7045537727743380782`
        #### minimal(Optional Default:False):
        - Whether to return simplified data.
        - Example:
        `True`
        `False`
        ## Return
        - List of user single video data, list contains JSON data.
    """
    print("Mengambil data")
    # Waktu Mulai
    start_time = time.time()
    # Mengambil Data
    data = await api.hybrid_parsing(url)
    
    if minimal:
        result = api.hybrid_parsing_minimal(data)
    else:
        result = {
            'url': url,
            "endpoint": "/api/",
            "total_time": float(format(time.time() - start_time, '.4f')),
        }
        result.update(data)
    
    await api_logs(start_time=start_time,
                   input_data={'url': url},
                   endpoint='api')
    return ORJSONResponse(result)


""" ________________________(Douyin video parsing endpoint)⬇️________________________"""


# Get Douyin single video data
@app.get("/douyin_video_data/", response_class=ORJSONResponse, response_model=API_Video_Response, tags=["Douyin"])
@limiter.limit(Rate_Limit)
async def get_douyin_video_data(request: Request, douyin_video_url: str = None, video_id: str = None):
    """
    ## Tujuan/Penggunaan
    - Dapatkan satu data video pengguna Douyin, parameternya adalah tautan video|bagikan kata sandi
    - Dapatkan data satu video dari pengguna Douyin, parameternya adalah tautan video.
    ##Parameter/Parameter
    #### douyin_video_url (opsional/Opsional):
    - Tautan video. | bagikan kata sandi
    - Tautan video.|
    - Contoh/Contoh:
    `https://www.douyin.com/video/7153585499477757192`
    `https://v.douyin.com/MkmSwy7/`
    #### video_id (opsional/Opsional):
    - ID Video, yang dapat diperoleh dari tautan video.
    - ID video, dapat diperoleh dari tautan video.
    - Contoh/Contoh:
    `7153585499477757192`
    #### s_v_web_id (opsional/Opsional):
    - s_v_web_id, Anda dapat mengakses Douyin dari browser dan mendapatkannya dari cookie.
    - s_v_web_id, dapat diperoleh dari browser untuk mengakses Douyin dan kemudian dari cookie.
    - Contoh/Contoh:
    `s_v_web_id=verifikasi_leytkxgn_kvO5kOmO_SdMs_4t1o_B5ml_BUqtWM1mP6BF;`
    #### Catatan/Catatan:
    - Anda dapat memilih salah satu parameter `douyin_video_url` dan `video_id`, jika Anda mengisi keduanya, gunakan `video_id` terlebih dahulu untuk mendapatkan kecepatan respon yang lebih cepat.
    - Parameter `douyin_video_url` dan `video_id` dapat dipilih, jika keduanya diisi maka `video_id` digunakan terlebih dahulu untuk mendapatkan kecepatan respon yang lebih cepat.
    ## mengembalikan nilai/Mengembalikan
    - Pengguna adalah daftar data video, dan daftar tersebut berisi data JSON.
    - Daftar data video tunggal pengguna, daftar berisi data JSON.
    """
    if video_id is None or video_id == '':
        # ID Video
        video_id = await api.get_douyin_video_id(douyin_video_url)
        if video_id is None:
            result = {
                "status": "failed",
                "platform": "douyin",
                "message": "Failed to get video_id",
            }
            return ORJSONResponse(result)
    if video_id is not None and video_id != '':
        # Waktu Mulai
        start_time = time.time()
        print('Data video_id yang diperoleh:{}'.format(video_id))
        if video_id is not None:
            video_data = await api.get_douyin_video_data(video_id=video_id)
            if video_data is None:
                result = {
                    "status": "failed",
                    "platform": "douyin",
                    "endpoint": "/douyin_video_data/",
                    "message": "Failed to get video API data",
                }
                return ORJSONResponse(result)
            # print('Video_data yang diperoleh:{}'.format(video_data))
            # Mencatat panggilan API
            await api_logs(start_time=start_time,
                           input_data={'douyin_video_url': douyin_video_url, 'video_id': video_id},
                           endpoint='douyin_video_data')
            # Akhir waktu
            total_time = float(format(time.time() - start_time, '.4f'))
            # mengembalikan data
            result = {
                "status": "success",
                "platform": "douyin",
                "endpoint": "/douyin_video_data/",
                "message": "Got video data successfully",
                "total_time": total_time,
                "aweme_list": [video_data]
            }
            return ORJSONResponse(result)
        else:
            print('Gagal mendapatkan vibrato video_id')
            result = {
                "status": "failed",
                "platform": "douyin",
                "endpoint": "/douyin_video_data/",
                "message": "Failed to get video ID",
                "total_time": 0,
                "aweme_list": []
            }
            return ORJSONResponse(result)


@app.get("/douyin_live_video_data/", response_class=ORJSONResponse, response_model=API_Video_Response, tags=["Douyin"])
@limiter.limit(Rate_Limit)
async def get_douyin_live_video_data(request: Request, douyin_live_video_url: str = None, web_rid: str = None):
    """
    ## Cara Penggunaan/Usage
    - Dapatkan data video langsung Douyin, parameternya adalah tautan video|bagikan kata sandi
    - Get the data of a Douyin live video, the parameter is the video link.
    ## Menunggu perbaikan/Waiting for repair
    """
    if web_rid is None or web_rid == '':
        # dapatkan id video
        web_rid = await api.get_douyin_video_id(douyin_live_video_url)
        if web_rid is None:
            result = {
                "status": "failed",
                "platform": "douyin",
                "message": "Failed to get web_rid",
            }
            return ORJSONResponse(result)
    if web_rid is not None and web_rid != '':
        # Waktu mulai
        start_time = time.time()
        print('Web_rid yang diperoleh:{}'.format(web_rid))
        if web_rid is not None:
            video_data = await api.get_douyin_live_video_data(web_rid=web_rid)
            if video_data is None:
                result = {
                    "status": "failed",
                    "platform": "douyin",
                    "endpoint": "/douyin_live_video_data/",
                    "message": "Failed to get live video API data",
                }
                return ORJSONResponse(result)
            # print('video_data yang diperoleh: {}'.format(video_data))
            # Mencatat panggilan API
            await api_logs(start_time=start_time,
                           input_data={'douyin_video_url': douyin_live_video_url, 'web_rid': web_rid},
                           endpoint='douyin_live_video_data')
            # Akhir waktu
            total_time = float(format(time.time() - start_time, '.4f'))
            # mengembalikan data
            result = {
                "status": "success",
                "platform": "douyin",
                "endpoint": "/douyin_live_video_data/",
                "message": "Got live video data successfully",
                "total_time": total_time,
                "aweme_list": [video_data]
            }
            return ORJSONResponse(result)
        else:
            print('Gagal mendapatkan vibrato video_id')
            result = {
                "status": "failed",
                "platform": "douyin",
                "endpoint": "/douyin_live_video_data/",
                "message": "Failed to get live video ID",
                "total_time": 0,
                "aweme_list": []
            }
            return ORJSONResponse(result)


@app.get("/douyin_profile_videos/", response_class=ORJSONResponse, response_model=None, tags=["Douyin"])
async def get_douyin_user_profile_videos(tikhub_token: str, douyin_user_url: str = None):
    """
    ## Usage
    - Get the data of a Douyin user profile, the parameter is the user link or ID.
    ## Parameter
    tikhub_token: https://api.tikhub.io/#/Authorization/login_for_access_token_user_login_post
    """
    response = await api.get_douyin_user_profile_videos(tikhub_token=tikhub_token, profile_url=douyin_user_url)
    return response


@app.get("/douyin_profile_liked_videos/", response_class=ORJSONResponse, response_model=None, tags=["Douyin"])
async def get_douyin_user_profile_liked_videos(tikhub_token: str, douyin_user_url: str = None):
    """
    ## Usage
    - Get the data of a Douyin user profile liked videos, the parameter is the user link or ID.
    ## Parameter
    tikhub_token: https://api.tikhub.io/#/Authorization/login_for_access_token_user_login_post
    """
    response = await api.get_douyin_profile_liked_data(tikhub_token=tikhub_token, profile_url=douyin_user_url)
    return response


@app.get("/douyin_video_comments/", response_class=ORJSONResponse, response_model=None, tags=["Douyin"])
async def get_douyin_video_comments(tikhub_token: str, douyin_video_url: str = None):
    """
    ## Usage
    - Get the data of a Douyin video comments, the parameter is the video link.
    ## Parameter
    tikhub_token: https://api.tikhub.io/#/Authorization/login_for_access_token_user_login_post
    """
    response = await api.get_douyin_video_comments(tikhub_token=tikhub_token, video_url=douyin_video_url)
    return response


""" ________________________⬇️TikTok video parsing endpoint⬇️________________________"""


# Get TikTok single video data
@app.get("/tiktok_video_data/", response_class=ORJSONResponse, response_model=API_Video_Response, tags=["TikTok"])
@limiter.limit(Rate_Limit)
async def get_tiktok_video_data(request: Request, tiktok_video_url: str = None, video_id: str = None):
    """
        ## Usage
        - Get single video data, the parameter is the video link.
        ## Parameter
        #### tiktok_video_url(Optional):
        - The video link.| Share code
        - Example:
        `https://www.tiktok.com/@hary_it/video/7263098269348269317`
        `https://vt.tiktok.com/ZSLbWqyF5/`
        #### video_id(Optional):
        - The video ID, can be obtained from the video link.
        - Example:
        `7263098269348269317`
        #### Note:
        - The parameters `tiktok_video_url` and `video_id` can be selected, if both are filled in, the `video_id` is used first to get a faster response speed.
        ## Return
        - List of user single video data, list contains JSON data.
        """
    # Waktu mulai
    start_time = time.time()
    if video_id is None or video_id == "":
        video_id = await api.get_tiktok_video_id(tiktok_video_url)
        if video_id is None:
            return ORJSONResponse({"status": "fail", "platform": "tiktok", "endpoint": "/tiktok_video_data/",
                                   "message": "Get video ID failed"})
    if video_id is not None and video_id != '':
        print('Mulai parsing satu data video TikTok')
        video_data = await api.get_tiktok_video_data(video_id)
        # If the TikTok API data is empty or there is no video data in the returned data, an error message is returned
        if video_data is None or video_data.get('aweme_id') != video_id:
            print('Failed to get video data')
            result = {
                "status": "failed",
                "platform": "tiktok",
                "endpoint": "/tiktok_video_data/",
                "message": "Failed to get video data"
            }
            return ORJSONResponse(result)
        # Mencatat panggilan API
        await api_logs(start_time=start_time,
                       input_data={'tiktok_video_url': tiktok_video_url, 'video_id': video_id},
                       endpoint='tiktok_video_data')
        # Akhir waktu
        total_time = float(format(time.time() - start_time, '.4f'))
        # mengembalikan data
        result = {
            "status": "success",
            "platform": "tiktok",
            "endpoint": "/tiktok_video_data/",
            "message": "Got video data successfully",
            "total_time": total_time,
            "aweme_list": [video_data]
        }
        return ORJSONResponse(result)
    else:
        print('Video link error')
        result = {
            "status": "failed",
            "platform": "tiktok",
            "endpoint": "/tiktok_video_data/",
            "message": "Video link error"
        }
        return ORJSONResponse(result)


# Get TikTok user video data
@app.get("/tiktok_profile_videos/", response_class=ORJSONResponse, response_model=None, tags=["TikTok"])
async def get_tiktok_profile_videos(tikhub_token: str, tiktok_video_url: str = None):
    """
    ## Usage
    - Get the data of a Douyin user profile, the parameter is the user link or ID.
    ## Parameter
    tikhub_token: https://api.tikhub.io/#/Authorization/login_for_access_token_user_login_post
    """
    response = await api.get_tiktok_user_profile_videos(tikhub_token=tikhub_token, tiktok_video_url=tiktok_video_url)
    return response


# Get TikTok user profile liked video data
@app.get("/tiktok_profile_liked_videos/", response_class=ORJSONResponse, response_model=None, tags=["TikTok"])
async def get_tiktok_profile_liked_videos(tikhub_token: str, tiktok_video_url: str = None):
    """
    ## Usage
    - Get the data of a Douyin user profile liked video, the parameter is the user link or ID.
    ## Parameter
    tikhub_token: https://api.tikhub.io/#/Authorization/login_for_access_token_user_login_post
    """
    response = await api.get_tiktok_user_profile_liked_videos(tikhub_token=tikhub_token, tiktok_video_url=tiktok_video_url)
    return response


""" ________________________⬇️(iOS Shortcut update endpoint)⬇️________________________"""


@app.get("/ios", response_model=iOS_Shortcut, tags=["iOS_Shortcut"])
async def Get_Shortcut():
    data = {
        'version': config["Web_API"]["iOS_Shortcut_Version"],
        'update': config["Web_API"]['iOS_Shortcut_Update_Time'],
        'link': config["Web_API"]['iOS_Shortcut_Link'],
        'link_en': config["Web_API"]['iOS_Shortcut_Link_EN'],
        'note': config["Web_API"]['iOS_Shortcut_Update_Note'],
        'note_en': config["Web_API"]['iOS_Shortcut_Update_Note_EN'],
    }
    return ORJSONResponse(data)


""" ________________________⬇️(Download file endpoints/functions)⬇️________________________"""


# Download file endpoint
@app.get("/download", tags=["Download"])
@limiter.limit(Rate_Limit)
async def download_file_hybrid(request: Request, url: str, prefix: bool = True, watermark: bool = False):
    """
        ## Usage
        ### [English]
        - Submit the [Douyin|TikTok] link as a parameter to this endpoint and return the [video|picture] file download request.
        # Parameter
        - url:str ->  [Douyin|TikTok] [video|image] link
        - prefix: bool -> [True/False] Whether to add a prefix
        - watermark: bool -> [True/False] Whether to add a watermark
        """
    # Whether to enable this endpoint
    if config["Web_API"]["Download_Switch"] != "True":
        return ORJSONResponse({"status": "endpoint closed",
                               "message": "This endpoint is closed, please enable it in the configuration file"})
    # Waktu mulai
    start_time = time.time()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    data = await api.hybrid_parsing(url)
    if data is None:
        return ORJSONResponse(data)
    else:
        # Mencatat panggilan API
        await api_logs(start_time=start_time,
                       input_data={'url': url},
                       endpoint='download')
        url_type = data.get('type')
        platform = data.get('platform')
        aweme_id = data.get('aweme_id')
        file_name_prefix = config["Web_API"]["File_Name_Prefix"] if prefix else ''
        root_path = config["Web_API"]["Download_Path"]
        # Periksa apakah direktori itu ada, buatlah jika tidak ada
        if not os.path.exists(root_path):
            os.makedirs(root_path)
        if url_type == 'video':
            file_name = file_name_prefix + platform + '_' + aweme_id + '.mp4' if not watermark else file_name_prefix + platform + '_' + aweme_id + '_watermark' + '.mp4'
            url = data.get('video_data').get('nwm_video_url_HQ') if not watermark else data.get('video_data').get(
                'wm_video_url_HQ')
            print('url: ', url)
            file_path = root_path + "/" + file_name
            print('file_path: ', file_path)
            # Tentukan apakah file tersebut ada, dan kembalikan langsung jika ada
            if os.path.exists(file_path):
                print('File sudah ada, langsung kembalikan')
                return FileResponse(path=file_path, media_type='video/mp4', filename=file_name)
            else:
                if platform == 'douyin':
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url=url, headers=headers, allow_redirects=False) as response:
                            r = response.headers
                            cdn_url = r.get('location')
                            async with session.get(url=cdn_url) as res:
                                r = await res.content.read()
                elif platform == 'tiktok':
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url=url, headers=headers) as res:
                            r = await res.content.read()
                with open(file_path, 'wb') as f:
                    f.write(r)
                return FileResponse(path=file_path, media_type='video/mp4', filename=file_name)
        elif url_type == 'image':
            url = data.get('image_data').get('no_watermark_image_list') if not watermark else data.get(
                'image_data').get('watermark_image_list')
            print('url: ', url)
            zip_file_name = file_name_prefix + platform + '_' + aweme_id + '_images.zip' if not watermark else file_name_prefix + platform + '_' + aweme_id + '_images_watermark.zip'
            zip_file_path = root_path + "/" + zip_file_name
            print('zip_file_name: ', zip_file_name)
            print('zip_file_path: ', zip_file_path)
            # Tentukan apakah file tersebut ada, langsung kembalikan jika ada,
            if os.path.exists(zip_file_path):
                print('File sudah ada, langsung kembalikan')
                return FileResponse(path=zip_file_path, media_type='zip', filename=zip_file_name)
            file_path_list = []
            for i in url:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url=i, headers=headers) as res:
                        content_type = res.headers.get('content-type')
                        file_format = content_type.split('/')[1]
                        r = await res.content.read()
                index = int(url.index(i))
                file_name = file_name_prefix + platform + '_' + aweme_id + '_' + str(
                    index + 1) + '.' + file_format if not watermark else \
                    file_name_prefix + platform + '_' + aweme_id + '_' + str(
                        index + 1) + '_watermark' + '.' + file_format
                file_path = root_path + "/" + file_name
                file_path_list.append(file_path)
                print('file_path: ', file_path)
                with open(file_path, 'wb') as f:
                    f.write(r)
                if len(url) == len(file_path_list):
                    zip_file = zipfile.ZipFile(zip_file_path, 'w')
                    for f in file_path_list:
                        zip_file.write(os.path.join(f), f, zipfile.ZIP_DEFLATED)
                    zip_file.close()
                    return FileResponse(path=zip_file_path, media_type='zip', filename=zip_file_name)
        else:
            return ORJSONResponse(data)


# Batch download file endpoint
@app.get("/batch_download", tags=["Download"])
async def batch_download_file(url_list: str, prefix: bool = True):
    """
    Batch download file endpoint
    Unfinished
    """
    print('url_list: ', url_list)
    return ORJSONResponse({"status": "failed",
                           "message": "Hehehe, this function hasn't been done yet, I'll do it when I have time"})


# Douyin link format download endpoint(video)
@app.get("/video/{aweme_id}", tags=["Download"])
async def download_douyin_video(aweme_id: str, prefix: bool = True, watermark: bool = False):
    """
    ## Usage
    ### [English]
    - Change the Douyin domain name to the current server domain name to call this endpoint and return the video file download request.
    - For example, the original link: https://douyin.com/video/1234567890123456789 becomes https://api.zone-ryy.asia/video/1234567890123456789 to call this endpoint.
    # Parameter
    - aweme_id:str -> Douyin video ID
    - prefix: bool -> [True/False] Whether to add a prefix
    - watermark: bool -> [True/False] Whether to add a watermark
    """
    # Whether to enable this endpoint
    if config["Web_API"]["Download_Switch"] != "True":
        return ORJSONResponse({"status": "endpoint closed",
                               "message": "This endpoint is closed, please enable it in the configuration file"})
    video_url = f"https://www.douyin.com/video/{aweme_id}"
    download_url = f"{domain}/download?url={video_url}&prefix={prefix}&watermark={watermark}"
    return RedirectResponse(download_url)


# Douyin link format download endpoint(video)
@app.get("/note/{aweme_id}", tags=["Download"])
async def download_douyin_video(aweme_id: str, prefix: bool = True, watermark: bool = False):
    """
    ## Usage
    ### [English]
    - Change the Douyin domain name to the current server domain name to call this endpoint and return the video file download request.
    - For example, the original link: https://douyin.com/video/1234567890123456789 becomes https://api.zone-ryy.asia/video/1234567890123456789 to call this endpoint.
    # Parameter
    - aweme_id:str -> Douyin video ID
    - prefix: bool -> [True/False] Whether to add a prefix
    - watermark: bool -> [True/False] Whether to add a watermark
    """
    # Whether to enable this endpoint
    if config["Web_API"]["Download_Switch"] != "True":
        return ORJSONResponse({"status": "endpoint closed",
                               "message": "This endpoint is closed, please enable it in the configuration file"})
    video_url = f"https://www.douyin.com/video/{aweme_id}"
    download_url = f"{domain}/download?url={video_url}&prefix={prefix}&watermark={watermark}"
    return RedirectResponse(download_url)


# Douyin link format download endpoint
@app.get("/discover", tags=["Download"])
async def download_douyin_discover(modal_id: str, prefix: bool = True, watermark: bool = False):
    """
    ## Usage
    ### [English]
    - Change the Douyin domain name to the current server domain name to call this endpoint and return the video file download request.
    - For example, the original link: https://douyin.com/discover?modal_id=1234567890123456789 becomes https://api.zone-ryy.asia/discover?modal_id=1234567890123456789 to call this endpoint.
    # Parameter
    - modal_id: str -> Douyin video ID
    - prefix: bool -> [True/False] Whether to add a prefix
    - watermark: bool -> [True/False] Whether to add a watermark
    """
    # Whether to enable this endpoint
    if config["Web_API"]["Download_Switch"] != "True":
        return ORJSONResponse({"status": "endpoint closed",
                               "message": "This endpoint is closed, please enable it in the configuration file"})
    video_url = f"https://www.douyin.com/discover?modal_id={modal_id}"
    download_url = f"{domain}/download?url={video_url}&prefix={prefix}&watermark={watermark}"
    return RedirectResponse(download_url)


# Tiktok link format download endpoint(video)
@app.get("/{user_id}/video/{aweme_id}", tags=["Download"])
async def download_tiktok_video(user_id: str, aweme_id: str, prefix: bool = True, watermark: bool = False):
    """
        ## Usage
        ### [English]
        - Change the TikTok domain name to the current server domain name to call this endpoint and return the video file download request.
        - For example, the original link: https://www.tiktok.com/@hary_it/video/7263098269348269317 becomes https://api.zone-ryy.asia/@evil0ctal/video/7263098269348269317 to call this endpoint.
        # Parameter
        - user_id: str -> TikTok user ID
        - aweme_id: str -> TikTok video ID
        - prefix: bool -> [True/False] Whether to add a prefix
        - watermark: bool -> [True/False] Whether to add a watermark
        """
    # Whether to enable this endpoint
    if config["Web_API"]["Download_Switch"] != "True":
        return ORJSONResponse({"status": "endpoint closed",
                               "message": "This endpoint is closed, please enable it in the configuration file"})
    video_url = f"https://www.tiktok.com/{user_id}/video/{aweme_id}"
    download_url = f"{domain}/download?url={video_url}&prefix={prefix}&watermark={watermark}"
    return RedirectResponse(download_url)



# Periodically clean the [Download_Path] folder
def cleanup_path():
    while True:
        root_path = config["Web_API"]["Download_Path"]
        timer = int(config["Web_API"]["Download_Path_Clean_Timer"])
        # Periksa apakah direktori tersebut ada, lewati jika tidak ada
        if os.path.exists(root_path):
            time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"{time_now}: Cleaning up the download folder...")
            for file in os.listdir("./download"):
                file_path = os.path.join("./download", file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(e)
        else:
            time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            print(f"{time_now}: The download folder does not exist, skipping...")
        time.sleep(timer)


""" ________________________⬇️(Project start execution function)⬇️________________________"""


# Execute after program startup
@app.on_event("startup")
async def startup_event():
    # Create a timer thread to clean up the download directory and start it
    download_path_clean_switches = True if config["Web_API"]["Download_Path_Clean_Switch"] == "True" else False
    if download_path_clean_switches:
        # Start cleaning thread
        thread_1 = threading.Thread(target=cleanup_path)
        thread_1.start()


if __name__ == '__main__':
    # It is recommended to use gunicorn to start, when using uvicorn to start, please set debug to False
    # uvicorn web_api:app --host '0.0.0.0' --port 8000 --reload
    uvicorn.run("web_api:app", host='0.0.0.0', port=port, reload=True, access_log=False)
