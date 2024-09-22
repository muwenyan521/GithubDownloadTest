import os
import hashlib
import requests
import subprocess
from tqdm import tqdm
from log import log


def ping_url(url):
    """Ping the given URL."""
    try:
        response = subprocess.run(["ping", "-c", "1", url], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return response.returncode == 0
    except Exception as e:
        log.error(f"Ping {url} failed: {e}")
        return False

def download_file(url):
    """Download a file and return the file path."""
    local_filename = url.split('/')[-1]
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                total_size = int(r.headers.get('content-length', 0))
                with tqdm(total=total_size, unit='B', unit_scale=True) as pbar:
                    for chunk in r.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
        return local_filename
    except Exception as e:
        log.error(f"下载 {url} 失败: {e}")
        return None

def calculate_md5(filename):
    """Calculate the MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main():
    # 用户输入
    size_mb = int(input("请输入所需MB数（1-50）: "))
    if size_mb < 1 or size_mb > 50:
        log.error("输入不在1-50的范围内")
        return
    
    repo = "muwenyan521/File"
    sha = "dee3b1cbf7872aef1317a7768625b9c5dd505532"
    path = f"{size_mb}MB.bin"
    
    url_list = [
        f'https://cdn.jsdmirror.com/gh/{repo}@{sha}/{path}',
        f'https://jsd.onmicrosoft.cn/gh/{repo}@{sha}/{path}',
        f'https://raw.dgithub.xyz/{repo}/{sha}/{path}',
        f'https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://raw.kkgithub.com/{repo}/{sha}/{path}',
        f'https://gitdl.cn/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://ghp.ci/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{sha}/{path}',
        f'https://fastly.jsdelivr.net/gh/{repo}@{sha}/{path}',
        f'https://jsdelivr.pai233.top/gh/{repo}@{sha}/{path}',
        f'https://cdn.jsdelivr.net/gh/{repo}@{sha}/{path}',
    ]

    # Ping 每个镜像源
    for url in url_list:
        domain = url.split('/')[2]
        if ping_url(domain):
            log.info(f"{domain} ping 成功")
            filename = download_file(url)
            if filename:
                log.info(f"下载完成: {filename}")
        else:
            log.error(f"{domain} ping 失败")

    # 校验文件
    base_url = f'https://raw.githubusercontent.com/{repo}/{sha}/{path}'
    try:
        base_file = download_file(base_url)
        if base_file:
            base_md5 = calculate_md5(base_file)
            log.info(f"基准文件 MD5: {base_md5}")

            # 对比 MD5
            for url in url_list:
                filename = url.split('/')[-1]
                if os.path.exists(filename):
                    md5 = calculate_md5(filename)
                    log.info(f"{filename} 的 MD5: {md5} - {'匹配' if md5 == base_md5 else '不匹配'}")

    except Exception as e:
        log.error(f"基准文件下载失败: {e}")

    # 清理临时文件
    for url in url_list:
        filename = url.split('/')[-1]
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    main()

