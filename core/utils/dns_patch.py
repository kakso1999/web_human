"""
自定义 DNS 解析器
解决本地 DNS 服务器无法解析阿里云域名的问题
"""
import socket
import functools

# 阿里云域名到 IP 的映射（使用公共 DNS 解析的结果）
ALIYUN_HOSTS = {
    "dashscope.aliyuncs.com": "39.96.213.166",
    "gtm-cn-rt54j1mlg03.dashscope.aliyuncs.com": "39.96.213.166",
}

# 保存原始的 getaddrinfo
_original_getaddrinfo = socket.getaddrinfo

@functools.wraps(_original_getaddrinfo)
def _custom_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    """
    自定义 DNS 解析器，优先使用预定义的 IP 地址
    """
    # 检查是否是阿里云域名
    if isinstance(host, str):
        for domain, ip in ALIYUN_HOSTS.items():
            if host == domain or host.endswith(f".{domain}"):
                # 使用预定义的 IP 地址
                if family in (0, socket.AF_INET):
                    return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, port))]

    # 否则使用原始的 DNS 解析
    return _original_getaddrinfo(host, port, family, type, proto, flags)


def patch_dns():
    """
    应用 DNS 补丁
    在程序启动时调用此函数
    """
    socket.getaddrinfo = _custom_getaddrinfo
    print(f"[DNS] Patched with custom resolver for: {list(ALIYUN_HOSTS.keys())}")


def unpatch_dns():
    """
    移除 DNS 补丁
    """
    socket.getaddrinfo = _original_getaddrinfo
    print("[DNS] Restored original resolver")


# 自动应用补丁
patch_dns()
