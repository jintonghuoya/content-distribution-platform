"""登录态保存脚本 — 宿主机运行。

用法：
    # 微博登录
    python login.py weibo

    # 小红书登录
    python login.py xiaohongshu

功能：
1. 打开有头浏览器，显示登录页
2. 用户手动扫码/输入密码登录
3. 登录成功后自动保存浏览器状态（Cookie + localStorage）
4. 保存到 ./data/ 目录下

后续 Browser Service 发布时会自动加载此文件，无需重复登录。
Cookie 过期后重新运行此脚本即可。
"""

import asyncio
import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

PLATFORMS = {
    "weibo": {
        "login_url": "https://weibo.com/login",
        "state_file": "weibo_state.json",
        "check_cookies": ["SUB"],
    },
    "xiaohongshu": {
        "login_url": "https://creator.xiaohongshu.com/login",
        "state_file": "xiaohongshu_state.json",
        "check_cookies": ["web_session", "a1", "webId"],
    },
}


async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in PLATFORMS:
        print("用法: python login.py <platform>")
        print(f"支持的平台: {', '.join(PLATFORMS.keys())}")
        sys.exit(1)

    platform = sys.argv[1]
    config = PLATFORMS[platform]

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("错误: playwright 未安装")
        print("请运行: pip install playwright && playwright install chromium")
        sys.exit(1)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state_path = DATA_DIR / config["state_file"]

    print(f"平台: {platform}")
    print(f"登录态将保存到: {state_path}")
    print("正在打开浏览器...\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()

        await page.goto(config["login_url"])

        print(f"请在浏览器中完成 {platform} 登录...")
        print("登录成功后，程序会自动检测并保存登录态。")
        print("关闭浏览器窗口也会触发保存。\n")

        while True:
            await asyncio.sleep(3)
            try:
                current_url = page.url
            except Exception:
                print("浏览器已关闭。")
                break

            if "login" not in current_url and "passport" not in current_url:
                try:
                    cookies = await context.cookies()
                    cookie_names = {c["name"] for c in cookies}
                    has_session = any(c in cookie_names for c in config["check_cookies"])
                    if has_session:
                        print("检测到登录成功！")
                        break
                except Exception:
                    pass

        try:
            state = await context.storage_state()
            with open(state_path, "w") as f:
                json.dump(state, f, indent=2)
            print(f"登录态已保存到: {state_path}")
            print(f"现在可以启动 Browser Service: python server.py")
        except Exception as e:
            print(f"保存登录态失败: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
