from fastapi import FastAPI, HTTPException
try:
    from botasaurus import AntiDetectDriver
except ImportError:
    from botasaurus.browser import Driver as AntiDetectDriver
import time
import logging

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Video Extractor API", description="API to extract video URLs from qushuiyin.me")

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse('static/index.html')

@app.get("/get_video")
def get_video(url: str):
    """
    Extract video download URL from qushuiyin.me
    Args:
        url: The video URL to process
    Returns:
        dict: Contains the extracted video download URL
    """
    logger.info(f"Starting video extraction for URL: {url}")

    driver = None
    try:
        # 使用 AntiDetectDriver 来绕过检测
        logger.info("Initializing AntiDetectDriver...")
        driver = AntiDetectDriver(
            headless=True,  # 无头模式
            wait_for_complete_page_load=True,
            block_images=True,  # 加速加载
        )
        logger.info("Driver initialized successfully")

        # 访问网站
        logger.info("Navigating to https://qushuiyin.me/...")
        driver.get("https://qushuiyin.me/")
        time.sleep(3)  # 等待页面加载
        logger.info("Page loaded, checking for CF shield bypass...")

        # 检查页面标题或内容确认加载成功
        page_title = driver.title
        logger.info(f"Page title: {page_title}")
        if "Just a moment" in page_title or "Checking your browser" in str(driver.bs4):
            logger.warning("CF shield detected, attempting bypass...")
            time.sleep(5)  # 额外等待 CF 检查
        else:
            logger.info("Page loaded without CF shield issues")

        # 查找输入框并输入 URL
        logger.info("Looking for input box...")
        # 基于提供的 HTML: <input type="text" class="n-input__input-el" ...>
        input_selectors = [".n-input__input-el", "input[placeholder*='Sora']", "input[type='text']"]
        input_box = None
        for selector in input_selectors:
            try:
                if driver.exists(selector):
                    input_box = driver.select(selector) # Botasaurus way if available, or use selenium method
                    # Fallback to selenium find_element if driver.select isn't standard selenium
                    if not input_box:
                         input_box = driver.find_element_by_css_selector(selector)
                    
                    if input_box and input_box.is_displayed():
                        logger.info(f"Found input box with selector: {selector}")
                        break
            except:
                continue

        if not input_box:
            logger.error("Input box not found with any selector")
            # 打印一下页面源码的前一部分帮助调试
            logger.info(f"Page source snippet: {str(driver.bs4)[:500]}")
            raise Exception("Input box not found")

        logger.info(f"Inputting URL: {url}")
        # Botasaurus driver.type is recommended
        driver.type(selector, url)
        
        # 查找并点击"立即获取"按钮
        logger.info("Looking for submit button...")
        # 基于 HTML: <button ... class="... submit-btn ...">
        button_selectors = [".submit-btn", "button:contains('立即获取')"]
        submit_button = None
        for selector in button_selectors:
            try:
                if driver.exists(selector):
                    logger.info(f"Found submit button with selector: {selector}")
                    # 确保按钮不再是 disabled 状态
                    time.sleep(1) 
                    driver.click(selector)
                    submit_button = True
                    break
            except:
                continue

        if not submit_button:
            logger.error("Submit button not found")
            raise Exception("Submit button not found")

        # 等待结果
        logger.info("Waiting for results...")
        # 等待视频元素或下载链接出现
        # 假设成功后会出现 video 标签或特定的下载按钮
        try:
            driver.wait_for_element("video, a[href*='.mp4'], .download-btn", wait=30)
        except:
            logger.warning("Timeout waiting for specific result elements, checking page content...")

        # 提取视频链接
        logger.info("Extracting video link...")
        video_url = None
        
        # 1. 检查 video 标签
        try:
            video_element = driver.get_element_or_none("video")
            if video_element:
                video_url = video_element.get_attribute("src")
                logger.info(f"Found video URL in <video> tag: {video_url}")
        except:
            pass

        # 2. 如果没有，检查下载链接
        if not video_url:
            links = driver.links("a")
            for link in links:
                href = link.get_attribute("href")
                if href and (".mp4" in href or "download" in href):
                    video_url = href
                    logger.info(f"Found video URL in <a> tag: {video_url}")
                    break
        
        # 3. 最后的手段：在页面文本中搜索 URL
        if not video_url:
            import re
            page_text = driver.text("body")
            # 寻找类似 https://...mp4 的链接
            url_match = re.search(r'https?://[^\s"]+\.mp4[^\s"]*', page_text)
            if url_match:
                video_url = url_match.group()
                logger.info(f"Extracted video URL from text: {video_url}")

        driver.quit()
        driver = None

        if not video_url:
            logger.error("Video URL not found in page")
            raise Exception("Video URL not found")

        logger.info(f"Successfully extracted video URL: {video_url}")
        return {"video_url": video_url}

    except Exception as e:
        logger.error(f"Error extracting video: {str(e)}")
        if driver:
            try:
                driver.quit()
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error extracting video: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)