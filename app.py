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
        
        # 尝试自动绕过 CF
        try:
            logger.info("Attempting detect_and_bypass_cloudflare...")
            driver.detect_and_bypass_cloudflare()
        except Exception as e:
            logger.warning(f"detect_and_bypass_cloudflare failed: {e}")

        # 检查页面标题或内容确认加载成功
        page_title = driver.title
        logger.info(f"Page title: {page_title}")
        
        # 获取页面源码
        page_source = ""
        try:
            page_source = driver.page_html
        except Exception as e:
            logger.warning(f"Failed to get page_html: {str(e)}")

        if "Just a moment" in page_title or "Checking your browser" in page_source:
            logger.warning("CF shield detected (still present after bypass attempt)...")
            time.sleep(5)
        else:
            logger.info("Page loaded without CF shield issues")

        # 查找输入框并输入 URL
        logger.info("Looking for input box...")
        # 基于提供的 HTML: <input type="text" class="n-input__input-el" ...>
        input_selectors = [".n-input__input-el", "input[placeholder*='Sora']", "input[type='text']"]
        input_selector_found = None
        
        for selector in input_selectors:
            try:
                logger.info(f"Checking selector: {selector}")
                if driver.is_element_present(selector):
                    logger.info(f"Selector {selector} exists")
                    input_selector_found = selector
                    break
            except Exception as e:
                logger.info(f"Error checking selector {selector}: {str(e)}")
                continue

        if not input_selector_found:
            logger.error("Input box not found with any selector")
            logger.info(f"Page source snippet: {page_source[:500]}")
            raise Exception("Input box not found")

        logger.info(f"Inputting URL: {url}")
        try:
            # 使用 Botasaurus 的 type 方法
            driver.type(input_selector_found, url)
        except Exception as e:
            logger.error(f"Failed to input URL: {str(e)}")
            raise

        # 查找并点击"立即获取"按钮
        logger.info("Looking for submit button...")
        button_selectors = [".submit-btn", "button:contains('立即获取')"]
        button_selector_found = None
        
        for selector in button_selectors:
            try:
                logger.info(f"Checking button selector: {selector}")
                if driver.is_element_present(selector):
                    logger.info(f"Found submit button with selector: {selector}")
                    # 确保按钮不再是 disabled 状态
                    time.sleep(1) 
                    driver.click(selector)
                    button_selector_found = selector
                    break
            except Exception as e:
                logger.info(f"Button selector {selector} failed: {str(e)}")
                continue

        if not button_selector_found:
            logger.error("Submit button not found")
            logger.info(f"Page source snippet: {page_source[:500]}")
            raise Exception("Submit button not found")

        # 等待结果
        logger.info("Waiting for results...")
        try:
            # 等待 video 或 下载链接
            driver.wait_for_element("video, a[href*='.mp4'], .download-btn", wait=30)
            logger.info("Wait for element completed")
        except:
            logger.warning("Timeout waiting for specific result elements")

        # 提取视频链接
        logger.info("Extracting video link...")
        video_url = None
        
        # 1. 检查 video 标签
        try:
            if driver.is_element_present("video"):
                video_url = driver.get_attribute("video", "src")
                logger.info(f"Found video URL in <video> tag: {video_url}")
        except:
            pass

        # 2. 如果没有，检查下载链接
        if not video_url:
            try:
                # 获取所有链接并过滤
                links = driver.get_all_links()
                for link in links:
                    if link and (".mp4" in link or "download" in link):
                        video_url = link
                        logger.info(f"Found video URL in links: {video_url}")
                        break
            except Exception as e:
                logger.warning(f"Error checking links: {e}")
        
        # 3. 最后的手段：在页面文本中搜索 URL
        if not video_url:
            logger.info("Trying fallback text search...")
            try:
                # 更新源码
                page_source = driver.page_html
                import re
                url_match = re.search(r'https?://[^\s"]+\.mp4[^\s"]*', page_source)
                if url_match:
                    video_url = url_match.group()
                    logger.info(f"Extracted video URL from text: {video_url}")
            except Exception as e:
                logger.error(f"Fallback search failed: {str(e)}")

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