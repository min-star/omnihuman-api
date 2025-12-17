# app.py
import streamlit as st
import json
import time
import requests
import datetime
import hashlib
import hmac
import sys
import os
from PIL import Image
import numpy as np
from io import BytesIO

# ======================
# 基础配置
# ======================
method = 'POST'
host = 'visual.volcengineapi.com'
region = 'cn-north-1'
endpoint = 'https://visual.volcengineapi.com'
service = 'cv'

# ======================
# V4 签名相关
# ======================
def sign(key, msg):
    return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

def getSignatureKey(key, dateStamp, regionName, serviceName):
    kDate = sign(key.encode('utf-8'), dateStamp)
    kRegion = sign(kDate, regionName)
    kService = sign(kRegion, serviceName)
    kSigning = sign(kService, 'request')
    return kSigning

def formatQuery(parameters):
    return "&".join(f"{k}={parameters[k]}" for k in sorted(parameters))

def signV4Request(access_key, secret_key, service, req_query, req_body):
    if not access_key or not secret_key:
        return None

    t = datetime.datetime.utcnow()
    current_date = t.strftime('%Y%m%dT%H%M%SZ')
    datestamp = t.strftime('%Y%m%d')

    canonical_uri = '/'
    canonical_querystring = req_query
    signed_headers = 'content-type;host;x-content-sha256;x-date'
    payload_hash = hashlib.sha256(req_body.encode('utf-8')).hexdigest()
    content_type = 'application/json'

    canonical_headers = (
        f'content-type:{content_type}\n'
        f'host:{host}\n'
        f'x-content-sha256:{payload_hash}\n'
        f'x-date:{current_date}\n'
    )

    canonical_request = (
        method + '\n' +
        canonical_uri + '\n' +
        canonical_querystring + '\n' +
        canonical_headers + '\n' +
        signed_headers + '\n' +
        payload_hash
    )

    algorithm = 'HMAC-SHA256'
    credential_scope = f'{datestamp}/{region}/{service}/request'
    string_to_sign = (
        algorithm + '\n' +
        current_date + '\n' +
        credential_scope + '\n' +
        hashlib.sha256(canonical_request.encode()).hexdigest()
    )

    signing_key = getSignatureKey(secret_key, datestamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

    authorization_header = (
        f'{algorithm} Credential={access_key}/{credential_scope}, '
        f'SignedHeaders={signed_headers}, Signature={signature}'
    )

    headers = {
        'X-Date': current_date,
        'Authorization': authorization_header,
        'X-Content-Sha256': payload_hash,
        'Content-Type': content_type
    }

    try:
        r = requests.post(endpoint + '?' + canonical_querystring,
                          headers=headers, data=req_body, timeout=60)
        r.raise_for_status()
        return r.text.replace("\\u0026", "&").replace(r'\&', '&')
    except Exception as e:
        print("Request error:", e)
        return None
    

def load_image_from_url(url):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return Image.open(BytesIO(r.content)).convert("RGBA")

def crop_by_mask(image: Image.Image, mask: Image.Image, out_size=256):
    """
    image: 原图 (RGB / RGBA)
    mask:  二值 mask (0 / 255), L / RGB / RGBA
    """

    mask_np = np.array(mask)

    # 统一成单通道 mask
    if mask_np.ndim == 3:
        mask_bin = mask_np[:, :, 0]
    else:
        mask_bin = mask_np

    # 找 mask == 255 的区域
    ys, xs = np.where(mask_bin == 255)
    if len(xs) == 0:
        return None

    x1, x2 = xs.min(), xs.max()
    y1, y2 = ys.min(), ys.max()

    # 裁剪（右下角要 +1）
    cropped = image.crop((x1, y1, x2 + 1, y2 + 1))

    # === 按最长边缩放 ===
    w, h = cropped.size
    scale = out_size / max(w, h)
    new_w = int(round(w * scale))
    new_h = int(round(h * scale))

    cropped = cropped.resize((new_w, new_h), Image.BILINEAR)

    return cropped



# ======================
# Streamlit 状态初始化
# ======================
def init_state():
    defaults = {
        "stage": "idle",
        "mask_list": None,
        "selected_mask": None,
        "task_id": None,
        "video_url": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()




UPLOAD_DIR = "/home/min/work/A_data/A_dog_talking/"
PUBLIC_BASE_URL = "https://intellectual-western-lake-mainland.trycloudflare.com"

os.makedirs(UPLOAD_DIR, exist_ok=True)


import uuid

def save_uploaded_file(uploaded_file, suffix):
    filename = f"{uuid.uuid4().hex}.{suffix}"
    path = os.path.join(UPLOAD_DIR, filename)
    print(path)
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return f"{PUBLIC_BASE_URL}/{filename}"

def save_Image_file(image_file, suffix):
    filename = f"{uuid.uuid4().hex}.{suffix}"
    path = os.path.join(UPLOAD_DIR, filename)
    print(path)
    image_file.save(path)
    return f"{PUBLIC_BASE_URL}/{filename}"


# ======================
# UI
# ======================
st.set_page_config("即梦数字人视频生成", layout="centered")
st.title("🎬 即梦 · 数字人视频生成（完整整合版）")

st.markdown("### 🔐 凭证")
access_key = st.text_input("Access Key", type="password")
secret_key = st.text_input("Secret Key", type="password")

# st.markdown("### 📥 输入")
# image_url = st.text_input(
#     "图片 URL",
#     "https://intellectual-western-lake-mainland.trycloudflare.com/last.jpg"
# )
# audio_url = st.text_input(
#     "音频 URL",
#     "https://intellectual-western-lake-mainland.trycloudflare.com/output.mp3"
# )

st.markdown("### ✏️ 驱动 Prompt")

prompt = st.text_area(
    "请输入生成提示词（可选）",
    placeholder="例如：自然表情，说话时嘴型清晰，真实光照，稳定人脸",
    height=100
)


st.markdown("### 📥 输入（拖拽）")

col1, col2 = st.columns(2)

with col1:
    uploaded_image = st.file_uploader(
        "🖼 拖拽图片（JPG / PNG）",
        type=["jpg", "jpeg", "png"]
    )

with col2:
    uploaded_audio = st.file_uploader(
        "🎵 拖拽音频（MP3）",
        type=["mp3", "wav"]
    )

image_url = None
audio_url = None

if uploaded_image:
    image_url = save_uploaded_file(uploaded_image, "jpg")
    # print(image_url)
    st.image(image_url, caption="已上传图片", width=256)

if uploaded_audio:
    audio_url = save_uploaded_file(uploaded_audio, "mp3")
    st.audio(audio_url)

# print("8"*50)
# print(image_url)

# ======================
# Step 1：检测
# ======================
if st.session_state.stage == "idle":
    if st.button("🔍 开始检测"):
        with st.spinner("目标检测中..."):
            query = formatQuery({"Action": "CVProcess", "Version": "2022-08-31"})
            body = json.dumps({
                "req_key": "jimeng_realman_avatar_object_detection",
                "image_url": image_url
            })

            resp_str = signV4Request(access_key, secret_key, service, query, body)
            if not resp_str:
                st.error("检测失败")
                st.stop()

            resp = json.loads(resp_str)
            resp_data = json.loads(resp["data"]["resp_data"])
            st.session_state.mask_list = resp_data["object_detection_result"]["mask"]["url"]
            st.session_state.stage = "detected"
           


            origin_img = load_image_from_url(image_url)

            mask_urls_ = resp_data["object_detection_result"]["mask"]["url"]

            visual_masks = []

            mask_urls = []

            for url in mask_urls_:
                mask_img = load_image_from_url(url)
                mask_urls.append(save_Image_file(mask_img, "png"))
            
            for url in mask_urls:
                try:
                    mask_img = load_image_from_url(url)
                    preview = crop_by_mask(origin_img, mask_img)

                    if preview:
                        visual_masks.append({
                            "mask_url": url,
                            "preview": preview
                        })
                except Exception as e:
                    print("mask error:", e)

            visual_masks.append({
                "mask_url": None,            # 关键：None 表示不使用 mask
                "preview": origin_img.resize((256, 256)),
                "label": "原图（不使用 Mask）"
            })

            st.session_state.masks = visual_masks
            st.session_state.stage = "detected"

            st.experimental_rerun()


# ======================
# Step 2：选择 mask
# ======================
# if st.session_state.stage == "detected":
#     st.success(f"检测完成，共 {len(st.session_state.mask_list)} 个 mask")
#     st.session_state.selected_mask = st.selectbox(
#         "请选择一个 mask",
#         st.session_state.mask_list
#     )
#     if st.button("➡️ 使用该 mask"):
#         st.session_state.stage = "mask_selected"
#         st.experimental_rerun()
if st.session_state.stage == "detected":
    st.success(f"检测完成，共 {len(st.session_state.masks)} 个主体")

    cols = st.columns(4)
    selected_index = None

    # for i, item in enumerate(st.session_state.masks):
    #     with cols[i % 4]:
    #         st.image(item["preview"], width=220)
    #         if st.button(f"选择 #{i+1}", key=f"mask_{i}"):
    #             selected_index = i
    for i, item in enumerate(st.session_state.masks):
        with cols[i % 4]:
            st.image(item["preview"], width=220)

            label = f"主体 #{i}" if item["mask_url"] is not None else '原图'
            if st.button(f"选择 {label}", key=f"mask_{i}"):
                selected_index = i


    if selected_index is not None:
        st.session_state.selected_mask = st.session_state.masks[selected_index]["mask_url"]
        st.session_state.stage = "mask_selected"
        st.experimental_rerun()

# ======================
# Step 3：提交任务
# ======================
if st.session_state.stage == "mask_selected":
    with st.spinner("提交生成任务中..."):
        query = formatQuery({"Action": "CVSubmitTask", "Version": "2022-08-31"})
        body = json.dumps({
            "req_key": "jimeng_realman_avatar_picture_omni_v15",
            "image_url": image_url,
            "mask_url": [st.session_state.selected_mask] if st.session_state.selected_mask else [],
            "audio_url": audio_url,
            "prompt": prompt
        })

        resp_str = signV4Request(access_key, secret_key, service, query, body)
        if not resp_str:
            st.error("提交失败")
            st.stop()

        resp = json.loads(resp_str)
        st.session_state.task_id = resp["data"]["task_id"]
        st.session_state.stage = "submitted"
        st.experimental_rerun()

# ======================
# Step 4：轮询
# ======================
if st.session_state.stage == "submitted":
    st.markdown("### ⏳ 视频生成中")
    bar = st.progress(10)
    query = formatQuery({"Action": "CVGetResult", "Version": "2022-08-31"})
    body = json.dumps({
        "req_key": "jimeng_realman_avatar_picture_omni_v15",
        "task_id": st.session_state.task_id
    })

    for i in range(1, 200):
        resp_str = signV4Request(access_key, secret_key, service, query, body)
        resp = json.loads(resp_str)
        if resp["data"]["status"] == "done":
            st.session_state.video_url = resp["data"]["video_url"]
            st.session_state.stage = "done"
            bar.progress(100)
            st.experimental_rerun()
        bar.progress(min(10 + i * 3, 95))
        time.sleep(3)

    st.error("任务超时")

# ======================
# Step 5：结果 + 下载
# ======================
# if st.session_state.stage == "done":
#     st.success("🎉 生成完成")
#     st.video(st.session_state.video_url)

#     video_path = "result.mp4"
#     if not os.path.exists(video_path):
#         with requests.get(st.session_state.video_url, stream=True) as r:
#             with open(video_path, "wb") as f:
#                 for chunk in r.iter_content(1024 * 1024):
#                     if chunk:
#                         f.write(chunk)

#     with open(video_path, "rb") as f:
#         st.download_button(
#             "📥 下载视频",
#             f,
#             file_name="result.mp4",
#             mime="video/mp4"
#         )

#     if st.button("🔄 重新开始"):
#         for k in list(st.session_state.keys()):
#             del st.session_state[k]
#         st.experimental_rerun()

import uuid
from datetime import datetime

if st.session_state.stage == "done":
    st.success("🎉 生成完成")
    st.video(st.session_state.video_url)

    # === 生成 日期 + UUID 文件名 ===
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    filename = f"result_{date_str}_{uid}.mp4"
    video_path = os.path.join("res", filename)  # 可改为你想保存的目录

    # === 下载并缓存 ===
    if not os.path.exists(video_path):
        with requests.get(st.session_state.video_url, stream=True) as r:
            r.raise_for_status()
            with open(video_path, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)

    # === 下载按钮 ===
    with open(video_path, "rb") as f:
        st.download_button(
            "📥 下载视频",
            f,
            file_name=filename,
            mime="video/mp4"
        )

    # === 重置 ===
    if st.button("🔄 重新开始"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

