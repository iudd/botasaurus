from fastapi import FastAPI, HTTPException
from botasaurus import AntiDetectDriver
import time

app = FastAPI(title="Video Extractor API", description="API to extract video URLs from qushuiyin.me")

@app.get("/")
def read_root():
    return {"message": "Video Extractor API", "endpoint": "/get_video?url=<video_url>"}

@app.get("/get_video")
def get_video(url: str):
    """
    Extract video download URL from qushuiyin.me
    Args:
        url: The video URL to process
    Returns:
        dict: Contains the extracted video download URL
    """
    try:
        # 使用 AntiDetectDriver 来绕过检测
        driver = AntiDetectDriver(
            headless=True,  # 无头模式
            wait_for_complete_page_load=True,
            block_images=True,  # 加速加载
        )

        # 访问网站
        driver.get("https://qushuiyin.me/")
        time.sleep(2)  # 等待页面加载

        # 查找输入框并输入 URL
        input_box = driver.find_element_by_css_selector("input[type='text'], input[name='url'], textarea")  # 根据实际页面调整选择器
        if not input_box:
            raise Exception("Input box not found")

        input_box.send_keys(url)

        # 查找并点击“立即获取”按钮
        submit_button = driver.find_element_by_css_selector("button[type='submit'], input[type='submit'], .submit-btn")  # 根据实际页面调整选择器
        if not submit_button:
            raise Exception("Submit button not found")

        submit_button.click()

        # 等待结果
        time.sleep(5)  # 根据网站响应时间调整

        # 提取视频链接（根据实际页面结构调整选择器）
        video_link = driver.find_element_by_css_selector("a[href*='download'], .video-link, .result a")  # 根据实际页面调整
        if video_link:
            video_url = video_link.get_attribute("href")
        else:
            # 如果是文本，查找包含链接的元素
            result_element = driver.find_element_by_css_selector(".result, .output, #result")
            video_url = result_element.text if result_element else None

        driver.quit()

        if not video_url:
            raise Exception("Video URL not found")

        return {"video_url": video_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting video: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)