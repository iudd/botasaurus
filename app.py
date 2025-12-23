from fastapi import FastAPI, HTTPException
try:
    from botasaurus import AntiDetectDriver
except ImportError:
    from botasaurus.browser import Driver as AntiDetectDriver
import time
import logging
import os
import random

# 内置代理池
BUILTIN_PROXIES = [
    "http://46.62.171.144:80",
    "http://18.202.158.161:80",
    "http://45.4.202.170:999",
    "http://200.59.186.176:999",
    "http://5.202.176.42:80",
    "http://134.209.29.120:8080",
    "http://103.30.211.34:80",
    "http://8.213.195.191:3333",
    "http://8.220.204.215:8086",
    "http://47.91.89.3:8081",
    "http://8.211.195.139:8081",
    "http://62.99.135.51:80",
    "http://87.239.31.42:80",
    "http://8.137.62.53:8081",
    "http://8.243.68.11:8080",
    "http://47.121.183.107:9080",
    "http://154.31.113.209:80",
    "http://200.33.20.25:80",
    "http://94.184.25.4:80",
    "http://47.91.89.3:1081",
    "http://38.54.9.151:3128",
    "http://47.91.89.3:6379",
    "http://103.253.43.144:80",
    "http://190.116.28.148:80",
    "http://8.211.51.115:4022",
    "http://188.245.91.223:80",
]

def get_proxy_pool():
    """获取代理池（内置 + 环境变量）"""
    proxy_pool = BUILTIN_PROXIES.copy()
    
    # 从环境变量获取额外代理
    env_proxies = os.getenv("PROXY_URL", "")
    if env_proxies:
        # 支持多个代理，用逗号或分号分隔
        additional_proxies = [p.strip() for p in env_proxies.replace(';', ',').split(',') if p.strip()]
        proxy_pool.extend(additional_proxies)
        logger.info(f"Added {len(additional_proxies)} proxies from environment variable")
    
    logger.info(f"Total proxy pool size: {len(proxy_pool)}")
    return proxy_pool

def get_random_proxy():
    """从代理池中随机选择一个代理"""
    proxy_pool = get_proxy_pool()
    if proxy_pool:
        selected_proxy = random.choice(proxy_pool)
        logger.info(f"Selected proxy: {selected_proxy}")
        return selected_proxy
    return None

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
        
        # 从代理池随机选择一个代理
        proxy_url = get_random_proxy()
        
        driver = AntiDetectDriver(
            headless=True,  # 保持 headless 模式
            wait_for_complete_page_load=True,
            block_images=True,  # 加速加载
            proxy=proxy_url,  # 使用随机选择的代理
        )
        logger.info("Driver initialized successfully")

        # 启用人类模拟模式，这对过盾至关重要
        try:
            logger.info("Enabling human mode...")
            driver.enable_human_mode()
        except:
            pass

        # 访问网站
        logger.info("Navigating to https://qushuiyin.me/...")
        # 关键：使用 bypass_cloudflare=True 来自动绕过 Turnstile
        driver.get("https://qushuiyin.me/", bypass_cloudflare=True)
        
        # 额外等待确保页面完全加载
        time.sleep(3)

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
            
            # 验证输入是否成功
            input_value = driver.get_attribute(input_selector_found, "value")
            logger.info(f"Input box value after typing: {input_value}")
            if not input_value:
                logger.warning("Input box is empty! Trying run_js to set value...")
                driver.run_js(f"document.querySelector('{input_selector_found}').value = '{url}'")
                # 触发 input 事件以激活按钮状态
                driver.run_js(f"document.querySelector('{input_selector_found}').dispatchEvent(new Event('input', {{ bubbles: true }}))")

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
                    button_selector_found = selector
                    break
            except Exception as e:
                logger.info(f"Button selector {selector} failed: {str(e)}")
                continue

        if not button_selector_found:
            logger.error("Submit button not found")
            logger.info(f"Page source snippet: {page_source[:500]}")
            raise Exception("Submit button not found")

        # 尝试解决 Turnstile
        logger.info("Checking for Turnstile widget...")
        turnstile_selector = "iframe[src*='challenges.cloudflare.com']"
        if driver.is_element_present(turnstile_selector):
            logger.info("Turnstile iframe found. Attempting to click...")
            try:
                # 尝试点击 iframe 区域
                driver.click(turnstile_selector)
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Failed to click Turnstile: {e}")

        # 关键修改：等待按钮启用（通过 Turnstile 验证）
        logger.info("Waiting for submit button to become enabled (Turnstile check)...")
        is_enabled = False
        for i in range(30): # 等待 30 秒
            try:
                # 检查 disabled 属性
                is_disabled_attr = driver.get_attribute(button_selector_found, "disabled")
                # 检查 class 是否包含 disabled
                class_attr = driver.get_attribute(button_selector_found, "class")
                is_disabled_class = "disabled" in class_attr if class_attr else False
                
                if is_disabled_attr is None and not is_disabled_class:
                    logger.info("Submit button is enabled!")
                    is_enabled = True
                    break
                else:
                    if i % 5 == 0: # 每5秒尝试重新点击一下 Turnstile
                        logger.info(f"Button still disabled. Re-attempting Turnstile click...")
                        try:
                            driver.click(turnstile_selector)
                        except:
                            pass
                    else:
                        logger.info(f"Button still disabled. Waiting...")
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Error checking button state: {e}")
                time.sleep(1)
        
        if not is_enabled:
            logger.error("Submit button remained disabled. Turnstile verification likely failed.")
            # 即使失败也尝试点击，也许只是状态没更新
            logger.warning("Attempting to click disabled button anyway...")

        driver.click(button_selector_found)

        # 等待结果
        logger.info("Waiting for results...")
        try:
            # 等待 video 或 下载链接
            driver.wait_for_element("video, a[href*='.mp4'], .download-btn", wait=60) # 增加等待时间到 60秒
            logger.info("Wait for element completed")
        except:
            logger.warning("Timeout waiting for specific result elements")
            # 打印当前页面状态帮助调试
            try:
                html_snippet = driver.page_html[:1000]
                logger.info(f"Page HTML snippet after timeout: {html_snippet}")
            except:
                pass

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

        try:
            driver.close()
        except:
            pass
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