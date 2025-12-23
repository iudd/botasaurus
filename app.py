from fastapi import FastAPI, HTTPException
try:
    from botasaurus import AntiDetectDriver
except ImportError:
    from botasaurus.browser import Driver as AntiDetectDriver
import time
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        if "Just a moment" in page_title or "Checking your browser" in driver.page_source:
            logger.warning("CF shield detected, attempting bypass...")
            time.sleep(5)  # 额外等待 CF 检查
        else:
            logger.info("Page loaded without CF shield issues")

        # 查找输入框并输入 URL
        logger.info("Looking for input box...")
        input_selectors = ["input[type='text']", "input[name='url']", "input[placeholder*='url']", "textarea"]
        input_box = None
        for selector in input_selectors:
            try:
                input_box = driver.find_element_by_css_selector(selector)
                if input_box and input_box.is_displayed():
                    logger.info(f"Found input box with selector: {selector}")
                    break
            except:
                continue

        if not input_box:
            logger.error("Input box not found with any selector")
            raise Exception("Input box not found")

        logger.info(f"Inputting URL: {url}")
        input_box.clear()
        input_box.send_keys(url)

        # 查找并点击"立即获取"按钮
        logger.info("Looking for submit button...")
        button_selectors = ["button[type='submit']", "input[type='submit']", ".submit-btn", "button:contains('立即获取')", "input[value*='获取']"]
        submit_button = None
        for selector in button_selectors:
            try:
                if "contains" in selector:
                    # 对于文本包含的按钮，需要用 XPath
                    xpath = f"//button[contains(text(),'立即获取')] | //input[contains(@value,'立即获取')]"
                    submit_button = driver.find_element_by_xpath(xpath)
                else:
                    submit_button = driver.find_element_by_css_selector(selector)
                if submit_button and submit_button.is_displayed():
                    logger.info(f"Found submit button with selector: {selector}")
                    break
            except:
                continue

        if not submit_button:
            logger.error("Submit button not found with any selector")
            raise Exception("Submit button not found")

        logger.info("Clicking submit button...")
        submit_button.click()

        # 等待结果
        logger.info("Waiting for results...")
        time.sleep(10)  # 根据网站响应时间调整

        # 提取视频链接
        logger.info("Extracting video link...")
        link_selectors = ["a[href*='download']", "a[href*='.mp4']", ".video-link a", ".result a", ".output a"]
        video_link = None
        for selector in link_selectors:
            try:
                video_link = driver.find_element_by_css_selector(selector)
                if video_link and video_link.is_displayed():
                    logger.info(f"Found video link with selector: {selector}")
                    break
            except:
                continue

        video_url = None
        if video_link:
            video_url = video_link.get_attribute("href")
            logger.info(f"Extracted video URL from link: {video_url}")
        else:
            # 如果是文本，查找包含链接的元素
            result_selectors = [".result", ".output", "#result", ".video-url"]
            for selector in result_selectors:
                try:
                    result_element = driver.find_element_by_css_selector(selector)
                    if result_element and result_element.is_displayed():
                        text = result_element.text
                        logger.info(f"Found result text: {text}")
                        # 尝试提取 URL
                        import re
                        url_match = re.search(r'https?://[^\s]+', text)
                        if url_match:
                            video_url = url_match.group()
                            logger.info(f"Extracted video URL from text: {video_url}")
                            break
                except:
                    continue

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