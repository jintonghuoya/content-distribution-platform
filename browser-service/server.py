"""Playwright Browser Service — 宿主机运行。

这是一个独立的 FastAPI 服务，在宿主机上运行，提供浏览器自动化能力。
Docker 里的 CDP API 通过 HTTP 调用此服务来发布内容到微博/小红书等平台。

用法：
    cd browser-service
    pip install -r requirements.txt
    playwright install chromium
    python server.py

配置：
    默认监听 0.0.0.0:8001
    登录态文件存放在 ./data/ 目录下

API：
    POST /publish/weibo       — 发布微博
    POST /publish/xiaohongshu — 发布小红书
    GET  /status/{platform}   — 检查平台登录状态
    GET  /health              — 健康检查
"""

import json
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel

# 数据目录：登录态文件存放位置
DATA_DIR = Path(os.environ.get("BROWSER_DATA_DIR", "./data")).resolve()
WEIBO_STATE = DATA_DIR / "weibo_state.json"
XHS_STATE = DATA_DIR / "xiaohongshu_state.json"


# ──────────────────────────────────────────
# Request models
# ──────────────────────────────────────────

class PublishRequest(BaseModel):
    title: str = ""
    body: str = ""


class PublishResponse(BaseModel):
    success: bool
    platform_url: str = ""
    error_message: str = ""


# ──────────────────────────────────────────
# Browser helpers
# ──────────────────────────────────────────

async def _get_browser():
    """创建 Playwright 浏览器实例。"""
    from playwright.async_api import async_playwright

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    return pw, browser


async def _check_login(platform: str) -> dict:
    """检查指定平台的登录状态。"""
    state_file = WEIBO_STATE if platform == "weibo" else XHS_STATE

    if not state_file.exists():
        return {"logged_in": False, "error": f"登录态文件不存在: {state_file}"}

    try:
        pw, browser = await _get_browser()
        context = await browser.new_context(storage_state=str(state_file))

        if platform == "weibo":
            page = await context.new_page()
            await page.goto("https://weibo.com/", wait_until="networkidle", timeout=30000)
            logged_in = "login" not in page.url and "passport" not in page.url
        elif platform == "xiaohongshu":
            page = await context.new_page()
            await page.goto(
                "https://creator.xiaohongshu.com/publish/publish",
                wait_until="networkidle",
                timeout=30000,
            )
            logged_in = "login" not in page.url and "passport" not in page.url
        else:
            logged_in = False

        await browser.close()
        await pw.stop()

        return {"logged_in": logged_in}
    except Exception as e:
        return {"logged_in": False, "error": str(e)}


async def _publish_weibo(text: str) -> PublishResponse:
    """通过浏览器发布微博。

    使用有头模式(headless=False)，弹出浏览器窗口。
    点击发送后如果弹出滑块验证码，暂停等用户手动拖完（最多5分钟），
    然后继续发布流程。同一个浏览器会话，不重新来。
    """
    from playwright.async_api import async_playwright

    if not WEIBO_STATE.exists():
        return PublishResponse(
            success=False,
            error_message=f"微博登录态不存在: {WEIBO_STATE}，请先运行登录脚本",
        )

    captcha_selectors = [
        '[class*="captcha"]',
        '[class*="verify"]',
        '[class*="slider"]',
        '[class*="geetest"]',
        '[id*="captcha"]',
        '[id*="verify"]',
    ]

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=False)
    context = await browser.new_context(
        storage_state=str(WEIBO_STATE),
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
    )
    page = await context.new_page()

    try:
        logger.info("[Weibo] Opening weibo.com...")
        await page.goto("https://weibo.com/", wait_until="networkidle", timeout=30000)

        if "login" in page.url or "passport" in page.url:
            return PublishResponse(success=False, error_message="微博登录态已过期")

        # 点击发布输入框
        logger.info("[Weibo] Clicking compose area...")
        compose = page.locator(
            'textarea[placeholder], [class*="editor-input"], '
            '[class*="compose"] textarea, [class*="Input_ele"]'
        )
        compose_count = await compose.count()
        logger.info(f"[Weibo] Found {compose_count} compose elements")

        if compose_count > 0:
            await compose.first.click()
            await page.wait_for_timeout(500)
        else:
            hint = page.locator('[placeholder*="新鲜事"], [placeholder*="想说"], div[class*="placeholder"]')
            hint_count = await hint.count()
            logger.info(f"[Weibo] Trying hint locators, found {hint_count}")
            if hint_count > 0:
                await hint.first.click()
                await page.wait_for_timeout(500)

        # 清空编辑框
        logger.info("[Weibo] Clearing compose area...")
        await page.keyboard.press("Control+a")
        await page.wait_for_timeout(100)
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(300)

        # 输入正文
        logger.info(f"[Weibo] Typing text ({len(text)} chars)...")
        await page.keyboard.type(text, delay=30)
        await page.wait_for_timeout(500)

        # 关闭话题弹窗
        logger.info("[Weibo] Closing topic popup...")
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(500)
        await page.mouse.click(10, 10)
        await page.wait_for_timeout(500)

        # 点击发布按钮
        logger.info("[Weibo] Clicking publish...")
        publish_btn = page.locator('button:has-text("发送"):visible, a:has-text("发送"):visible')
        btn_count = await publish_btn.count()
        logger.info(f"[Weibo] Found {btn_count} send button(s)")

        if btn_count == 0:
            publish_btn = page.locator('button:has-text("发布"):visible, a:has-text("发布"):visible')
            btn_count = await publish_btn.count()
            logger.info(f"[Weibo] Found {btn_count} publish button(s)")

        if btn_count > 0:
            await publish_btn.first.click()
        else:
            logger.warning("[Weibo] No publish button found, trying Ctrl+Enter")
            await page.keyboard.press("Control+Enter")

        await page.wait_for_timeout(2000)

        # 处理确认弹窗
        confirm_btn = page.locator('button:has-text("确认"):visible, button:has-text("确定"):visible')
        if await confirm_btn.count() > 0:
            logger.info("[Weibo] Found confirm dialog, clicking...")
            await confirm_btn.first.click()
            await page.wait_for_timeout(2000)

        # 检测验证码 — 同一个浏览器会话里等用户操作，不重新来
        for sel in captcha_selectors:
            if await page.locator(f'{sel}:visible').count() > 0:
                logger.info(f"[Weibo] Captcha detected ({sel}), waiting for user...")
                logger.info("[Weibo] >>> 滑块验证窗口已弹出，请手动完成验证（最多5分钟）")
                # 等验证码消失（用户拖完滑块后弹窗会关闭）
                try:
                    await page.wait_for_function(
                        "() => !document.querySelector('[class*=\"captcha\"], [class*=\"verify\"], [class*=\"slider\"], [class*=\"geetest\"]')",
                        timeout=300_000,
                    )
                    logger.info("[Weibo] Captcha solved by user, continuing...")
                except Exception:
                    return PublishResponse(success=False, error_message="验证码超时（5分钟未完成）")
                break

        await page.wait_for_timeout(3000)

        # 检查发布后状态
        await page.screenshot(path=str(DATA_DIR / "weibo_step4_after_publish.png"))

        error_el = page.locator('[class*="error"], [class*="fail"]')
        if await error_el.count() > 0:
            error_text = await error_el.first.text_content()
            if error_text and any(k in error_text for k in ("失败", "错误", "请登录")):
                return PublishResponse(success=False, error_message=f"微博: {error_text}")

        # 更新登录态
        new_state = await context.storage_state()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(WEIBO_STATE, "w") as f:
            json.dump(new_state, f)

        logger.info("[Weibo] Published successfully")
        return PublishResponse(success=True, platform_url=page.url)

    except Exception as e:
        logger.error(f"[Weibo] Error: {e}")
        return PublishResponse(success=False, error_message=f"微博发布异常: {e}")
    finally:
        await browser.close()
        await pw.stop()


async def _publish_xiaohongshu(title: str, body: str) -> PublishResponse:
    """通过浏览器发布小红书笔记。"""
    from playwright.async_api import async_playwright

    if not XHS_STATE.exists():
        return PublishResponse(
            success=False,
            error_message=f"小红书登录态不存在: {XHS_STATE}，请先运行登录脚本",
        )

    pw, browser = await _get_browser()
    context = await browser.new_context(
        storage_state=str(XHS_STATE),
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1920, "height": 1080},
    )
    page = await context.new_page()

    try:
        logger.info("[XHS] Opening publish page...")
        await page.goto(
            "https://creator.xiaohongshu.com/publish/publish",
            wait_until="networkidle",
            timeout=30000,
        )

        if "login" in page.url or "passport" in page.url:
            return PublishResponse(success=False, error_message="小红书登录态已过期")

        await page.screenshot(path=str(DATA_DIR / "xhs_step1_loaded.png"))
        logger.info("[XHS] Step 1: Page loaded")

        # 1. 点击"写长文"
        logger.info("[XHS] Clicking '写长文'...")
        article_tab = page.locator('text="写长文"')
        if await article_tab.count() > 0:
            await article_tab.click()
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(2000)
            logger.info(f"[XHS] Navigated to: {page.url}")

        await page.screenshot(path=str(DATA_DIR / "xhs_step2_article_page.png"))
        logger.info("[XHS] Step 2: Article page loaded")

        # 2. 点击"新的创作"按钮
        logger.info("[XHS] Clicking '新的创作'...")
        new_post_btn = page.locator('button:has-text("新的创作"), a:has-text("新的创作"), div:has-text("新的创作")')
        if await new_post_btn.count() > 0:
            await new_post_btn.first.click()
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(2000)
            logger.info(f"[XHS] Navigated to editor: {page.url}")
        else:
            logger.warning("[XHS] '新的创作' button not found, trying to continue...")

        await page.screenshot(path=str(DATA_DIR / "xhs_step3_editor.png"))
        logger.info("[XHS] Step 3: Editor page loaded")

        # 3. 输入正文（默认焦点在正文编辑框）
        xhs_body = body[:1000]
        logger.info(f"[XHS] Entering body ({len(xhs_body)} chars)...")
        body_editor = page.locator('div[contenteditable="true"]').first
        if await body_editor.count() > 0:
            await body_editor.click()
            await page.keyboard.press("Control+a")
            await page.keyboard.press("Backspace")
            await page.wait_for_timeout(300)
            await body_editor.type(xhs_body, delay=20)
            await page.wait_for_timeout(500)
        else:
            logger.warning("[XHS] Body editor not found!")

        await page.screenshot(path=str(DATA_DIR / "xhs_step4_body_entered.png"))
        logger.info("[XHS] Step 4: Body entered")

        # 4. 输入标题（点击标题区域后输入）
        xhs_title = title[:20]
        logger.info(f"[XHS] Entering title: {xhs_title}")
        title_input = page.locator('input[placeholder*="标题"], textarea[placeholder*="标题"]')
        if await title_input.count() > 0:
            await title_input.first.click()
            await title_input.first.fill("")
            await title_input.first.type(xhs_title, delay=50)
            await page.wait_for_timeout(300)
        else:
            logger.warning("[XHS] Title input not found!")

        await page.screenshot(path=str(DATA_DIR / "xhs_step5_title_entered.png"))
        logger.info("[XHS] Step 5: Title entered")

        # 5. 点击"一键排版"
        logger.info("[XHS] Clicking '一键排版'...")
        format_btn = page.locator('button:has-text("一键排版"), div:has-text("一键排版"), span:has-text("一键排版")')
        if await format_btn.count() > 0:
            await format_btn.first.click()
            await page.wait_for_timeout(2000)
            logger.info("[XHS] Clicked '一键排版'")
        else:
            logger.warning("[XHS] '一键排版' button not found, skipping...")

        await page.screenshot(path=str(DATA_DIR / "xhs_step6_formatted.png"))
        logger.info("[XHS] Step 6: After formatting")

        # 6. 等待"下一步"按钮出现，然后点击
        logger.info("[XHS] Waiting for '下一步' button...")
        next_btn = page.locator('button:has-text("下一步"), div:has-text("下一步")')
        # 最多等 10 秒
        for _ in range(20):
            if await next_btn.count() > 0 and await next_btn.first.is_visible():
                break
            await page.wait_for_timeout(500)

        if await next_btn.count() > 0 and await next_btn.first.is_visible():
            await next_btn.first.click()
            await page.wait_for_timeout(2000)
            logger.info("[XHS] Clicked '下一步'")
        else:
            logger.warning("[XHS] '下一步' button not found!")

        await page.screenshot(path=str(DATA_DIR / "xhs_step7_next_clicked.png"))
        logger.info("[XHS] Step 7: After next click")

        # 7. 点击"发布"按钮
        logger.info("[XHS] Clicking publish...")
        publish_btn = page.locator('button:has-text("发布"):visible')
        btn_count = await publish_btn.count()
        logger.info(f"[XHS] Found {btn_count} publish button(s)")
        if btn_count > 0:
            await publish_btn.first.click()
        else:
            logger.warning("[XHS] No publish button found!")

        await page.wait_for_timeout(3000)

        await page.screenshot(path=str(DATA_DIR / "xhs_step8_after_publish.png"))
        logger.info("[XHS] Step 8: After publish click")

        # 检查错误
        error_el = page.locator('.error-toast, [class*="error"], [class*="fail"]')
        if await error_el.count() > 0:
            error_text = await error_el.first.text_content()
            if error_text:
                return PublishResponse(success=False, error_message=f"小红书: {error_text}")

        # 更新登录态
        new_state = await context.storage_state()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(XHS_STATE, "w") as f:
            json.dump(new_state, f)

        logger.info("[XHS] Published successfully")
        return PublishResponse(success=True, platform_url=page.url)

    except Exception as e:
        logger.error(f"[XHS] Error: {e}")
        return PublishResponse(success=False, error_message=f"小红书发布异常: {e}")
    finally:
        await browser.close()
        await pw.stop()


# ──────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────

app = FastAPI(title="Playwright Browser Service", version="1.0.0")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "data_dir": str(DATA_DIR),
        "weibo_state": WEIBO_STATE.exists(),
        "xiaohongshu_state": XHS_STATE.exists(),
    }


@app.get("/status/{platform}")
async def check_status(platform: str):
    """检查平台登录状态。"""
    if platform not in ("weibo", "xiaohongshu"):
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")
    return await _check_login(platform)


@app.post("/publish/weibo", response_model=PublishResponse)
async def publish_weibo(req: PublishRequest):
    """发布微博。"""
    if not req.body:
        raise HTTPException(status_code=400, detail="body 不能为空")

    # 微博正文上限 2000 字
    text = f"{req.title}\n\n{req.body}" if req.title else req.body
    if len(text) > 2000:
        text = text[:1997] + "..."

    return await _publish_weibo(text)


@app.post("/publish/xiaohongshu", response_model=PublishResponse)
async def publish_xiaohongshu(req: PublishRequest):
    """发布小红书笔记。"""
    if not req.body:
        raise HTTPException(status_code=400, detail="body 不能为空")
    return await _publish_xiaohongshu(req.title, req.body)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
