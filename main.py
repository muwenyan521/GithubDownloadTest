import os
import asyncio
import aiohttp
import hashlib
import platform
import subprocess
from tqdm.asyncio import tqdm
from log import log

# 工具函数: Ping 测试
async def async_ping(domain, timeout=3):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        proc = await asyncio.create_subprocess_exec(
            "ping", param, "1", domain,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=timeout)
            if proc.returncode == 0:
                log.info(f"Ping {domain} 成功")
                return True
            else:
                log.warning(f"Ping {domain} 失败")
                return False
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            log.warning(f"Ping {domain} 超时")
            return False
    except Exception as e:
        log.error(f"Ping {domain} 异常: {e}")
        return False

# 工具函数: 文件MD5计算
def calculate_md5(filename):
    if not os.path.exists(filename):
        log.error(f"文件不存在: {filename}")
        return None
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# 工具函数: 异步下载
async def async_download(session, url, filename):
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            total_size = int(resp.headers.get('content-length', 0))
            with open(filename, 'wb') as f:
                pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading {filename}")
                async for chunk in resp.content.iter_chunked(1024):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                pbar.close()
        log.info(f"下载完成: {filename}")
        return filename
    except Exception as e:
        log.error(f"下载 {url} 出错: {e}")
        return None

# 主函数逻辑
async def main():
    size_mb = int(input("请输入所需MB数（1-50）: "))
    if not (1 <= size_mb <= 50):
        log.error("输入不合法，请输入1-50之间的整数")
        return

    repo = "muwenyan521/File"
    sha = "dee3b1cbf7872aef1317a7768625b9c5dd505532"
    path = f"{size_mb}MB.bin"
    base_url = f'https://raw.dgithub.xyz/{repo}/{sha}/{path}'

    url_list = [
        f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
        f'https://jsd.onmicrosoft.cn/gh/{repo}@{sha}/{path}',
        f'https://raw.dgithub.xyz/{repo}/{sha}/{path}',
        f'https://raw.kkgithub.com/{repo}/{sha}/{path}',
        f'https://gitdl.cn/https://raw.dgithub.xyz/{repo}/{sha}/{path}',
        f'https://ghp.ci/https://raw.dgithub.xyz/{repo}/{sha}/{path}',
        f'https://ghproxy.net/https://raw.dgithub.xyz/{repo}@{sha}/{path}',
        f'https://fastly.jsdelivr.net/gh/{repo}@{sha}/{path}',
        f'https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}',
        f'https://cdn.jsdelivr.net/gh/{repo}@{sha}/{path}',
    ]

    # 步骤1: 并发ping所有域名，筛选可用源
    log.info("开始Ping测试所有镜像源...")
    ping_tasks = [async_ping(url.split('/')[2]) for url in url_list]
    ping_results = await asyncio.gather(*ping_tasks)
    available_urls = [url for url, success in zip(url_list, ping_results) if success]

    if not available_urls:
        log.error("所有镜像源不可用，退出程序")
        return

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
        # 步骤2: 下载基准文件
        log.info("开始下载基准文件...")
        base_file = await async_download(session, base_url, filename=f"base_{path}")
        if not base_file:
            log.error("基准文件下载失败，退出程序")
            return

        base_md5 = calculate_md5(base_file)
        if not base_md5:
            log.error("基准文件MD5计算失败，退出程序")
            return

        # 步骤3: 并发下载所有可用镜像
        log.info("开始下载所有可用镜像...")
        download_tasks = []
        for url in available_urls:
            filename = url.split('/')[-1]
            download_tasks.append(async_download(session, url, filename=filename))
        
        downloaded_files = await asyncio.gather(*download_tasks)

        # 步骤4: MD5校验
        log.info("开始校验文件完整性...")
        for filename in downloaded_files:
            if filename and os.path.exists(filename):
                file_md5 = calculate_md5(filename)
                if file_md5 == base_md5:
                    log.info(f"{filename} 的 MD5 匹配 ✅")
                else:
                    log.warning(f"{filename} 的 MD5 不匹配 ❌")

    # 步骤5: 清理所有下载文件
    log.info("开始清理临时文件...")
    temp_files = [f"base_{path}"] + [url.split('/')[-1] for url in available_urls]
    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)
            log.info(f"已删除临时文件: {f}")

# 真正入口
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning("用户主动中断，退出程序")
    except Exception as e:
        log.error(f"程序运行异常: {e}")
